"""
AI service.

Calls the OpenAI API (key read from OPENAI_API_KEY env var) for
beginner-friendly explanations, error reasoning, and fix suggestions.

Per the spec (section 42 - AI safety/reliability): AI output is
always labeled as a suggestion, never presented as guaranteed-correct,
and corrected code is re-validated with the deterministic parser
before being shown as "Parser Validation: Passed".

If no API key is configured, or the OpenAI call fails for any reason
(network, quota, etc.), every function below transparently falls back
to a deterministic, template-based explanation instead of crashing
the request — see section 41 (graceful error handling) and section 44
("real functionality... use mock data only when a real implementation
is technically impossible, and clearly isolate mock functionality").
"""

import os
import re
import json
from typing import Optional

_client = None
_ai_enabled = False

try:
    from openai import OpenAI
    if os.getenv("OPENAI_API_KEY"):
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        _ai_enabled = True
except Exception:
    _client = None
    _ai_enabled = False


def ai_available() -> bool:
    return _ai_enabled


def _chat(system: str, user: str, max_tokens: int = 600) -> Optional[str]:
    if not _ai_enabled:
        return None
    try:
        resp = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return resp.choices[0].message.content
    except Exception:
        return None


def explain_code(code: str, language: str, components: dict, mode: str = "beginner") -> dict:
    """Returns {'summary': str, 'source': 'ai'|'template'}"""
    if _ai_enabled:
        style = "a total beginner who is new to programming" if mode == "beginner" else "an experienced developer"
        system = (
            f"You are CodeLens, a programming tutor. Explain {language} code to {style}. "
            "Be concise (4-8 sentences), plain language, no code repetition. "
            "Focus on WHAT the program does and WHY the main constructs (loops, conditions, functions) are used."
        )
        text = _chat(system, f"Explain this {language} code:\n\n{code}")
        if text:
            return {"summary": text.strip(), "source": "ai"}

    # ---- deterministic template fallback ----
    funcs = len(components.get("functions", []))
    loops = len(components.get("loops", []))
    conds = len(components.get("conditions", []))
    parts = [f"This {language} program is {components.get('line_count', 'a number of')} lines long."]
    if funcs:
        parts.append(f"It defines {funcs} function(s), which group reusable logic into named blocks.")
    if loops:
        parts.append(f"It uses {loops} loop(s) to repeat operations instead of duplicating code.")
    if conds:
        parts.append(f"It makes {conds} decision(s) using conditional checks to branch program flow.")
    if not (funcs or loops or conds):
        parts.append("It runs as a straight, linear sequence of statements from top to bottom.")
    parts.append("(Template explanation — set OPENAI_API_KEY in .env for richer AI-generated explanations.)")
    return {"summary": " ".join(parts), "source": "template"}


def explain_error(error: dict, language: str) -> dict:
    if _ai_enabled:
        system = f"You are CodeLens, a programming tutor explaining a {language} error to a beginner in 2-3 sentences."
        prompt = f"Error type: {error['type']}\nLine: {error['line']}\nProblem: {error['problem']}"
        text = _chat(system, prompt, max_tokens=200)
        if text:
            return {"why": text.strip(), "source": "ai"}
    return {"why": error.get("why") or "This was flagged by CodeLens's static analyzer based on the code pattern at this line.",
            "source": "template"}


def suggest_fix(code: str, errors: list, language: str) -> dict:
    """
    Returns {'fixed_code': str|None, 'source': 'ai'|'template'|'none',
              'notes': str, 'fix_steps': [{'line', 'problem', 'how_to_fix'}, ...]}
    The caller is responsible for re-validating fixed_code with the
    deterministic analyzer before labeling it "Parser Validation: Passed".
    fix_steps is ALWAYS populated (even with AI on) so the UI always has
    something concrete to show, not just a code diff.
    """
    if not errors:
        return {"fixed_code": None, "source": "none", "notes": "No confirmed errors to fix.", "fix_steps": []}

    fix_steps = [
        {
            "line": e.get("line"),
            "problem": e.get("problem"),
            "how_to_fix": e.get("how_to_fix") or "Review this line manually — no automatic guidance available for this error type.",
        }
        for e in errors
    ]

    if _ai_enabled:
        error_list = "\n".join(f"- Line {e['line']}: {e['problem']}" for e in errors)
        system = (
            f"You are CodeLens, an expert {language} developer. Fix ONLY the listed errors. "
            "Return ONLY the corrected full source code, no explanation, no markdown fences."
        )
        prompt = f"Errors to fix:\n{error_list}\n\nOriginal code:\n{code}"
        text = _chat(system, prompt, max_tokens=1200)
        if text:
            cleaned = text.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
                if cleaned.endswith("```"):
                    cleaned = cleaned.rsplit("```", 1)[0]
            return {"fixed_code": cleaned.strip(), "source": "ai",
                    "notes": "AI Suggested Fix — review before applying.", "fix_steps": fix_steps}

    # ---- Template fallback: no AI key, but we can still auto-apply SAFE,
    # unambiguous fixes (ones that don't require guessing developer intent). ----
    template_fixed = _apply_safe_template_fixes(code, errors)
    if template_fixed and template_fixed != code:
        return {
            "fixed_code": template_fixed, "source": "template",
            "notes": "Rule-based fix — only unambiguous corrections (like removing dead code) were auto-applied. "
                     "Errors needing developer judgment are listed below; add OPENAI_API_KEY for full AI fixes.",
            "fix_steps": fix_steps,
        }

    return {"fixed_code": None, "source": "none",
            "notes": "AI fixing is unavailable (no OPENAI_API_KEY configured), and no error here has a safe "
                     "automatic fix. Follow the step-by-step fixes below for each error, then re-analyze.",
            "fix_steps": fix_steps}


def _apply_safe_template_fixes(code: str, errors: list) -> str:
    """Applies only fixes that are unambiguous with no AI needed, e.g. removing
    dead/unreachable code after a return. Returns the (possibly unmodified) code."""
    lines = code.splitlines()
    drop_lines = set()
    for e in errors:
        if e.get("type") == "Logical Error" and "Unreachable code" in (e.get("problem") or ""):
            ln = e.get("line")
            if ln and 1 <= ln <= len(lines):
                drop_lines.add(ln)
    if not drop_lines:
        return code
    kept = [line for i, line in enumerate(lines, start=1) if i not in drop_lines]
    return "\n".join(kept)



def suggest_improvements(code: str, language: str, components: dict) -> list:
    if _ai_enabled:
        system = f"You are CodeLens. List 3-6 short, concrete improvement suggestions for this {language} code as a JSON array of strings only."
        text = _chat(system, code, max_tokens=300)
        if text:
            try:
                cleaned = text.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("```")[1]
                    if cleaned.startswith("json"):
                        cleaned = cleaned[4:]
                items = json.loads(cleaned)
                if isinstance(items, list):
                    return items[:6]
            except Exception:
                pass

    suggestions = []
    if not components.get("functions"):
        suggestions.append("Consider breaking the code into functions to improve reusability.")
    if len(components.get("variables", [])) > 8:
        suggestions.append("Several variables are in use — check names are descriptive and not single letters.")
    if len(components.get("conditions", [])) > 4:
        suggestions.append("Several conditionals were found — consider simplifying deeply nested logic.")
    if not suggestions:
        suggestions.append("Add comments explaining non-obvious logic for future readers.")
    suggestions.append("(Template suggestions — set OPENAI_API_KEY in .env for AI-tailored suggestions.)")
    return suggestions


def _line_component_tags(components: dict) -> dict:
    """
    Build {line_number: tag} from the analyzer's structural components,
    so template explanations can say WHY a line exists (not just what it is).
    Priority order matters when several components land on the same line.
    """
    tags = {}
    for item in components.get("imports", []):
        tags[item["line"]] = ("import", item.get("name", ""))
    for item in components.get("classes", []):
        tags[item["line"]] = ("class", item.get("name", ""))
    for item in components.get("functions", []):
        tags[item["line"]] = ("function", item.get("name", ""))
    for item in components.get("loops", []):
        tags[item["line"]] = ("loop", item.get("kind", ""))
    for item in components.get("conditions", []):
        tags[item["line"]] = ("condition", "")
    for item in components.get("variables", []):
        # don't override a function/loop/condition tag on the same line
        tags.setdefault(item["line"], ("variable", item.get("name", "")))
    return tags


_COMMENT_PREFIX = {"python": ("#",), "java": ("//", "/*", "*"), "cpp": ("//", "/*", "*"), "c": ("//", "/*", "*")}
_PRINT_HINT = {
    "python": ("print(",),
    "java": ("System.out.print",),
    "cpp": ("cout", "printf("),
    "c": ("printf(",),
}


def _template_line_reason(stripped: str, language: str, tag) -> str:
    """Deterministic, rule-based 'why this line' explanation — no AI needed."""
    if not stripped:
        return "Blank line — used only to visually separate code sections."

    comment_prefixes = _COMMENT_PREFIX.get(language, ("#",))
    if any(stripped.startswith(p) for p in comment_prefixes):
        return "A comment — ignored by the compiler/interpreter, written for human readers."

    if stripped in ("{", "}") or stripped in ("):", ":"):
        return "Marks the start or end of a code block (function, loop, or condition body)."

    if tag:
        kind, name = tag
        if kind == "import":
            return f"Imports '{name}', bringing in functionality defined elsewhere so it can be reused here."
        if kind == "class":
            return f"Declares the class '{name}', bundling related data and behavior into one blueprint."
        if kind == "function":
            return f"Defines the function '{name}', grouping a piece of logic under a reusable, named block."
        if kind == "loop":
            return f"Starts a {name or ''} loop — repeats the block below instead of duplicating the same code."
        if kind == "condition":
            return "Checks a condition — the program branches to different code depending on whether it's true or false."
        if kind == "variable":
            return f"Assigns a value to '{name}', storing it in memory so it can be reused later in the program."

    if re.search(r'\breturn\b', stripped):
        return "Returns a value from the function, ending its execution at this point and sending the result back to the caller."
    if re.search(r'\bbreak\b', stripped):
        return "Exits the nearest loop immediately, skipping any remaining iterations."
    if re.search(r'\bcontinue\b', stripped):
        return "Skips the rest of the current loop iteration and jumps to the next one."
    if re.search(r'\b(else if|elif)\b', stripped):
        return "An alternate branch — runs only if the earlier condition(s) above were false."
    if re.search(r'^\s*else\b', stripped):
        return "The fallback branch — runs when none of the preceding conditions were true."
    if re.search(r'\b(try|except|catch|finally)\b', stripped):
        return "Part of error handling — lets the program respond to a failure instead of crashing."
    if any(h in stripped for h in _PRINT_HINT.get(language, ())):
        return "Outputs a value to the console so it can be seen when the program runs."
    if re.search(r'[+\-*/%]=', stripped):
        return "Updates an existing variable's value based on its current value (a compound assignment)."
    if re.search(r'^\s*(#include|import)\b', stripped):
        return "Includes an external library so its functions/types are available in this file."
    if re.search(r'\w+\s*\([^)]*\)\s*;?\s*$', stripped) and "=" not in stripped:
        return "Calls a function — hands control to another named block of logic and (optionally) waits for its result."

    return "A supporting statement that helps carry out the logic of the surrounding block."


def explain_lines(code: str, language: str, components: dict) -> list:
    """
    Returns a list of per-line explanations:
    [{'line': 1, 'code': 'def foo():', 'why': '...', 'source': 'ai'|'template'}, ...]
    Blank lines are still included (with a short blank-line note) so the
    frontend can render one row per source line without gaps.
    """
    lines = code.splitlines()
    tags = _line_component_tags(components)

    ai_map = {}
    if _ai_enabled and lines:
        numbered = "\n".join(f"{i}: {line}" for i, line in enumerate(lines, start=1))
        system = (
            f"You are CodeLens, explaining {language} code line by line to a learner. "
            "For EVERY numbered line given (including braces/blank lines, explain those briefly too), "
            "write ONE short sentence (max ~18 words) saying what that specific line does and why it's there. "
            'Respond with ONLY a JSON array like [{"line": 1, "why": "..."}, ...] and nothing else — '
            "no markdown fences, no commentary."
        )
        text = _chat(system, numbered, max_tokens=min(2000, 60 * max(len(lines), 1)))
        if text:
            try:
                cleaned = text.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("```")[1]
                    if cleaned.startswith("json"):
                        cleaned = cleaned[4:]
                parsed = json.loads(cleaned)
                if isinstance(parsed, list):
                    for item in parsed:
                        if isinstance(item, dict) and "line" in item and "why" in item:
                            ai_map[int(item["line"])] = str(item["why"]).strip()
            except Exception:
                ai_map = {}

    results = []
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if i in ai_map and ai_map[i]:
            results.append({"line": i, "code": line, "why": ai_map[i], "source": "ai"})
        else:
            why = _template_line_reason(stripped, language, tags.get(i))
            results.append({"line": i, "code": line, "why": why, "source": "template"})
    return results


def explain_flow_step(step_label: str, code_line: str, language: str) -> dict:
    if _ai_enabled:
        system = f"You are CodeLens explaining one execution step of {language} code to a beginner. Answer in 2-3 short sentences: what happens and why it's needed."
        text = _chat(system, f"Step: {step_label}\nCode line: {code_line}", max_tokens=150)
        if text:
            return {"explanation": text.strip(), "source": "ai"}
    return {
        "explanation": f"This step ({step_label}) executes '{code_line.strip()}'. "
                        "It exists to move the program from one state to the next in its execution flow.",
        "source": "template",
    }
