"""
Computes the code-quality score and complexity summary from real
analysis results (errors/issues/components) — no AI involved, so the
number is reproducible and explainable, per section 22 ("The score
should be calculated from actual analysis results where possible").
"""


def compute_quality(result: dict) -> dict:
    line_count = max(result.get("line_count", 1), 1)
    errors = result.get("errors", [])
    issues = result.get("issues", [])
    components = result.get("components", {})

    high_errors = sum(1 for e in errors if e.get("severity") == "High")
    med_errors = sum(1 for e in errors if e.get("severity") == "Medium")
    low_errors = len(errors) - high_errors - med_errors

    # Readability: penalize very long files and lack of functions
    readability = 100
    if line_count > 40 and not components.get("functions"):
        readability -= 20
    if line_count > 100:
        readability -= 10
    readability -= min(len(issues) * 3, 20)
    readability = max(0, min(100, readability))

    # Maintainability: penalize confirmed errors and deep nesting proxy (conditions+loops)
    maintainability = 100 - (high_errors * 15) - (med_errors * 8) - (low_errors * 3) - (len(issues) * 2)
    maintainability = max(0, min(100, maintainability))

    # Complexity score (0-100, higher = simpler/better) derived from cyclomatic-ish proxy
    branch_points = len(components.get("conditions", [])) + len(components.get("loops", []))
    complexity_score = max(0, 100 - branch_points * 6)

    # Security: only reduced if issues mention risk keywords
    risky_terms = ("memory leak", "dangling", "security", "unsafe")
    security_hits = sum(1 for i in issues if any(t in i.get("type", "").lower() or t in i.get("description", "").lower() for t in risky_terms))
    security = max(0, 100 - security_hits * 15)

    overall = round((readability + maintainability + complexity_score + security) / 4)

    complexity_label = "Low"
    if branch_points > 8:
        complexity_label = "High"
    elif branch_points > 3:
        complexity_label = "Medium"

    return {
        "overall": overall,
        "readability": readability,
        "maintainability": maintainability,
        "complexity": complexity_score,
        "security": security,
        "complexity_summary": {
            "overall_label": complexity_label,
            "nested_loops": len(components.get("loops", [])),
            "conditions": len(components.get("conditions", [])),
            "functions": len(components.get("functions", [])),
        },
    }


def security_scan(result: dict, language: str) -> dict:
    """Very small, explicitly-scoped static security scan."""
    issues = result.get("issues", [])
    security_findings = [i for i in issues if "security" in i.get("type", "").lower()
                          or "memory" in i.get("type", "").lower()
                          or "dangling" in i.get("type", "").lower()]
    if not security_findings:
        return {"status": "clear", "message": "No obvious security issue detected."}
    return {
        "status": "warning",
        "findings": security_findings,
        "note": "This is a lightweight static scan, not a complete security audit.",
    }
