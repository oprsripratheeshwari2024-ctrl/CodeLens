"""
Builds a React-Flow-compatible graph (nodes + edges) from the
sequential `flow_nodes` collected by a language analyzer. Each node
maps back to a source-code line, so the frontend can create the
Source Code <-> Flowchart <-> Explanation link described in section 19.
"""


def build_flowchart(code: str, flow_nodes: list) -> dict:
    lines = code.splitlines()
    nodes = []
    edges = []

    # START node
    nodes.append({
        "id": "start",
        "type": "input",
        "data": {"label": "START", "kind": "start", "line": 0, "code": ""},
        "position": {"x": 0, "y": 0},
    })

    prev_id = "start"
    y = 100
    sorted_steps = sorted(flow_nodes, key=lambda s: s.get("line", 0))

    for idx, step in enumerate(sorted_steps):
        node_id = f"step-{idx}"
        line_no = step.get("line", 0)
        code_line = lines[line_no - 1] if 0 < line_no <= len(lines) else ""
        nodes.append({
            "id": node_id,
            "data": {
                "label": step.get("label", "Step"),
                "kind": step.get("kind", "step"),
                "line": line_no,
                "code": code_line.strip(),
            },
            "position": {"x": 0, "y": y},
        })
        edges.append({"id": f"e-{prev_id}-{node_id}", "source": prev_id, "target": node_id})
        prev_id = node_id
        y += 100

    # END node
    nodes.append({
        "id": "end",
        "type": "output",
        "data": {"label": "END", "kind": "end", "line": 0, "code": ""},
        "position": {"x": 0, "y": y},
    })
    edges.append({"id": f"e-{prev_id}-end", "source": prev_id, "target": "end"})

    return {"nodes": nodes, "edges": edges}
