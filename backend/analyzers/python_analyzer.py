"""
Python analyzer.

Uses Python's built-in `ast` module for real structural analysis
(this is the "Python AST" parser referenced in the spec — it ships
with Python, no extra install needed). Syntax errors are caught
directly from the parser (compile/ast.parse raises SyntaxError with
an exact line number). Logical-issue detection (unused variables,
infinite loops, division by zero risk, etc.) is done by walking the
AST tree.
"""

import ast
import builtins
from .base import empty_result, make_error, make_issue


def analyze(code: str) -> dict:
    result = empty_result()
    result["line_count"] = len(code.splitlines())

    if not code.strip():
        result["errors"].append(
            make_error(0, "Empty Input", "High", "No code was submitted.",
                       "The editor was empty.", "Write or paste some Python code and try again.")
        )
        return result

    # ---- Stage: syntax parsing ----
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        result["errors"].append(
            make_error(
                line=e.lineno or 0,
                error_type="Syntax Error",
                severity="High",
                problem=e.msg or "Invalid syntax.",
                why="The Python parser could not build a valid syntax tree at this line.",
                how_to_fix="Check for missing colons, unmatched brackets/quotes, or bad indentation near this line.",
            )
        )
        return result  # can't do structural analysis on unparsable code

    # ---- Stage: structural walk ----
    assigned_names = {}     # name -> line first assigned
    used_names = set()
    bound_names = set()     # every name ever "defined" anywhere (flat, not scope-precise — keeps false positives low)
    func_stack = []         # for building call structure

    class Visitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node):
            result["components"]["functions"].append({"name": node.name, "line": node.lineno})
            bound_names.add(node.name)
            args = node.args
            for a in (args.posonlyargs + args.args + args.kwonlyargs):
                bound_names.add(a.arg)
            if args.vararg:
                bound_names.add(args.vararg.arg)
            if args.kwarg:
                bound_names.add(args.kwarg.arg)
            func_stack.append(node.name)
            self.generic_visit(node)
            func_stack.pop()

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_Lambda(self, node):
            for a in (node.args.posonlyargs + node.args.args + node.args.kwonlyargs):
                bound_names.add(a.arg)
            if node.args.vararg:
                bound_names.add(node.args.vararg.arg)
            if node.args.kwarg:
                bound_names.add(node.args.kwarg.arg)
            self.generic_visit(node)

        def visit_ClassDef(self, node):
            result["components"]["classes"].append({"name": node.name, "line": node.lineno})
            bound_names.add(node.name)
            self.generic_visit(node)

        def visit_Import(self, node):
            for n in node.names:
                result["components"]["imports"].append({"name": n.name, "line": node.lineno})
                bound_names.add((n.asname or n.name).split(".")[0])
            self.generic_visit(node)

        def visit_ImportFrom(self, node):
            mod = node.module or ""
            for n in node.names:
                result["components"]["imports"].append({"name": f"{mod}.{n.name}", "line": node.lineno})
                bound_names.add(n.asname or n.name)
            self.generic_visit(node)

        def visit_For(self, node):
            result["components"]["loops"].append({"kind": "for", "line": node.lineno})
            result["flow_nodes"].append({"line": node.lineno, "label": "For Loop", "kind": "loop"})
            for n in ast.walk(node.target):
                if isinstance(n, ast.Name):
                    bound_names.add(n.id)
            self.generic_visit(node)

        def visit_comprehension(self, node):
            for n in ast.walk(node.target):
                if isinstance(n, ast.Name):
                    bound_names.add(n.id)
            self.generic_visit(node)

        def visit_With(self, node):
            for item in node.items:
                if item.optional_vars:
                    for n in ast.walk(item.optional_vars):
                        if isinstance(n, ast.Name):
                            bound_names.add(n.id)
            self.generic_visit(node)

        visit_AsyncWith = visit_With

        def visit_ExceptHandler(self, node):
            if node.name:
                bound_names.add(node.name)
            self.generic_visit(node)

        def visit_Global(self, node):
            bound_names.update(node.names)

        def visit_Nonlocal(self, node):
            bound_names.update(node.names)

        def visit_NamedExpr(self, node):  # walrus operator :=
            if isinstance(node.target, ast.Name):
                bound_names.add(node.target.id)
            self.generic_visit(node)

        def visit_While(self, node):
            result["components"]["loops"].append({"kind": "while", "line": node.lineno})
            result["flow_nodes"].append({"line": node.lineno, "label": "While Loop", "kind": "loop"})
            # infinite loop heuristic: while True with no break inside
            if isinstance(node.test, ast.Constant) and node.test.value is True:
                has_break = any(isinstance(n, ast.Break) for n in ast.walk(node))
                if not has_break:
                    result["issues"].append(
                        make_issue(node.lineno, "Possible Infinite Loop",
                                   "This 'while True' loop has no 'break' statement anywhere inside it, "
                                   "so it may never terminate.", confirmed=False)
                    )
            self.generic_visit(node)

        def visit_If(self, node):
            result["components"]["conditions"].append({"line": node.lineno})
            result["flow_nodes"].append({"line": node.lineno, "label": "Condition Check", "kind": "condition"})
            self.generic_visit(node)

        def visit_Assign(self, node):
            for target in node.targets:
                for n in ast.walk(target):
                    if isinstance(n, ast.Name):
                        bound_names.add(n.id)
                if isinstance(target, ast.Name):
                    if target.id not in assigned_names:
                        assigned_names[target.id] = node.lineno
                    result["components"]["variables"].append({"name": target.id, "line": node.lineno})
            self.generic_visit(node)

        def visit_AugAssign(self, node):
            if isinstance(node.target, ast.Name):
                bound_names.add(node.target.id)
            self.generic_visit(node)

        def visit_AnnAssign(self, node):
            if isinstance(node.target, ast.Name):
                bound_names.add(node.target.id)
                if node.value is not None and node.target.id not in assigned_names:
                    assigned_names[node.target.id] = node.lineno
            self.generic_visit(node)

        def visit_Name(self, node):
            if isinstance(node.ctx, ast.Load):
                used_names.add(node.id)
            self.generic_visit(node)

        def visit_BinOp(self, node):
            if isinstance(node.op, ast.Div) or isinstance(node.op, ast.FloorDiv):
                # division by zero risk if RHS is a literal 0, or a bare name (unknown at static time)
                if isinstance(node.right, ast.Constant) and node.right.value == 0:
                    result["errors"].append(
                        make_error(node.lineno, "Logical Error", "High",
                                   "Division by zero.",
                                   "The right-hand side of this division is the literal 0.",
                                   "Guard the division with an `if divisor != 0:` check.")
                    )
                elif isinstance(node.right, ast.Name):
                    result["issues"].append(
                        make_issue(node.lineno, "Possible Division by Zero",
                                   f"'{node.right.id}' is used as a divisor; if it can be 0 at runtime "
                                   "this will raise ZeroDivisionError.", confirmed=False)
                    )
            self.generic_visit(node)

        def visit_Call(self, node):
            result["flow_nodes"].append({"line": getattr(node, "lineno", 0), "label": "Function Call", "kind": "call"})
            self.generic_visit(node)

    Visitor().visit(tree)

    # ---- undefined-name heuristic (flat/whole-tree, so flagged as a POTENTIAL issue, ----
    # ---- not a confirmed error — real scoping can make some of these false positives) ----
    builtin_names = set(dir(builtins)) | {"self", "cls", "__name__", "__file__", "__doc__"}
    reported_undefined = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id in bound_names or node.id in builtin_names:
                continue
            if node.id in reported_undefined:
                continue
            reported_undefined.add(node.id)
            result["issues"].append(
                make_issue(node.lineno, "Possibly Undefined Name",
                           f"'{node.id}' is used here but CodeLens can't find where it was assigned, "
                           "imported, or passed as a parameter — this may raise a NameError at runtime.",
                           confirmed=False)
            )

    # ---- unused-variable heuristic (module/function-level simple names only) ----
    for name, line in assigned_names.items():
        if name.startswith("_"):
            continue
        if name not in used_names:
            result["issues"].append(
                make_issue(line, "Unused Variable",
                           f"'{name}' is assigned on this line but never read anywhere else.",
                           confirmed=False)
            )

    # ---- unreachable code after return (simple, function-body level) ----
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            for i, stmt in enumerate(body[:-1]):
                if isinstance(stmt, ast.Return):
                    unreachable_line = body[i + 1].lineno
                    result["errors"].append(
                        make_error(unreachable_line, "Logical Error", "Medium",
                                   "Unreachable code after 'return'.",
                                   "This statement comes after a 'return' in the same block, so it never runs.",
                                   "Remove the dead code, or move it before the 'return'.")
                    )

    return result
