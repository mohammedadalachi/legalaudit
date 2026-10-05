"""Sentence embeddings + logistic regression, 5-fold out-of-fold predictions.

Frozen encoder (no fine-tuning), multinomial classifier with a "NONE" class, C chosen
by inner 3-fold CV on training folds only. Same folds as every other method.

usage:  python run_embeddings.py [model_name]
default model: sentence-transformers/all-MiniLM-L6-v2
multilingual option (useful for Malay text): sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
"""
import sys
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from common import load, save_predictions, N_FOLDS

MODEL = sys.argv[1] if len(sys.argv) > 1 else "sentence-transformers/all-MiniLM-L6-v2"


def embed(texts):
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(MODEL)
    return model.encode(list(texts), normalize_embeddings=True, show_progress_bar=False)


def run(embed_fn=embed, name=None):
    df = load()
    E = embed_fn(df["text"])
    preds = {i: [] for i in df["id"]}
    for dt in ["employment", "tenancy"]:
        idx = np.where(df.doc_type.values == dt)[0]
        sub = df.iloc[idx]
        y_all = sub["label_list"].apply(lambda l: l[0] if l else "NONE").values
        folds = sub["fold"].values
        ids = sub["id"].values
        X = E[idx]
        for k in range(N_FOLDS):
            tr, te = folds != k, folds == k
            gs = GridSearchCV(
                LogisticRegression(max_iter=5000, class_weight="balanced"),
                {"C": [0.1, 1, 10, 100]},
                cv=StratifiedKFold(3, shuffle=True, random_state=0), scoring="f1_macro")
            gs.fit(X[tr], y_all[tr])
            for cid, lab in zip(ids[te], gs.predict(X[te])):
                if lab != "NONE":
                    preds[cid].append(lab)
    name = name or "emb_" + MODEL.split("/")[-1]
    save_predictions(name, df["id"], [preds[i] for i in df["id"]])


if __name__ == "__main__":
    run()
