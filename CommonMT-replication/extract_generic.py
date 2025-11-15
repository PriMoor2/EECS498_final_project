import json
from typing import Any, List


def extract_field(data: Any, target_key: str, out_list: List[Any]):
    """
    Recursively extract all values associated with `target_key`.
    Handles lists, dicts, and nested JSON structures.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if key == target_key:
                out_list.append(value)
            extract_field(value, target_key, out_list)
    elif isinstance(data, list):
        for item in data:
            extract_field(item, target_key, out_list)


def main():
    # ---------------------------------------------------------
    # EDIT THESE VALUES
    input_file = "claude-sonnet-4-5-20250929-base-BLEURT.json"
    field = "bleurt_score"
    output_file = "output.txt"
    # ---------------------------------------------------------

    with open(input_file, "r") as f:
        data = json.load(f)

    extracted = []
    extract_field(data, field, extracted)

    # Write to plain .txt (one value per line)
    with open(output_file, "w") as f:
        for item in extracted:
            f.write(str(item) + "\n")

    print(f"Extracted {len(extracted)} values for '{field}' → {output_file}")


if __name__ == "__main__":
    main()
