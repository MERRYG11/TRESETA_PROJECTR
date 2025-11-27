
import json
import os
import subprocess
import sys
from pathlib import Path

# Base directory = project root (one level up from mcp_server/)
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


# --------------------- tool implementations ---------------------


def tool_list_files(args: dict):
    """
    List available data files. Assumes CSV files are in ../data.
    Returns a list of relative paths like "data/phone.csv".
    """
    files = []
    if DATA_DIR.exists():
        for p in DATA_DIR.glob("*.csv"):
            # Return paths relative to BASE_DIR so caller can reuse them
            rel = os.path.relpath(p, BASE_DIR)
            files.append(rel)
    return {"files": files}


def tool_column_prediction(args: dict):
    """
    Call predict.py for a given file and column.
    Args:
      file_path: path to CSV, relative to project root (BASE_DIR)
      column_name: name of the column to classify
    Returns:
      { "label": "<semantic_type>" }
    """
    file_path = args.get("file_path")
    column_name = args.get("column_name")
    if not file_path or not column_name:
        raise ValueError("Both 'file_path' and 'column_name' are required.")

    abs_file = BASE_DIR / file_path

    cmd = [
        sys.executable,
        str(BASE_DIR / "predict.py"),
        "--input",
        str(abs_file),
        "--column",
        column_name,
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"predict.py failed: {proc.stderr.strip()}")

    label = proc.stdout.strip()
    return {"label": label}


def tool_parse_file(args: dict):
    """
    Call parser.py for a given file.
    Args:
      file_path: path to CSV, relative to project root (BASE_DIR)
    Returns:
      {
        "input": "<file_path>",
        "output": "output.csv"
      }
    """
    file_path = args.get("file_path")
    if not file_path:
        raise ValueError("'file_path' is required.")

    abs_file = BASE_DIR / file_path

    cmd = [
        sys.executable,
        str(BASE_DIR / "parser.py"),
        "--input",
        str(abs_file),
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"parser.py failed: {proc.stderr.strip()}")

    # parser.py always writes "output.csv" in BASE_DIR
    output_path = os.path.relpath(BASE_DIR / "output.csv", BASE_DIR)

    return {
        "input": file_path,
        "output": output_path,
        "log": proc.stdout.strip(),
    }


TOOLS = {
    "list_files": tool_list_files,
    "column_prediction": tool_column_prediction,
    "parse_file": tool_parse_file,
}


def handle_request(req: dict):
    """
    Dispatch a single JSON request to the appropriate tool.
    """
    req_id = req.get("id")
    tool_name = req.get("tool")
    args = req.get("args", {}) or {}

    if tool_name == "list_tools":
        # Special helper: return available tools
        return {
            "id": req_id,
            "ok": True,
            "result": {
                "tools": list(TOOLS.keys())
            },
        }

    if tool_name not in TOOLS:
        return {
            "id": req_id,
            "ok": False,
            "error": f"Unknown tool: {tool_name}",
        }

    tool_fn = TOOLS[tool_name]
    try:
        result = tool_fn(args)
        return {
            "id": req_id,
            "ok": True,
            "result": result,
        }
    except Exception as e:
        return {
            "id": req_id,
            "ok": False,
            "error": str(e),
        }


def main():
    """
    Main loop: read one JSON object per line from stdin, write one JSON object
    per line to stdout.
    """
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError as e:
            resp = {
                "id": None,
                "ok": False,
                "error": f"Invalid JSON: {e}",
            }
            print(json.dumps(resp), flush=True)
            continue

        resp = handle_request(req)
        print(json.dumps(resp), flush=True)


if __name__ == "__main__":
    main()
