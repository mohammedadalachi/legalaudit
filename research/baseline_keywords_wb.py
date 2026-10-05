"""Stronger baseline: the same keyword lists, but matched on whole words.

The shipped engine uses re.search(keyword, text) with no word boundaries, so short
keywords match inside longer words ('nda' in 'calendar', 'cat' in 'vacates').
This variant wraps each keyword in \\b...\\b and changes nothing else. It exists so
the learned models are compared against the best the keyword approach can do, not
against a version with a known bug.
"""
import os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import knowledge_base as kb
import inference_engine as ie
from common import load, save_predictions


def matches(keywords, text):
    for kw in keywords:
        pat = ie._normalise(kw).replace("-", "[- ]?")
        if re.search(r"\b" + pat + r"\b", text):
            return True
    return False


df = load()
preds = []
for _, row in df.iterrows():
    text = ie._normalise(row["text"])
    preds.append([r["id"] for r in kb.RULES
                  if r["doc_type"] == row["doc_type"] and matches(r["keywords"], text)])
save_predictions("keywords_wordboundary", df["id"], preds)
