"""Zero-shot LLM classification of each clause (no training data used).

Needs:  pip install anthropic     and     set ANTHROPIC_API_KEY
usage:  python run_llm.py [model_name]
Makes one API call per clause (266 calls). The prompt gives the model each rule's
name and description for the clause's document type and asks for one rule ID or NONE.
Because nothing is trained, every clause is scored without cross-validation.
"""
import json, os, re, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import knowledge_base as kb
from common import load, save_predictions

MODEL = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("LLM_MODEL", "claude-sonnet-5-5")


def prompt(doc_type, clause):
    rules = [r for r in kb.RULES if r["doc_type"] == doc_type]
    listing = "\n".join(f'{r["id"]}: {r["name"]} - {r["description"]}' for r in rules)
    return (
        f"You classify clauses of a Malaysian {doc_type} contract.\n"
        f"Rules:\n{listing}\n\n"
        "Decide which single rule the clause below addresses (it states, restricts or "
        "provides for the topic of that rule). If it addresses none of them, answer NONE.\n"
        'Reply with JSON only, like {"rule": "E003"} or {"rule": "NONE"}.\n\n'
        f"Clause: {clause}"
    )


def main():
    import anthropic
    client = anthropic.Anthropic()
    df = load()
    valid = {r["id"] for r in kb.RULES} | {"NONE"}
    preds = []
    for i, row in df.iterrows():
        for attempt in range(3):
            try:
                msg = client.messages.create(model=MODEL, max_tokens=50, temperature=0,
                                             messages=[{"role": "user", "content": prompt(row["doc_type"], row["text"])}])
                m = re.search(r'"rule"\s*:\s*"([A-Z0-9]+)"', msg.content[0].text)
                rule = m.group(1) if m else "NONE"
                break
            except Exception as e:
                print("retry:", e); time.sleep(2 * (attempt + 1)); rule = "NONE"
        if rule not in valid or (rule != "NONE" and rule[0] != ("E" if row["doc_type"] == "employment" else "T")):
            rule = "NONE"
        preds.append([] if rule == "NONE" else [rule])
        if i % 25 == 0:
            print(i, "/", len(df), flush=True)
    save_predictions("llm_zeroshot_" + MODEL, df["id"], preds)


if __name__ == "__main__":
    main()
