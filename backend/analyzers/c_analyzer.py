"""
C analyzer.

Same rationale as cpp_analyzer.py: Clang/LibTooling is the spec'd
tool but is a separate native install, so this ships a real, working
heuristic analyzer plus an optional `clang -fsyntax-only` hook that
activates automatically if clang is present on PATH.
"""

import re
import shutil
import subprocess
import tempfile
import os
from .base import empty_result, make_error, make_issue

FUNC_RE = re.compile(r'\b[\w\*]+\s+(\w+)\s*\([^;{]*\)\s*\{')
FOR_RE = re.compile(r'\bfor\s*\(')
WHILE_RE = re.compile(r'\bwhile\s*\(')
IF_RE = re.compile(r'\bif\s*\(')
INCLUDE_RE = re.compile(r'^\s*#include\s*[<"]([^">]+)[">]')
VAR_RE = re.compile(r'\b(int|double|float|long|char|void\s*\*)\s+(\w+)\s*=')


def _try_clang_syntax_check(code: str):
    if not shutil.which("clang"):
        return None
    with tempfile.NamedTemporaryFile(suffix=".c", delete=False, mode="w") as f:
        f.write(code)
        path = f.name
    try:
        proc = subprocess.run(
            ["clang", "-fsyntax-only", path],
            capture_output=True, text=True, timeout=10
        )
        return proc.stderr
    except Exception:
        return None
    finally:
        os.unlink(path)


def analyze(code: str) -> dict:
    result = empty_result()
    result["analyzer_note"] = (
        "C analysis is running on CodeLens's built-in heuristic parser. "
        "If clang is installed and on PATH, CodeLens will also run `clang -fsyntax-only` "
        "for real compiler diagnostics. For full LibTooling AST analysis, install LLVM/Clang "
        "and wire it into backend/analyzers/c_analyzer.py."
    )
    lines = code.splitlines()
    result["line_count"] = len(lines)

    if not code.strip():
        result["errors"].append(make_error(0, "Empty Input", "High", "No code was submitted.",
                                            "The editor was empty.", "Write or paste some C code and try again."))
        return result

    brace_balance = 0
    malloc_lines, free_lines = [], []
    for i, line in enumerate(lines, start=1):
        brace_balance += line.count("{") - line.count("}")

        if m := FUNC_RE.search(line):
            result["components"]["functions"].append({"name": m.group(1), "line": i})
        if FOR_RE.search(line):
            result["components"]["loops"].append({"kind": "for", "line": i})
            result["flow_nodes"].append({"line": i, "label": "For Loop", "kind": "loop"})
        if WHILE_RE.search(line):
            result["components"]["loops"].append({"kind": "while", "line": i})
            result["flow_nodes"].append({"line": i, "label": "While Loop", "kind": "loop"})
        if IF_RE.search(line):
            result["components"]["conditions"].append({"line": i})
            result["flow_nodes"].append({"line": i, "label": "Condition Check", "kind": "condition"})
        if m := INCLUDE_RE.match(line):
            result["components"]["imports"].append({"name": m.group(1), "line": i})
        if m := VAR_RE.search(line):
            result["components"]["variables"].append({"name": m.group(2), "line": i})
        if re.search(r'/\s*0\b', line):
            result["issues"].append(make_issue(i, "Possible Division by Zero",
                                     "A division by the literal 0 (or a variable that may be 0) was found.",
                                     confirmed=False))
        if "malloc(" in line or "calloc(" in line:
            malloc_lines.append(i)
        if "free(" in line:
            free_lines.append(i)

    if malloc_lines and not free_lines:
        result["issues"].append(make_issue(malloc_lines[0], "Possible Memory Leak",
                                 "Memory is allocated with malloc/calloc but 'free' was not found anywhere "
                                 "in the submitted code.", confirmed=False))

    if brace_balance != 0:
        result["errors"].append(make_error(
            len(lines), "Syntax Error", "High",
            f"Unbalanced braces: {'missing ' + str(brace_balance) + ' closing }' if brace_balance > 0 else str(-brace_balance) + ' extra }'}.",
            "Every '{' needs a matching '}'.",
            "Check block boundaries for a missing or extra brace."
        ))

    clang_stderr = _try_clang_syntax_check(code)
    if clang_stderr:
        for m in re.finditer(r':(\d+):\d+:\s*(error|warning):\s*(.+)', clang_stderr):
            line_no, sev, msg = int(m.group(1)), m.group(2), m.group(3).strip()
            if sev == "error":
                result["errors"].append(make_error(line_no, "Compiler Error", "High", msg,
                                                     "Reported directly by clang -fsyntax-only.",
                                                     "Fix the reported issue at this line."))
            else:
                result["issues"].append(make_issue(line_no, "Compiler Warning", msg, confirmed=False))

    return result
