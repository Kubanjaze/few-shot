import sys
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import argparse, os, json, re, warnings
warnings.filterwarnings("ignore")
import pandas as pd
from dotenv import load_dotenv
import anthropic

load_dotenv()
os.environ.setdefault("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY", ""))


def pic50_to_class(pic50: float) -> str:
    if pic50 < 5.0:   return "inactive"
    elif pic50 < 6.0: return "weak"
    elif pic50 < 7.0: return "moderate"
    elif pic50 < 8.0: return "potent"
    else:             return "highly_potent"


CLASS_DEFS = (
    "Activity classes: inactive (pIC50<5), weak (5-6), moderate (6-7), potent (7-8), highly_potent (>=8).\n"
    "Classify the compound and respond with ONLY JSON: {\"activity_class\": \"<class>\"}"
)

# Select diverse examples: one moderate, one potent, one highly_potent
EXAMPLES = [
    {"name": "benz_008_OMe", "pic50": 6.35, "class": "moderate"},
    {"name": "benz_001_F",   "pic50": 7.25, "class": "potent"},
    {"name": "benz_004_CF3", "pic50": 8.10, "class": "highly_potent"},
]


def build_zero_shot(row) -> list:
    return [{"role": "user", "content": f"{CLASS_DEFS}\n\nCompound: {row['compound_name']}, pIC50={row['pic50']:.2f}"}]


def build_few_shot(row) -> list:
    messages = []
    for ex in EXAMPLES:
        messages.append({"role": "user", "content": f"{CLASS_DEFS}\n\nCompound: {ex['name']}, pIC50={ex['pic50']:.2f}"})
        messages.append({"role": "assistant", "content": json.dumps({"activity_class": ex["class"]})})
    messages.append({"role": "user", "content": f"{CLASS_DEFS}\n\nCompound: {row['compound_name']}, pIC50={row['pic50']:.2f}"})
    return messages


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", required=True)
    parser.add_argument("--n-test", type=int, default=5)
    parser.add_argument("--model", default="claude-haiku-4-5-20251001")
    parser.add_argument("--output-dir", default="output")
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    df = pd.read_csv(args.input)
    # Exclude example compounds from test set
    example_names = {ex["name"] for ex in EXAMPLES}
    test_df = df[~df["compound_name"].isin(example_names)].head(args.n_test)

    client = anthropic.Anthropic()
    print(f"\nPhase 71 — Few-Shot Activity Classification")
    print(f"Model: {args.model} | Examples: {len(EXAMPLES)} | Test: {len(test_df)}\n")

    results = {"zero_shot": [], "few_shot": []}
    total_input = 0
    total_output = 0

    for mode_name, msg_builder in [("zero_shot", build_zero_shot), ("few_shot", build_few_shot)]:
        print(f"--- {mode_name.upper()} ---")
        for _, row in test_df.iterrows():
            messages = msg_builder(row)
            response = client.messages.create(model=args.model, max_tokens=64, messages=messages)
            text = "".join(b.text for b in response.content if hasattr(b, "text"))
            total_input += response.usage.input_tokens
            total_output += response.usage.output_tokens

            match = re.search(r'\{.*\}', text, re.DOTALL)
            parsed_class = json.loads(match.group()).get("activity_class", "?") if match else "?"
            true_class = pic50_to_class(row["pic50"])
            correct = parsed_class == true_class

            print(f"  {row['compound_name']:20s} true={true_class:15s} pred={parsed_class:15s} {'OK' if correct else 'MISS'}")
            results[mode_name].append({"compound": row["compound_name"], "true": true_class, "pred": parsed_class, "correct": correct})
        print()

    zs_acc = sum(1 for r in results["zero_shot"] if r["correct"]) / len(test_df)
    fs_acc = sum(1 for r in results["few_shot"] if r["correct"]) / len(test_df)
    cost = (total_input / 1e6 * 0.80) + (total_output / 1e6 * 4.0)

    report = (
        f"Phase 71 — Few-Shot Activity Classification\n{'='*50}\n"
        f"Model: {args.model}\nExamples: {len(EXAMPLES)} | Test: {len(test_df)}\n\n"
        f"Zero-shot accuracy: {zs_acc:.0%}\nFew-shot accuracy:  {fs_acc:.0%}\n"
        f"Delta: {fs_acc - zs_acc:+.0%}\n\n"
        f"Tokens: in={total_input} out={total_output}\nCost: ${cost:.4f}\n"
    )
    print(report)

    with open(os.path.join(args.output_dir, "fewshot_comparison.json"), "w") as f:
        json.dump(results, f, indent=2)
    with open(os.path.join(args.output_dir, "fewshot_report.txt"), "w") as f:
        f.write(report)
    print("Done.")


if __name__ == "__main__":
    main()
