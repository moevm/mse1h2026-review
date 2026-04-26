import os
import json
import re
from jsonschema import validate, ValidationError
from collections import Counter

from pprint import pprint

REVIEW_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "required": [
            "file",
            "line",
            "message",
            "suggestion",
            "error_type",
            "error_topic"
        ],
        "properties": {
            "file": {"type": "string", "minLength": 1},
            "line": {"type": "integer", "minimum": 1},
            "message": {"type": "string", "minLength": 1},
            "suggestion": {
                "type": ["string", "null"]
            },
            "error_type": {"type": "string"},
            "error_topic": {"type": "string"}
        },
        "additionalProperties": False
    }
}

def extract_json_from_llm(raw: str):

    raw = raw.strip()

    match = re.search(r"```json\s*(.*?)\s*```", raw, re.DOTALL)

    if match:
        raw = match.group(1).strip()

    return json.loads(raw)


def process_artifact(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        artifact = json.load(f)

    response_text = artifact["data"]["response"]

    try:
        parsed = extract_json_from_llm(response_text)

        validate(instance=parsed, schema=REVIEW_SCHEMA)

        return {
            "file": file_path,
            "status": "valid",
            "items_count": len(parsed),
            "errors": None,
            "parsed": parsed
        }

    except ValidationError as e:
        return {
            "file": file_path,
            "status": "invalid",
            "items_count": 0,
            "errors": e.message,
            "parsed": None
        }

    except Exception as e:
        return {
            "file": file_path,
            "status": "invalid",
            "items_count": 0,
            "errors": str(e),
            "parsed": None
        }


def process_folder(folder_path):
    results = []

    global_type_stats = Counter()
    global_topic_stats = Counter()

    total_files = 0
    valid_files = 0
    invalid_files = 0
    comment_count = 0

    for file_name in os.listdir(folder_path):
        if not file_name.endswith(".json"):
            continue

        total_files += 1
        file_path = os.path.join(folder_path, file_name)

        result = process_artifact(file_path)

        results.append(result)

        if result["status"] == "valid":
            valid_files += 1

            parsed = result["parsed"]

            comment_count += len(parsed)

            for item in parsed:
                global_type_stats[item["error_type"]] += 1
                global_topic_stats[item["error_topic"]] += 1

        else:
            invalid_files += 1
    ans = {
        "total_files": total_files,
        "valid_files": valid_files,
        "invalid_files": invalid_files,
        "comment_count": comment_count,
        "error_type_stats": dict(global_type_stats),
        "error_topic_stats": dict(global_topic_stats)
    }

    pprint(ans)
    return ans
