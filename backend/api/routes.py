from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
import re

from models.schemas import LoginRequest, LoginResponse, AnalyzeRequest, ReviewRequest
from database import db
from analyzers import python_analyzer, java_analyzer, cpp_analyzer, c_analyzer
from ai import ai_service
from services import flowchart_service, quality_service, report_service

router = APIRouter(prefix="/api")

ANALYZERS = {
    "python": python_analyzer.analyze,
    "java": java_analyzer.analyze,
    "cpp": cpp_analyzer.analyze,
    "c": c_analyzer.analyze,
}


# ---------------- LOGIN ----------------

@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest):
    user_id = db.get_or_create_user(str(req.email))
    return {"user_id": user_id, "email": str(req.email)}


# ---------------- DASHBOARD ----------------

@router.get("/dashboard/{user_id}")
def dashboard(user_id: int):
    stats = db.get_dashboard_stats(user_id)
    recent = db.get_history(user_id, limit=5)
    return {"stats": stats, "recent": recent}


# ---------------- MAIN ANALYSIS PIPELINE ----------------

@router.post("/analyze")
def analyze(req: AnalyzeRequest):
    analyzer_fn = ANALYZERS.get(req.language)
    if not analyzer_fn:
        raise HTTPException(400, "Unsupported language.")

    try:
        # Stage: parsing + error/bug detection (deterministic)
        result = analyzer_fn(req.code)
    except Exception:
        return {
            "error": True,
            "message": "We could not fully analyze this code.",
            "reason": "The submitted code contains unsupported or incomplete syntax.",
        }

    # Stage: explanation (AI w/ template fallback)
    explanation = ai_service.explain_code(req.code, req.language, result["components"], req.mode)

    # Stage: line-by-line explanation ("why this line?")
    line_explanations = ai_service.explain_lines(req.code, req.language, result["components"])

    # Stage: error explanations enriched
    enriched_errors = []
    for e in result["errors"]:
        ai_why = ai_service.explain_error(e, req.language)
        enriched = dict(e)
        enriched["why"] = enriched.get("why") or ai_why["why"]
        enriched["why_source"] = ai_why["source"]
        enriched_errors.append(enriched)
    result["errors"] = enriched_errors

    # Stage: corrected code / auto-fix, re-validated with the deterministic parser
    fix = ai_service.suggest_fix(req.code, result["errors"], req.language)
    validated = None
    if fix["fixed_code"]:
        try:
            revalidate = analyzer_fn(fix["fixed_code"])
            validated = len(revalidate["errors"]) == 0
        except Exception:
            validated = False

    # Stage: flowchart generation
    flowchart = flowchart_service.build_flowchart(req.code, result["flow_nodes"])

    # Stage: improvements
    improvements = ai_service.suggest_improvements(req.code, req.language, result["components"])

    # Stage: quality + complexity + security
    quality = quality_service.compute_quality(result)
    security = quality_service.security_scan(result, req.language)

    payload = {
        "language": req.language,
        "analyzer_note": result.get("analyzer_note"),
        "components": result["components"],
        "explanation": explanation,
        "line_explanations": line_explanations,
        "errors": result["errors"],
        "issues": result["issues"],
        "fix": {
            "fixed_code": fix["fixed_code"],
            "source": fix["source"],
            "notes": fix["notes"],
            "fix_steps": fix["fix_steps"],
            "parser_validation": "Passed" if validated else ("Failed" if validated is False else None),
        },
        "flowchart": flowchart,
        "improvements": improvements,
        "quality": quality,
        "security": security,
        "ai_available": ai_service.ai_available(),
    }

    summary_text = (explanation["summary"][:180] + "…") if len(explanation["summary"]) > 180 else explanation["summary"]
    analysis_id = db.save_analysis(
        user_id=req.user_id,
        language=req.language,
        code=req.code,
        summary=summary_text,
        quality_score=quality["overall"],
        result=payload,
    )
    payload["analysis_id"] = analysis_id
    return payload


@router.post("/explain")
def explain_only(req: AnalyzeRequest):
    analyzer_fn = ANALYZERS.get(req.language)
    if not analyzer_fn:
        raise HTTPException(400, "Unsupported language.")
    result = analyzer_fn(req.code)
    return ai_service.explain_code(req.code, req.language, result["components"], req.mode)


@router.post("/explain-lines")
def explain_lines_only(req: AnalyzeRequest):
    analyzer_fn = ANALYZERS.get(req.language)
    if not analyzer_fn:
        raise HTTPException(400, "Unsupported language.")
    try:
        result = analyzer_fn(req.code)
    except Exception:
        raise HTTPException(400, "Could not parse this code for line-by-line explanation.")
    return {"lines": ai_service.explain_lines(req.code, req.language, result["components"])}


@router.post("/detect-errors")
def detect_errors_only(req: AnalyzeRequest):
    analyzer_fn = ANALYZERS.get(req.language)
    if not analyzer_fn:
        raise HTTPException(400, "Unsupported language.")
    result = analyzer_fn(req.code)
    return {"errors": result["errors"], "issues": result["issues"]}


@router.post("/fix-code")
def fix_code_only(req: AnalyzeRequest):
    analyzer_fn = ANALYZERS.get(req.language)
    if not analyzer_fn:
        raise HTTPException(400, "Unsupported language.")
    result = analyzer_fn(req.code)
    return ai_service.suggest_fix(req.code, result["errors"], req.language)


@router.post("/generate-flow")
def generate_flow_only(req: AnalyzeRequest):
    analyzer_fn = ANALYZERS.get(req.language)
    if not analyzer_fn:
        raise HTTPException(400, "Unsupported language.")
    result = analyzer_fn(req.code)
    return flowchart_service.build_flowchart(req.code, result["flow_nodes"])


@router.post("/improvements")
def improvements_only(req: AnalyzeRequest):
    analyzer_fn = ANALYZERS.get(req.language)
    if not analyzer_fn:
        raise HTTPException(400, "Unsupported language.")
    result = analyzer_fn(req.code)
    return {"improvements": ai_service.suggest_improvements(req.code, req.language, result["components"])}


@router.post("/flow-step-explain")
def flow_step_explain(payload: dict):
    return ai_service.explain_flow_step(
        payload.get("label", "Step"), payload.get("code_line", ""), payload.get("language", "python")
    )


# ---------------- HISTORY ----------------

@router.get("/history")
def history(user_id: int):
    return {"history": db.get_history(user_id)}


@router.get("/history/{analysis_id}")
def history_detail(analysis_id: int, user_id: int):
    record = db.get_analysis(analysis_id, user_id)
    if not record:
        raise HTTPException(404, "Analysis not found.")
    return record


# ---------------- REPORT ----------------

@router.get("/report/{analysis_id}")
def report(analysis_id: int, user_id: int):
    record = db.get_analysis(analysis_id, user_id)
    if not record:
        raise HTTPException(404, "Analysis not found.")
    pdf_bytes = report_service.generate_pdf(record)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="codelens-report-{analysis_id}.pdf"'},
    )


# ---------------- REVIEW ----------------

@router.post("/review")
def review(req: ReviewRequest):
    review_id = db.save_review(req.user_id, req.rating, req.feedback or "")
    return {"id": review_id, "message": "Thank you for your feedback!"}
