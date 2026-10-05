"""Shared data loading, fixed CV folds and prediction I/O for all methods.

Every method writes out-of-fold predictions to results/<method>.csv with columns
id, pred (pipe-separated rule IDs, empty = no rule). analysis.py scores them all
the same way, so methods are compared on identical clauses and identical folds.
"""
import os
import pandas as pd
from sklearn.model_selection import StratifiedKFold

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "clauses.csv")
RESULTS = os.path.join(HERE, "results")
SEED = 42
N_FOLDS = 5


def load():
    df = pd.read_csv(DATA, keep_default_na=False)
    df["label_list"] = df["labels"].apply(lambda s: [x for x in s.split("|") if x])
    # stratify folds on (doc_type, primary label); clauses with no rule get "NONE"
    strat = df["doc_type"] + "_" + df["label_list"].apply(lambda l: l[0] if l else "NONE")
    df["fold"] = -1
    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
    for k, (_, test_idx) in enumerate(skf.split(df, strat)):
        df.loc[df.index[test_idx], "fold"] = k
    return df


def rules_for(df, doc_type):
    """Sorted list of rule IDs that exist for a document type."""
    return sorted({l for ls in df[df.doc_type == doc_type]["label_list"] for l in ls})


def save_predictions(name, ids, preds):
    os.makedirs(RESULTS, exist_ok=True)
    out = pd.DataFrame({"id": ids, "pred": ["|".join(sorted(p)) for p in preds]})
    out.to_csv(os.path.join(RESULTS, f"{name}.csv"), index=False)
    print(f"saved results/{name}.csv ({len(out)} clauses)")
