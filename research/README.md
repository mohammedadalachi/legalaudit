# Keyword rules vs learned classifiers for Malaysian contract clauses

Part of [LegalAudit](../README.md), a university project. Author: Dalachi Mohammed Abderrahmane.

LegalAudit's README admits that keyword matching misses unusual wording. This folder measures that.

**Question.** Per clause, how well does each method find which of the 38 LegalAudit rule topics the clause is about,
and where does each one fail?

## Setup

- Data: 266 labelled clauses, see [data/DATA_CARD.md](data/DATA_CARD.md).
- Task: for each clause, predict the rule it addresses, or none.
- Evaluation: 5-fold cross-validation with fixed folds (seed 42), stratified by rule. Every method is scored by `analysis.py`
  on the same out-of-fold predictions. Micro-F1 comes with a 95% bootstrap interval over clauses.
- The keyword baselines use the real `knowledge_base.py` rules and the real `_normalise` and matcher from `inference_engine.py`.
  The two document-level special cases (E001 notice duration, E018 salary value) are not applied, since they judge a whole contract.

## Results

| method | micro P | micro R | micro F1 (95% CI) | macro F1 | recall: standard | recall: paraphrase | non-rule clauses with a false alarm |
|---|---|---|---|---|---|---|---|
| keywords (as shipped) | 0.72 | 0.50 | 0.59 (0.54-0.64) | 0.61 | 0.97 | 0.03 | 3% |
| keywords, whole-word match | 0.79 | 0.47 | 0.59 (0.54-0.65) | 0.60 | 0.94 | 0.01 | 3% |
| TF-IDF + logistic regression | 0.52 | 0.53 | 0.52 (0.46-0.59) | 0.51 | 0.58 | 0.47 | 58% |
| TF-IDF, one-vs-rest (first attempt) | 0.68 | 0.09 | 0.16 (0.10-0.23) | 0.14 | 0.11 | 0.07 | 3% |
| sentence embeddings + LR | not run yet | | | | | | |
| fine-tuned transformer | not run yet | | | | | | |
| LLM zero-shot | not run yet | | | | | | |

Full tables: `results/summary.md`, `results/per_rule.csv`.

## What the results say

1. **The keyword engine has a real bug.** It matches keywords as substrings, so short keywords fire inside longer words:
   `nda` matched "ca**lenda**r year" and raised a false Confidentiality finding on 10 clauses; `cat` matched "va**cat**es"
   and raised a false Pet Policy finding. Matching on whole words raises precision from 0.72 to 0.79 at a small cost in recall
   (it no longer catches variants like "assigned"). Suggested fix for `_find_matching_keyword`:
   ```python
   if re.search(r"\b" + kw_flexible + r"\b", text):
   ```
   Checked on both sample contracts: the output is identical before and after the change (14 and 13 findings), so the samples do not exercise this bug. The fix is applied in `inference_engine.py` on this branch.
2. **Overall F1 does not separate the methods.** The keyword intervals and the TF-IDF interval overlap. With 266 clauses
   I cannot claim a winner.
3. **The methods fail in opposite places.** Keywords recover almost every standard clause and almost no paraphrase
   (the paraphrase result is partly by construction, see limits). TF-IDF recovers 47% of paraphrases, but only 58% of standard clauses,
   and it invents a rule on 58% of clauses that match none, because its "none" class is small.
4. **Per rule it varies a lot.** TF-IDF beats keywords on E009 (salary timing, 0.80 vs 0.32), E011, E013, T004, T016, and scores 0 on
   T008, T013 and T017, where keywords are at 0.55, 0.50 and 0.71. See `results/per_rule.csv`.
5. **First attempt failed.** A one-vs-rest model with a 0.5 cutoff got recall 0.09 because each rule has about five training
   clauses. I switched to one multiclass model with a "none" class and chose its regularisation by inner cross-validation on
   training folds only. The failed run stays in the table so the choice is visible.

## Limits

- The clauses were written for this study, with AI assistance, by someone who knew the keyword lists. The near-zero keyword recall on
  paraphrases is therefore close to guaranteed. It is a stress test of a known weakness, not an estimate of how real contracts behave.
  The honest next step is a second test set of clauses taken from real public contract templates, written by nobody who has seen the keywords.
- 6 clauses per rule is very small. A single annotator labelled everything.
- Document-level checks (E001 duration, E018 salary) are out of scope here.

## To do before this is finished

1. Done: the author has read every row of `data/clauses.csv` and the data card is updated.
2. Add 100+ clauses from real public templates, tagged `style=natural`, and report them as a separate test set.
3. Ask a classmate to label a sample of 50 clauses blind, then report Cohen's kappa.
4. Run the three methods marked "not run yet" (commands below) and re-run `analysis.py`.
5. Add a short error analysis per method with 5-10 real examples.

## Reproduce

```powershell
pip install -r research/requirements-research.txt
python research/baseline_keywords.py
python research/baseline_keywords_wb.py
python research/run_tfidf.py
python research/run_embeddings.py
python research/run_embeddings.py sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
python research/run_finetune.py distilbert-base-uncased 15
python research/run_finetune.py nlpaueb/legal-bert-base-uncased 15
$env:ANTHROPIC_API_KEY="your-key"; python research/run_llm.py
python research/analysis.py
```

`run_embeddings.py`, `run_finetune.py` and `run_llm.py` were written and plumbing-checked but not run end to end, because they need model downloads.
Expect to debug small things on the first run.

## Explanations

```powershell
python research/explain.py terms employment
python research/explain.py clause employment "Pay shall be credited no later than the seventh day after the month ends."
```
