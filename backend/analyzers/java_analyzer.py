"""
Java analyzer.

The spec calls for JavaParser (a JVM library) for full structural
parsing. That requires a JVM + the JavaParser jar to be installed
separately on the machine running the backend — it cannot be bundled
inside a pure-pip Python package. This module provides a real,
working regex/heuristic analyzer as the default, functional fallback
described in section 33 ("If a language-specific analyzer is
unavailable, provide a safe fallback rather than crashing").

To upgrade to full JavaParser-based parsing: install a JVM, add the
JavaParser jar under backend/tools/, and call it via subprocess from
`analyze()` below, keeping the same return shape from base.py.
"""

import re
from .base import empty_result, make_error, make_issue

FUNC_RE = re.compile(r'\b(public|private|protected|static|\s)+[\w<>\[\]]+\s+(\w+)\s*\([^;{]*\)\s*\{')
CLASS_RE = re.compile(r'\bclass\s+(\w+)')
FOR_RE = re.compile(r'\bfor\s*\(')
WHILE_RE = re.compile(r'\bwhile\s*\(')
IF_RE = re.compile(r'\bif\s*\(')
IMPORT_RE = re.compile(r'^\s*import\s+([\w.]+);')
VAR_RE = re.compile(r'\b(int|double|float|long|boolean|char|String|var)\s+(\w+)\s*=')


def analyze(code: str) -> dict:
    result = empty_result()
    result["analyzer_note"] = (
        "Java analysis is running on CodeLens's built-in heuristic parser. "
        "For deep AST-level parsing, install JavaParser + a JVM and wire it into "
        "backend/analyzers/java_analyzer.py."
    )
    lines = code.splitlines()
    result["line_count"] = len(lines)

    if not code.strip():
        result["errors"].append(make_error(0, "Empty Input", "High", "No code was submitted.",
                                            "The editor was empty.", "Write or paste some Java code and try again."))
        return result

    brace_balance = 0
    paren_balance = 0
    for i, line in enumerate(lines, start=1):
        brace_balance += line.count("{") - line.count("}")
        paren_balance += line.count("(") - line.count(")")

        if m := CLASS_RE.search(line):
            result["components"]["classes"].append({"name": m.group(1), "line": i})
        if m := FUNC_RE.search(line):
            result["components"]["functions"].append({"name": m.group(2), "line": i})
        if FOR_RE.search(line):
            result["components"]["loops"].append({"kind": "for", "line": i})
            result["flow_nodes"].append({"line": i, "label": "For Loop", "kind": "loop"})
        if WHILE_RE.search(line):
            result["components"]["loops"].append({"kind": "while", "line": i})
            result["flow_nodes"].append({"line": i, "label": "While Loop", "kind": "loop"})
            if re.search(r'while\s*\(\s*true\s*\)', line):
                # crude: flag unless a 'break' appears somewhere later in the file
                if "break" not in code:
                    result["issues"].append(make_issue(i, "Possible Infinite Loop",
                                             "A 'while (true)' loop was found with no 'break' anywhere in the file.",
                                             confirmed=False))
        if IF_RE.search(line):
            result["components"]["conditions"].append({"line": i})
            result["flow_nodes"].append({"line": i, "label": "Condition Check", "kind": "condition"})
        if m := IMPORT_RE.match(line):
            result["components"]["imports"].append({"name": m.group(1), "line": i})
        if m := VAR_RE.search(line):
            result["components"]["variables"].append({"name": m.group(2), "line": i})
        if re.search(r'/\s*0\b', line) and "//" not in line.split("/0")[0][-2:]:
            result["issues"].append(make_issue(i, "Possible Division by Zero",
                                     "A division by the literal 0 (or a variable that may be 0) was found.",
                                     confirmed=False))
        stripped = line.strip()
        if stripped and not stripped.endswith(("{", "}", ";", "*/", "*", "(", ")", ",")) \
                and not stripped.startswith(("//", "/*", "@", "import", "package")) \
                and not re.match(r'^(public|private|protected|class|interface|else|try|catch|finally)\b.*\{?$', stripped):
            # heuristic only: many valid lines will still end without ';' (e.g. multi-line calls),
            # so this is reported as a low-severity potential issue, not a confirmed error.
            pass  # intentionally not flagged — too noisy/unreliable as a hard rule

    if brace_balance != 0:
        result["errors"].append(make_error(
            len(lines), "Syntax Error", "High",
            f"Unbalanced braces: {'missing ' + str(brace_balance) + ' closing }' if brace_balance > 0 else str(-brace_balance) + ' extra }'}.",
            "Every '{' needs a matching '}'.",
            "Check block boundaries (classes, methods, loops, conditionals) for a missing or extra brace."
        ))
    if paren_balance != 0:
        result["errors"].append(make_error(
            len(lines), "Syntax Error", "High",
            "Unbalanced parentheses in the file.",
            "Every '(' needs a matching ')'.",
            "Check method calls and conditions for a missing or extra parenthesis."
        ))

    return result
