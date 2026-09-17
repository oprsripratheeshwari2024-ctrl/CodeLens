"""
Shared data shapes returned by every language analyzer.
Every analyzer (python / java / cpp / c) returns a dict with this
same shape so the rest of the pipeline (flowchart, AI, quality,
report) can stay language-agnostic.
"""

from typing import TypedDict, List, Dict, Any


def empty_result() -> Dict[str, Any]:
    return {
        "components": {
            "variables": [],
            "functions": [],
            "classes": [],
            "conditions": [],
            "loops": [],
            "imports": [],
        },
        "errors": [],       # confirmed syntax/logical errors
        "issues": [],       # potential issues / bugs (not confirmed)
        "structure": [],    # function/class call-tree edges: {"from": "main", "to": "login"}
        "flow_nodes": [],   # sequential steps used for flowchart generation
        "line_count": 0,
        "analyzer_note": None,  # set when a real parser wasn't available (fallback used)
    }


def make_error(line: int, error_type: str, severity: str, problem: str,
               why: str = "", how_to_fix: str = "") -> Dict[str, Any]:
    return {
        "line": line,
        "type": error_type,
        "severity": severity,  # "High" | "Medium" | "Low"
        "problem": problem,
        "why": why,
        "how_to_fix": how_to_fix,
    }


def make_issue(line: int, issue_type: str, description: str, confirmed: bool = False) -> Dict[str, Any]:
    return {
        "line": line,
        "type": issue_type,
        "description": description,
        "confirmed": confirmed,  # False = "Potential Issue", True = "Confirmed Error"
    }
