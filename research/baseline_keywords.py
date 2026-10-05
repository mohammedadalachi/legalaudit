"""Baseline: the existing LegalAudit keyword engine, applied clause by clause.

Uses the real RULES and the real _normalise / _find_matching_keyword from the
parent project, so this measures the engine as shipped. A rule 'fires' on a clause
if any of its keywords matches that clause. The two document-level special cases
(E001 notice-period validation, E018 salary extraction) are not applied because
they judge a whole document, not one clause; this is a stated limitation.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import knowledge_base as kb
import inference_engine as ie
from common import load, save_predictions

df = load()
preds = []
for _, row in df.iterrows():
    text = ie._normalise(row["text"])
    fired = [r["id"] for r in kb.RULES
             if r["doc_type"] == row["doc_type"]
             and ie._find_matching_keyword(r["keywords"], text) is not None]
    preds.append(fired)
save_predictions("keywords", df["id"], preds)
