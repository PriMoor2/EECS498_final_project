from comet import download_model, load_from_checkpoint
import json
import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["USE_CPU"] = "1"

def evaluate_comet(input_path, output_path, model_name="wmt22-comet-da"):
    model_path = download_model(model_name)
    model = load_from_checkpoint(model_path)

    # Load dataset
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = []
    for item in data:
        src = item["input"]
        mt = item["output"]
        ref = item["reference"]

        score = model.predict([{
            "src": src,
            "mt": mt,
            "ref": ref
        }])

        results.append({
            "input": src,
            "reference": ref,
            "output": mt,
            "comet_score": score["scores"][0]
        })

    # Save output JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Done! Saved COMET-scored file to: {output_path}")


# --------------------------
# MAIN — edit these values
# --------------------------
if __name__ == "__main__":
    INPUT_FILE = "claude-sonnet-4-5-20250929-MAD-output.json"     
    OUTPUT_FILE = "claude-sonnet-4-5-20250929-MAD-COMET.json"  
    MODEL_NAME = "Unbabel/wmt22-comet-da"  #needs, input, output plus reference  

    evaluate_comet(INPUT_FILE, OUTPUT_FILE, MODEL_NAME)
