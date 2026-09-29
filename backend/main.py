import os
import re
import secrets
import time
import hashlib
import difflib
import json
import sqlite3
import urllib.request
import urllib.error

from fastapi import FastAPI, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

import analyzer


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

D = os.path.dirname(os.path.abspath(__file__))


# ============================================================
# DATABASE
# ============================================================

def db():
    c = sqlite3.connect(
        os.path.join(D, "codelens.db")
    )
    c.row_factory = sqlite3.Row
    return c


with db() as c:
    c.executescript("""
        CREATE TABLE IF NOT EXISTS otps(
            email TEXT PRIMARY KEY,
            h TEXT,
            exp REAL
        );

        CREATE TABLE IF NOT EXISTS sess(
            tok TEXT PRIMARY KEY,
            email TEXT,
            ts REAL
        );

        CREATE TABLE IF NOT EXISTS hist(
            id INTEGER PRIMARY KEY,
            email TEXT,
            lang TEXT,
            kind TEXT,
            code TEXT,
            score INT,
            ts TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)


try:
    with db() as c:
        c.execute(
            "ALTER TABLE hist ADD COLUMN fav INT DEFAULT 0"
        )
except Exception:
    pass


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(title="CodeLens")


# ============================================================
# HELPERS
# ============================================================

H = lambda s: hashlib.sha256(s.encode()).hexdigest()


class E(BaseModel):
    email: str


class V(BaseModel):
    email: str
    code: str


class C(BaseModel):
    code: str
    lang: str = "python"
    explain: str = "en"
    to: str = "python"
    b: str = ""
    level: str = "expert"


# ============================================================
# RATE LIMIT
# ============================================================

RL = {}


def me(t):
    with db() as c:
        r = c.execute(
            "SELECT email,ts FROM sess WHERE tok=?",
            (t,)
        ).fetchone()

    if not r:
        raise HTTPException(401, "Please login")

    if time.time() - (r[1] or 0) > 7 * 86400:
        raise HTTPException(401, "Please login")

    w = [
        x for x in RL.get(t, [])
        if x > time.time() - 60
    ]

    if len(w) >= 120:
        raise HTTPException(
            429,
            "Too many requests, slow down"
        )

    RL[t] = w + [time.time()]

    return r[0]


# ============================================================
# GEMINI AI
# ============================================================

def ask(p):
    """
    Send a prompt to Google Gemini API.

    Returns:
        AI generated text
        None if API key is missing or API request fails
    """

    api_key = os.getenv("GEMINI_API_KEY")

    model = os.getenv(
        "GEMINI_MODEL",
        "gemini-3.8-flash"
    )

    if not api_key:
        print("Gemini API key is not configured.")
        return None

    url = (
        "https://generativelanguage.googleapis.com/"
        f"v1beta/models/{model}:generateContent"
    )

    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": p
                    }
                ]
            }
        ]
    }

    # Only retry temporary server/network errors.
    # Do NOT retry 429 quota errors.
    max_retries = 2

    for attempt in range(1, max_retries + 1):

        try:
            request = urllib.request.Request(
                url,
                data=json.dumps(data).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": api_key
                },
                method="POST"
            )

            with urllib.request.urlopen(
                request,
                timeout=60
            ) as response:

                result = json.load(response)

            candidates = result.get(
                "candidates",
                []
            )

            if not candidates:
                print("Gemini returned no candidates.")
                return None

            content = candidates[0].get(
                "content",
                {}
            )

            parts = content.get(
                "parts",
                []
            )

            if not parts:
                print("Gemini returned no content.")
                return None

            output = parts[0].get(
                "text",
                ""
            )

            if not output:
                return None

            output = re.sub(
                r"^```[a-zA-Z0-9_+#.-]*\s*",
                "",
                output.strip()
            )

            output = re.sub(
                r"\s*```$",
                "",
                output.strip()
            )

            return output.strip()

        except urllib.error.HTTPError as e:

            try:
                error_body = e.read().decode(
                    "utf-8",
                    errors="ignore"
                )
            except Exception:
                error_body = str(e)

            print(
                f"Gemini HTTP error "
                f"(attempt {attempt}/{max_retries}):",
                e.code,
                error_body
            )

            # 429 = quota/rate limit.
            # Retrying immediately will not solve a daily quota limit.
            if e.code == 429:
                print(
                    "Gemini quota/rate limit reached. "
                    "Using local fallback where available."
                )
                return None

            if e.code in (500, 502, 503, 504):

                if attempt < max_retries:

                    wait_time = attempt * 2

                    print(
                        f"Gemini temporarily unavailable. "
                        f"Retrying in {wait_time} seconds..."
                    )

                    time.sleep(wait_time)

                    continue

            return None

        except urllib.error.URLError as e:

            print(
                f"Gemini connection error "
                f"(attempt {attempt}/{max_retries}):",
                e
            )

            if attempt < max_retries:

                wait_time = attempt * 2

                print(
                    f"Retrying in {wait_time} seconds..."
                )

                time.sleep(wait_time)

                continue

            return None

        except Exception as e:

            print(
                "Gemini API error:",
                e
            )

            return None

    return None


# ============================================================
# LOCAL CODE CONVERTER
# ============================================================

def local_convert(code, from_lang, to_lang):
    """
    Basic local converter used when Gemini is unavailable.

    Supported:
        Python -> Java
        Python -> C++
        Python -> C
        Java -> Python
        C++ -> Python
        C -> Python

    Returns:
        Converted code or None.
    """

    source = from_lang.strip().lower()
    target = to_lang.strip().lower()

    if source == target:
        return code

    # --------------------------------------------------------
    # Python -> Java
    # --------------------------------------------------------

    if source == "python" and target == "java":

        lines = code.splitlines()

        result = [
            "public class Main {",
            "    public static void main(String[] args) {"
        ]

        for line in lines:

            stripped = line.strip()

            if not stripped:
                result.append("")
                continue

            if stripped.startswith("#"):
                result.append(
                    "        //" + stripped[1:]
                )
                continue

            if stripped.startswith("print(") and stripped.endswith(")"):

                value = stripped[6:-1]

                result.append(
                    f"        System.out.println({value});"
                )
                continue

            if re.match(
                r"^[A-Za-z_]\w*\s*=\s*.+$",
                stripped
            ):

                name, value = stripped.split(
                    "=",
                    1
                )

                result.append(
                    f"        var {name.strip()} = {value.strip()};"
                )
                continue

            result.append(
                "        " + stripped
            )

        result.extend([
            "    }",
            "}"
        ])

        return "\n".join(result)

    # --------------------------------------------------------
    # Python -> C++
    # --------------------------------------------------------

    if source == "python" and target in ("c++", "cpp"):

        lines = code.splitlines()

        result = [
            "#include <iostream>",
            "using namespace std;",
            "",
            "int main() {"
        ]

        for line in lines:

            stripped = line.strip()

            if not stripped:
                continue

            if stripped.startswith("#"):
                result.append(
                    "    //" + stripped[1:]
                )
                continue

            if stripped.startswith("print(") and stripped.endswith(")"):

                value = stripped[6:-1]

                result.append(
                    f"    cout << {value} << endl;"
                )
                continue

            if re.match(
                r"^[A-Za-z_]\w*\s*=\s*.+$",
                stripped
            ):

                name, value = stripped.split(
                    "=",
                    1
                )

                result.append(
                    f"    auto {name.strip()} = {value.strip()};"
                )
                continue

            result.append(
                "    " + stripped
            )

        result.extend([
            "    return 0;",
            "}"
        ])

        return "\n".join(result)

    # --------------------------------------------------------
    # Python -> C
    # --------------------------------------------------------

    if source == "python" and target == "c":

        lines = code.splitlines()

        result = [
            "#include <stdio.h>",
            "",
            "int main() {"
        ]

        for line in lines:

            stripped = line.strip()

            if not stripped:
                continue

            if stripped.startswith("#"):
                result.append(
                    "    //" + stripped[1:]
                )
                continue

            if stripped.startswith("print(") and stripped.endswith(")"):

                value = stripped[6:-1]

                result.append(
                    f"    printf(\"%d\\n\", {value});"
                )
                continue

            if re.match(
                r"^[A-Za-z_]\w*\s*=\s*.+$",
                stripped
            ):

                name, value = stripped.split(
                    "=",
                    1
                )

                result.append(
                    f"    int {name.strip()} = {value.strip()};"
                )
                continue

            result.append(
                "    " + stripped
            )

        result.extend([
            "    return 0;",
            "}"
        ])

        return "\n".join(result)

    # --------------------------------------------------------
    # Java -> Python
    # --------------------------------------------------------

    if source == "java" and target == "python":

        lines = code.splitlines()

        result = []

        for line in lines:

            stripped = line.strip()

            if stripped in (
                "public class Main {",
                "public static void main(String[] args) {",
                "}"
            ):
                continue

            if stripped.startswith("//"):
                result.append(
                    "#" + stripped[2:]
                )
                continue

            match = re.match(
                r'System\.out\.println\((.*)\);',
                stripped
            )

            if match:
                result.append(
                    f"print({match.group(1)})"
                )
                continue

            match = re.match(
                r'(?:int|double|float|String|var)\s+'
                r'([A-Za-z_]\w*)\s*=\s*(.*);',
                stripped
            )

            if match:
                result.append(
                    f"{match.group(1)} = {match.group(2)}"
                )
                continue

            if stripped:
                result.append(
                    stripped.rstrip(";")
                )

        return "\n".join(result)

    # --------------------------------------------------------
    # C++ -> Python
    # --------------------------------------------------------

    if source in ("c++", "cpp") and target == "python":

        lines = code.splitlines()

        result = []

        for line in lines:

            stripped = line.strip()

            if stripped.startswith("//"):
                result.append(
                    "#" + stripped[2:]
                )
                continue

            if stripped.startswith("#include"):
                continue

            if stripped in (
                "using namespace std;",
                "int main() {",
                "return 0;",
                "}"
            ):
                continue

            match = re.match(
                r'cout\s*<<\s*(.*?)\s*<<\s*endl;',
                stripped
            )

            if match:
                result.append(
                    f"print({match.group(1)})"
                )
                continue

            match = re.match(
                r'(?:int|float|double|auto)\s+'
                r'([A-Za-z_]\w*)\s*=\s*(.*);',
                stripped
            )

            if match:
                result.append(
                    f"{match.group(1)} = {match.group(2)}"
                )
                continue

            if stripped:
                result.append(
                    stripped.rstrip(";")
                )

        return "\n".join(result)

    # --------------------------------------------------------
    # C -> Python
    # --------------------------------------------------------

    if source == "c" and target == "python":

        lines = code.splitlines()

        result = []

        for line in lines:

            stripped = line.strip()

            if stripped.startswith("//"):
                result.append(
                    "#" + stripped[2:]
                )
                continue

            if stripped.startswith("#include"):
                continue

            if stripped in (
                "int main() {",
                "return 0;",
                "}"
            ):
                continue

            match = re.match(
                r'printf\(".*?%d.*?"\s*,\s*(.*?)\);',
                stripped
            )

            if match:
                result.append(
                    f"print({match.group(1)})"
                )
                continue

            match = re.match(
                r'(?:int|float|double)\s+'
                r'([A-Za-z_]\w*)\s*=\s*(.*);',
                stripped
            )

            if match:
                result.append(
                    f"{match.group(1)} = {match.group(2)}"
                )
                continue

            if stripped:
                result.append(
                    stripped.rstrip(";")
                )

        return "\n".join(result)

    return None


# ============================================================
# LOGIN
# ============================================================

@app.post("/api/login")
def login(e: E):

    m = e.email.strip().lower()

    if not re.fullmatch(
        r"[^@\s]+@[^@\s]+\.\w+",
        m
    ):
        raise HTTPException(
            400,
            "Enter a valid email"
        )

    t = secrets.token_hex(16)

    with db() as c:
        c.execute(
            "INSERT INTO sess VALUES(?,?,?)",
            (
                t,
                m,
                time.time()
            )
        )

    return {
        "token": t,
        "email": m
    }


# ============================================================
# ANALYZE
# ============================================================

@app.post("/api/analyze")
def an(
    b: C,
    x_token: str = Header("")
):

    u = me(x_token)

    r = analyzer.analyze(
        b.code,
        b.lang,
        b.explain,
        b.level
    )

    with db() as c:
        c.execute(
            """
            INSERT INTO hist
            (email, lang, kind, code, score)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                u,
                b.lang,
                "analyze",
                b.code,
                r["score"]
            )
        )

    return r


# ============================================================
# CODE FIX
# ============================================================

@app.post("/api/fix")
def fx(
    b: C,
    x_token: str = Header("")
):

    me(x_token)

    r = analyzer.analyze(
        b.code,
        b.lang
    )

    prompt = f"""
You are CodeLens, an AI code debugging assistant.

Fix all real bugs in the following {b.lang} code.

Known analyzer errors:
{json.dumps(r["errors"], ensure_ascii=False)}

Known security issues:
{json.dumps(r["security"], ensure_ascii=False)}

Requirements:
1. Return ONLY the corrected code.
2. Do not explain the changes.
3. Do not use Markdown code fences.
4. Preserve the original purpose of the program.
5. Do not invent unnecessary features.

Original code:

{b.code}
"""

    ai = ask(prompt)

    if ai:

        fixed = ai

        ch = [
            "AI-corrected code"
        ]

        ai_used = True

    else:

        fixed, ch = analyzer.autofix(
            b.code,
            b.lang,
            r["errors"]
        )

        # Local fallback for Python missing-colon errors
        if b.lang.lower() == "python":

            lines = fixed.splitlines()

            for e in r["errors"]:

                line_no = e.get("line")
                msg = str(
                    e.get("msg", "")
                )

                if (
                    line_no
                    and "expected ':'" in msg
                ):

                    i = line_no - 1

                    if 0 <= i < len(lines):

                        original = lines[i]

                        if not original.rstrip().endswith(":"):

                            lines[i] = (
                                original.rstrip()
                                + ":"
                            )

                            ch.append(
                                f"Line {line_no}: Added missing ':'"
                            )

            fixed = "\n".join(lines)

        ai_used = False

    return {
        "code": fixed,
        "changes": ch,
        "ai": ai_used,
        "diff": list(
            difflib.unified_diff(
                b.code.splitlines(),
                fixed.splitlines(),
                "original",
                "fixed",
                lineterm="",
                n=1
            )
        )
    }


# ============================================================
# CODE CONVERTER
# ============================================================

@app.post("/api/convert")
def cv(
    b: C,
    x_token: str = Header("")
):

    me(x_token)

    prompt = f"""
Convert the following {b.lang} program into {b.to}.

Requirements:
1. Return ONLY the converted code.
2. Do not explain.
3. Do not use Markdown code fences.
4. Preserve the original program's functionality.
5. Use correct syntax for {b.to}.

Original {b.lang} code:

{b.code}
"""

    output = ask(prompt)

    if output:

        return {
            "code": output,
            "note": "AI conversion using Gemini"
        }

    local_output = local_convert(
        b.code,
        b.lang,
        b.to
    )

    if local_output:

        return {
            "code": local_output,
            "note": (
                "Local fallback conversion used "
                "because Gemini is unavailable."
            )
        }

    return {
        "code": "",
        "note": (
            f"Gemini AI is unavailable and "
            f"local conversion from {b.lang} "
            f"to {b.to} is not supported yet."
        )
    }


# ============================================================
# CODE SIMILARITY
# ============================================================

@app.post("/api/similarity")
def sm(
    b: C,
    x_token: str = Header("")
):

    me(x_token)

    n = lambda s: re.findall(
        r"\w+|\S",
        s
    )

    percentage = round(
        difflib.SequenceMatcher(
            None,
            n(b.code),
            n(b.b),
            autojunk=False
        ).ratio() * 100,
        1
    )

    return {
        "pct": percentage
    }


# ============================================================
# HISTORY
# ============================================================

@app.get("/api/history")
def hs(
    q: str = "",
    fav: int = 0,
    x_token: str = Header("")
):

    u = me(x_token)

    with db() as c:

        rows = c.execute(
            """
            SELECT
                id,
                lang,
                kind,
                code,
                score,
                ts,
                fav
            FROM hist
            WHERE email=?
            AND (
                code LIKE ?
                OR lang LIKE ?
            )
            AND (
                ?=0
                OR fav=1
            )
            ORDER BY id DESC
            LIMIT 100
            """,
            (
                u,
                f"%{q}%",
                f"%{q}%",
                fav
            )
        ).fetchall()

    return [
        dict(r)
        for r in rows
    ]


# ============================================================
# FAVORITE HISTORY
# ============================================================

@app.post("/api/fav/{i}")
def favt(
    i: int,
    x_token: str = Header("")
):

    u = me(x_token)

    with db() as c:

        c.execute(
            """
            UPDATE hist
            SET fav = 1 - COALESCE(fav, 0)
            WHERE id=?
            AND email=?
            """,
            (
                i,
                u
            )
        )

    return {
        "ok": True
    }


# ============================================================
# COMPARE HISTORY
# ============================================================

@app.get("/api/compare")
def cmpr(
    a: int,
    b: int,
    x_token: str = Header("")
):

    u = me(x_token)

    with db() as c:

        rows = [
            c.execute(
                """
                SELECT code, score
                FROM hist
                WHERE id=?
                AND email=?
                """,
                (
                    i,
                    u
                )
            ).fetchone()
            for i in (a, b)
        ]

    if not all(rows):

        raise HTTPException(
            404,
            "Not found"
        )

    return {
        "a": rows[0]["score"],
        "b": rows[1]["score"],
        "diff": list(
            difflib.unified_diff(
                rows[0]["code"].splitlines(),
                rows[1]["code"].splitlines(),
                "A",
                "B",
                lineterm="",
                n=1
            )
        )
    }


# ============================================================
# STATISTICS
# ============================================================

@app.get("/api/stats")
def stt(
    x_token: str = Header("")
):

    u = me(x_token)

    with db() as c:

        rows = c.execute(
            """
            SELECT lang, code, score
            FROM hist
            WHERE email=?
            ORDER BY id DESC
            LIMIT 50
            """,
            (u,)
        ).fetchall()

    lg = {}
    er = {}

    for r in rows:

        lg[r["lang"]] = (
            lg.get(r["lang"], 0) + 1
        )

        analysis = analyzer.analyze(
            r["code"],
            r["lang"]
        )

        for e in analysis["errors"]:

            k = (
                e["msg"]
                .split("'")[0]
                .strip(" :")
            )

            er[k] = (
                er.get(k, 0) + 1
            )

    return {
        "trend": [
            r["score"]
            for r in rows
        ][::-1],

        "langs": lg,

        "errors": er
    }


# ============================================================
# AI TOOLS
# ============================================================

@app.post("/api/ai")
def aitool(
    b: C,
    x_token: str = Header("")
):

    me(x_token)

    prompts = {

        "ask": f"""
Answer this question about the {b.lang} code.

Question:
{b.b}

Return a clear and beginner-friendly answer.
""",

        "docstring": f"""
Add clear docstrings and useful comments to this {b.lang} code.

Requirements:
1. Return ONLY code.
2. Do not use Markdown code fences.
3. Keep the program functionality unchanged.

Code:

{b.code}
""",

        "tests": f"""
Write appropriate unit tests for this {b.lang} code.

Requirements:
1. Return ONLY test code.
2. Do not use Markdown code fences.
3. Cover the important functionality.

Code:

{b.code}
""",

        "readme": f"""
Create a clear README.md for this {b.lang} program.

Include:
- Project title
- Description
- Features
- Requirements
- How to run
- Example usage

Return ONLY the README content.

Code:

{b.code}
"""
    }

    selected_prompt = prompts.get(
        b.to,
        prompts["ask"]
    )

    output = ask(
        selected_prompt
    )

    return {
        "code": output or "",
        "note": (
            ""
            if output
            else
            "Gemini AI is not available. "
            "Check GEMINI_API_KEY in backend/.env."
        )
    }


# ============================================================
# SERVE FRONTEND
# ============================================================

app.mount(
    "/",
    StaticFiles(
        directory=os.path.join(
            D,
            "..",
            "frontend"
        ),
        html=True
    )
)