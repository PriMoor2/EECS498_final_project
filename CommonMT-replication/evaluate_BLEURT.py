import json
from evaluate import load

import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""


def evaluate_bleurt(input_path, output_path, model_name="bleurt-base-128"):
    # Load BLEURT metric
    bleurt = load("bleurt", module_type="metric")  # Hugging Face evaluate metric

    # Load dataset
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = []
    for item in data:
        src = item["input"]
        mt = item["output"]
        ref = item["reference"]

        # Compute BLEURT score
        score = bleurt.compute(predictions=[mt], references=[ref])["scores"][0]

        results.append({
            "input": src,
            "reference": ref,
            "output": mt,
            "bleurt_score": score
        })

    # Save output JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Done! Saved BLEURT-scored file to: {output_path}")


# --------------------------
# MAIN — edit these values
# --------------------------
if __name__ == "__main__":
    INPUT_FILE = "claude-sonnet-4-5-20250929-MAD-output.json"
    OUTPUT_FILE = "claude-sonnet-4-5-20250929-MAD-BLEURT.json"

    evaluate_bleurt(INPUT_FILE, OUTPUT_FILE)
