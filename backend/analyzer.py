import ast, re
LANGS = ("python", "java", "c", "cpp", "javascript")
SEC = [(r"\bgets\s*\(", "gets() - buffer overflow", "High"), (r"\bstrcpy\s*\(", "strcpy() - unbounded copy", "Medium"),
       (r"\bsystem\s*\(|os\.system|getRuntime\(\)\.exec", "Shell command execution", "High"),
       (r"\beval\s*\(|\bexec\s*\(", "eval/exec - code injection", "High"), (r"innerHTML|document\.write", "XSS risk", "Medium"),
       (r"(?i)(password|passwd|secret|api_?key)\s*=\s*[\"'][^\"']+[\"']", "Hardcoded credential", "High"),
       (r"(?i)\b(select|delete|update|insert)\b[^\n]*(\"\s*\+|'\s*\+|\{\w+\})", "Possible SQL injection", "High"),
       (r"pickle\.loads?", "Unsafe deserialization", "Medium")]

def security(src):
    return [dict(line=i, msg=m, sev=s) for i, l in enumerate(src.splitlines(), 1) for p, m, s in SEC if re.search(p, l)]

def py_check(src):
    E = []
    try: t = ast.parse(src)
    except SyntaxError as e: return [dict(line=e.lineno or 1, msg="SyntaxError: " + (e.msg or ""), sev="error")], None
    st, ld = {}, set()
    for n in ast.walk(t):
        if isinstance(n, ast.ExceptHandler) and n.type is None: E.append(dict(line=n.lineno, msg="Bare 'except:' hides errors", sev="warning"))
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and any(isinstance(d, (ast.List, ast.Dict, ast.Set)) for d in n.args.defaults):
            E.append(dict(line=n.lineno, msg="Mutable default argument", sev="warning"))
        if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Div, ast.FloorDiv, ast.Mod)) and isinstance(n.right, ast.Constant) and n.right.value == 0:
            E.append(dict(line=n.lineno, msg="Division by zero", sev="error"))
        if isinstance(n, ast.Compare) and any(isinstance(o, (ast.Eq, ast.NotEq)) for o in n.ops) and any(isinstance(c, ast.Constant) and c.value is None for c in n.comparators):
            E.append(dict(line=n.lineno, msg="Use 'is None' instead of '== None'", sev="warning"))
        if isinstance(n, ast.While) and isinstance(n.test, ast.Constant) and n.test.value is True and not any(isinstance(k, ast.Break) for k in ast.walk(n)):
            E.append(dict(line=n.lineno, msg="Possible infinite loop (no break)", sev="warning"))
        if isinstance(n, ast.Name):
            if isinstance(n.ctx, ast.Store): st.setdefault(n.id, n.lineno)
            else: ld.add(n.id)
    E += [dict(line=l, msg=f"Variable '{k}' assigned but never used", sev="warning") for k, l in st.items() if k not in ld and k != "_"]
    return E, t

def c_check(src, lang):
    L = src.splitlines(); E = []
    if src.count("{") != src.count("}"): E.append(dict(line=len(L), msg="Unbalanced braces { }", sev="error"))
    if src.count("(") != src.count(")"): E.append(dict(line=len(L), msg="Unbalanced parentheses ( )", sev="error"))
    for i, l in enumerate(L, 1):
        s = l.strip()
        if not s or s.startswith(("//", "#", "/*", "*", "@", "}", "{")) or s.endswith((";", "{", "}", ",", ":", "(", "/*")): continue
        if re.match(r"(if|for|while|else|switch|do|try|catch|finally|case|default)\b", s) or re.match(r"^(?!return)[\w:<>\*&\[\]]+(\s+[\w:<>\*&\[\]]+)+\s*\(", s): continue
        E.append(dict(line=i, msg="Missing semicolon ';'", sev="warning" if lang == "javascript" else "error"))
    return E

def py_flow(t, L):
    out = [dict(t="start", l="Start", line=0, d=0, lp=0)]
    tx = lambda s: (L[s.lineno - 1].strip() if s.lineno <= len(L) else "")[:38].rstrip(":")
    def w(b, d, lp):
        for s in b:
            if isinstance(s, ast.If): out.append(dict(t="decision", l=tx(s), line=s.lineno, d=d, lp=lp)); w(s.body, d + 1, lp); w(s.orelse, d + 1, lp)
            elif isinstance(s, (ast.For, ast.While)): out.append(dict(t="loop", l=tx(s), line=s.lineno, d=d, lp=lp + 1)); w(s.body, d + 1, lp + 1)
            elif isinstance(s, (ast.FunctionDef, ast.ClassDef)): out.append(dict(t="process", l=tx(s), line=s.lineno, d=d, lp=lp)); w(s.body, d + 1, lp)
            else: out.append(dict(t="end" if isinstance(s, ast.Return) else "process", l=tx(s), line=s.lineno, d=d, lp=lp))
    w(t.body, 0, 0); return out + [dict(t="end", l="End", line=0, d=0, lp=0)]

def g_flow(src):
    out = [dict(t="start", l="Start", line=0, d=0, lp=0)]; d = 0; stk = []
    for i, l in enumerate(src.splitlines(), 1):
        s = l.strip()
        if not s or s.startswith(("//", "#", "/*", "*")): continue
        while stk and d <= stk[-1]: stk.pop()
        t = None
        if re.match(r"(else\s+)?if\b|switch\b", s): t = "decision"
        elif re.match(r"(for|while)\b", s): t = "loop"; stk.append(d)
        elif s.startswith("return"): t = "end"
        elif s.lstrip("}").strip(" {"): t = "process"
        if t: out.append(dict(t=t, l=s[:38], line=i, d=d, lp=len(stk)))
        d += s.count("{") - s.count("}")
    return out + [dict(t="end", l="End", line=0, d=0, lp=0)]

TPL = {"en": dict(fn="Defines function '{n}'", cls="Defines class '{n}'", if_="Runs the block only if: {n}", elif_="Else-if check: {n}", else_="Runs when all conditions fail",
        for_="Loop: repeats for each item - {n}", while_="Repeats while true - {n}", ret="Returns a value: {n}", imp="Imports library/header: {n}",
        out="Prints output: {n}", asg="Stores a value in a variable: {n}", end="Block ends", cm="Comment", oth="Executes: {n}"),
    "ta": dict(fn="'{n}' nu oru function define pannuthu", cls="'{n}' nu oru class create pannuthu", if_="Condition sari na mattum indha block run aagum: {n}",
        elif_="Munnadi condition fail aana idha check pannum: {n}", else_="Ella condition um fail aana idhu run aagum", for_="Loop: oru oru item ku thirumba run aagum - {n}",
        while_="Condition true irukura varaikkum repeat aagum - {n}", ret="Value ah thirumba tharum: {n}", imp="Library/header include pannuthu: {n}",
        out="Screen la output print pannuthu: {n}", asg="Variable la value store pannuthu: {n}", end="Block mudiyuthu", cm="Comment", oth="Idhu run aagum: {n}"),
    "hi": dict(fn="'{n}' naam ka function banata hai", cls="'{n}' naam ki class banata hai", if_="Sharat sahi hone par hi yeh block chalega: {n}",
        elif_="Pehli sharat galat ho to yeh check hoga: {n}", else_="Sabhi sharten galat hone par yeh chalega", for_="Loop: har item ke liye dohrata hai - {n}",
        while_="Jab tak sharat sahi hai dohrata hai - {n}", ret="Value wapas deta hai: {n}", imp="Library/header import karta hai: {n}",
        out="Screen par output dikhata hai: {n}", asg="Variable mein value rakhta hai: {n}", end="Block khatam", cm="Comment", oth="Yeh chalega: {n}")}

def classify(s):
    if s in ("{", "}", "};"): return "end", ""
    if s.startswith(("//", "/*", "*")) or (s.startswith("#") and not s.startswith(("#include", "#define"))): return "cm", ""
    for p, k in [(r"^(?:async\s+)?(?:def|function)\s+(\w+)", "fn"), (r"^class\s+(\w+)", "cls"), (r"^(?:elif|else\s+if)\b", "elif_"), (r"^else\b", "else_"),
                 (r"^if\b", "if_"), (r"^(?:for|foreach)\b", "for_"), (r"^while\b", "while_"), (r"^return\b", "ret"), (r"^(?:import|from|#include|using|package)\b", "imp"),
                 (r"\b(?:print|printf|cout|println|console\.log)\b", "out"), (r"^(?!if|for|while|switch)[\w:<>\*&\s]+\s\**(\w+)\s*\([^;]*\)\s*\{?$", "fn"), (r"[^=!<>]=[^=]", "asg")]:
        m = re.search(p, s)
        if m: return k, (m.group(1) if m.groups() else s[:50])
    return "oth", s[:50]

def explain(src, lang):
    T = TPL.get(lang, TPL["en"]); o = []
    for i, l in enumerate(src.splitlines(), 1):
        if l.strip(): k, n = classify(l.strip()); o.append(dict(line=i, code=l, text=T[k].format(n=n or l.strip()[:50])))
    return o

def _base(code, lang="python", ex="en"):
    lang = lang if lang in LANGS else "python"
    if lang == "python":
        E, t = py_check(code)
        flow = py_flow(t, code.splitlines()) if t else g_flow(code)
        cc = 1 + sum(isinstance(n, (ast.If, ast.For, ast.While, ast.IfExp, ast.ExceptHandler, ast.comprehension)) + (len(n.values) - 1 if isinstance(n, ast.BoolOp) else 0) for n in ast.walk(t)) if t else 0
    else:
        E = c_check(code, lang); flow = g_flow(code); cc = 1 + len(re.findall(r"\b(?:if|for|while|case|catch)\b|&&|\|\|", code))
    sec = security(code); mx = max(n["lp"] for n in flow)
    sc = 100 - 15 * sum(e["sev"] == "error" for e in E) - 5 * sum(e["sev"] == "warning" for e in E) - sum(6 if s["sev"] == "High" else 3 for s in sec) - max(0, cc - 10) * 2
    return dict(errors=E, security=sec, flow=flow, explanation=explain(code, ex), score=max(0, min(100, sc)),
                complexity=dict(cc=cc, nesting=max(n["d"] for n in flow), bigo="O(1)" if mx == 0 else "O(n)" if mx == 1 else f"O(n^{mx})",
                                level="Low" if cc <= 5 else "Moderate" if cc <= 10 else "High"), heuristic=lang != "python")

def autofix(code, lang, errors):
    L = code.split("\n"); ch = []
    for e in errors:
        i = e["line"] - 1
        if not 0 <= i < len(L): continue
        o = L[i]
        if "semicolon" in e["msg"] and not o.rstrip().endswith(";"): L[i] = o.rstrip() + ";"
        elif "Bare" in e["msg"]: L[i] = o.replace("except:", "except Exception:")
        elif "is None" in e["msg"]: L[i] = re.sub(r"!=\s*None", "is not None", re.sub(r"==\s*None", "is None", o))
        if L[i] != o: ch.append(f"Line {e['line']}: {e['msg']}")
    return "\n".join(L), ch

import random
HINT = dict(fn="Functions let you reuse code.", for_="Loops avoid repeating code.", if_="Decisions run different code for different cases.", while_="Make sure the condition eventually becomes false.", asg="A variable is a named box holding a value.")
WHY = [("syntaxerror", "Python could not parse this line - check colons, brackets, indentation."), ("semicolon", "C-family statements must end with ';'."), ("unbalanced", "Every opening bracket needs a closing one."),
       ("division by zero", "Dividing by zero crashes the program. Check the divisor first."), ("bare", "Bare except also catches Ctrl+C. Catch specific exceptions."),
       ("mutable default", "Default lists/dicts are shared between calls. Use None and create inside."), ("is none", "'is' is the correct identity check for None."),
       ("never used", "Unused variables add noise and may hide typos."), ("infinite", "Add a break or a changing condition so the loop can end."), ("gets", "gets() cannot limit input; use fgets()."),
       ("eval", "eval runs arbitrary text as code."), ("credential", "Keep secrets in environment variables."), ("sql", "Use parameterized queries.")]
CON = [("Functions", r"\bdef\b|\bfunction\b"), ("OOP / Classes", r"\bclass\b"), ("Loops", r"\b(for|while)\b"), ("Conditionals", r"\bif\b"), ("Exception handling", r"\b(try|catch|except)\b"),
       ("Sorting", r"sort|bubble|quick|merge"), ("File handling", r"\bopen\s*\(|fopen|FileReader|readFile"), ("Data structures", r"\[|dict|vector|ArrayList|HashMap|\bmap\b")]
PS = dict(fn="FUNCTION {n}", cls="CLASS {n}", if_="IF {n} THEN", elif_="ELSE IF {n} THEN", else_="ELSE", for_="FOR EACH {n}", while_="WHILE {n} DO", ret="RETURN {n}", imp="USE {n}", out="DISPLAY {n}", asg="SET {n}", oth="DO {n}")

def pseudo(src):
    o = []
    for l in src.splitlines():
        s = l.strip()
        if not s: continue
        k, n = classify(s)
        if k not in ("end", "cm"): o.append(l[:len(l) - len(l.lstrip())] + PS[k].format(n=re.sub(r"^(if|elif|else if|while|for|return)\b\s*|[:{]\s*$", "", n).strip()))
    return "\n".join(o)

def extras(src, lang):
    L = src.splitlines(); sm, dd, pf, fn, cnt = [], [], [], [], {}
    for i, l in enumerate(L, 1):
        s = l.strip()
        if len(s) > 12 and not s.startswith(("//", "#", "*", "}", "{")): cnt.setdefault(s, []).append(i)
        if len(l) > 120: sm.append(dict(line=i, msg="Line longer than 120 characters"))
    sm += [dict(line=v[1], msg=f"Duplicate line appears {len(v)} times - extract a function") for v in cnt.values() if len(v) >= 3]
    if lang != "python": return sm, dd, pf, fn
    try: t = ast.parse(src)
    except SyntaxError: return sm, dd, pf, fn
    imp = {}; used = {n.id for n in ast.walk(t) if isinstance(n, ast.Name)}
    for n in ast.walk(t):
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names: imp[(a.asname or a.name).split(".")[0]] = n.lineno
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            ln = (n.end_lineno or n.lineno) - n.lineno + 1
            fn.append(dict(name=n.name, line=n.lineno, lines=ln, cc=1 + sum(isinstance(k, (ast.If, ast.For, ast.While, ast.IfExp, ast.ExceptHandler)) for k in ast.walk(n)),
                           rec=any(isinstance(k, ast.Call) and getattr(k.func, "id", "") == n.name for k in ast.walk(n))))
            if ln > 30: sm.append(dict(line=n.lineno, msg=f"Function '{n.name}' is {ln} lines long - split it"))
            if len(n.args.args) > 5: sm.append(dict(line=n.lineno, msg=f"Function '{n.name}' has {len(n.args.args)} parameters"))
        b = getattr(n, "body", None)
        if isinstance(b, list):
            dd += [dict(line=c.lineno, msg="Unreachable code after return/break/raise") for a, c in zip(b, b[1:]) if isinstance(a, (ast.Return, ast.Break, ast.Continue, ast.Raise))]
        if isinstance(n, ast.For) and len(n.body) == 1 and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Call) and getattr(n.body[0].value.func, "attr", "") == "append":
            pf.append(dict(line=n.lineno, msg="Loop that only appends - use a list comprehension"))
        if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "range" and n.args and isinstance(n.args[0], ast.Call) and getattr(n.args[0].func, "id", "") == "len":
            pf.append(dict(line=n.lineno, msg="range(len(x)) - iterate directly or use enumerate()"))
    dd += [dict(line=l, msg=f"Unused import '{k}'") for k, l in imp.items() if k not in used]
    return sm, dd, pf, fn

def quiz(r):
    c = r["complexity"]; q = []
    def mk(t, a, pool):
        o = list(dict.fromkeys([a] + [x for x in pool if x != a]))[:4]; random.shuffle(o); q.append(dict(q=t, opts=[str(x) for x in o], ans=o.index(a)))
    mk("What is the cyclomatic complexity of this code?", c["cc"], [c["cc"] + 1, max(1, c["cc"] - 1), c["cc"] + 3])
    mk("Estimated time complexity?", c["bigo"], ["O(1)", "O(n)", "O(n^2)", "O(log n)"])
    ne = len(r["errors"]); mk("How many errors were detected?", ne, [ne + 1, ne + 2, max(0, ne - 1)])
    mk("Maximum nesting depth?", c["nesting"], [c["nesting"] + 1, c["nesting"] + 2, max(0, c["nesting"] - 1)])
    return q

def analyze(code, lang="python", ex="en", level="expert"):
    r = _base(code, lang, ex); lang = lang if lang in LANGS else "python"
    for e in r["errors"] + r["security"]: e["why"] = next((w for k, w in WHY if k in e["msg"].lower()), "")
    if level == "beginner":
        for x in r["explanation"]:
            h = HINT.get(classify(x["code"].strip())[0]); x["text"] += " 💡 " + h if h else ""
    r["smells"], r["dead"], r["perf"], r["funcs"] = extras(code, lang); c = r["complexity"]
    if c["nesting"] > 3: r["smells"].append(dict(line=1, msg=f"Deep nesting ({c['nesting']} levels) - simplify"))
    if c["bigo"].startswith("O(n^"): r["perf"].append(dict(line=1, msg="Nested loops: try a set/dict lookup or sorting to cut runtime"))
    r["concepts"] = [n for n, p in CON if re.search(p, code)] + (["Recursion"] if any(f.get("rec") for f in r["funcs"]) else [])
    r["pseudo"] = pseudo(code); r["quiz"] = quiz(r); return r
