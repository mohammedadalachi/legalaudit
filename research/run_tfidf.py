"""TF-IDF + logistic regression, 5-fold out-of-fold predictions. Two variants.

tfidf_ovr         first attempt: one binary classifier per rule, fixed C=10,
                  predict a rule when probability >= 0.5. Kept in the results
                  because it failed (very low recall), which motivated the next one.
tfidf_multiclass  one multinomial model per document type with an explicit
                  "NONE" class for clauses that match no rule (all clauses in this
                  dataset have at most one label). C is chosen by 3-fold CV inside
                  each training fold only, so nothing is tuned on the test fold.
"""
import numpy as np
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from common import load, rules_for, save_predictions, N_FOLDS

THRESHOLD = 0.5
C = 10.0


def features(train_text, test_text):
    w = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, lowercase=True)
    c = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)
    Xtr = hstack([w.fit_transform(train_text), c.fit_transform(train_text)]).tocsr()
    Xte = hstack([w.transform(test_text), c.transform(test_text)]).tocsr()
    return Xtr, Xte


def multiclass():
    from sklearn.model_selection import GridSearchCV, StratifiedKFold
    df = load()
    preds = {i: [] for i in df["id"]}
    for dt in ["employment", "tenancy"]:
        sub = df[df.doc_type == dt]
        y_all = sub["label_list"].apply(lambda l: l[0] if l else "NONE")
        for k in range(N_FOLDS):
            tr, te = sub[sub.fold != k], sub[sub.fold == k]
            ytr = y_all[tr.index]
            Xtr, Xte = features(tr["text"], te["text"])
            gs = GridSearchCV(
                LogisticRegression(max_iter=5000, class_weight="balanced"),
                {"C": [1, 10, 100, 1000]},
                cv=StratifiedKFold(3, shuffle=True, random_state=0), scoring="f1_macro")
            gs.fit(Xtr, ytr)
            for cid, lab in zip(te["id"], gs.predict(Xte)):
                if lab != "NONE":
                    preds[cid].append(lab)
    save_predictions("tfidf_multiclass", df["id"], [preds[i] for i in df["id"]])


def main():
    df = load()
    preds = {i: [] for i in df["id"]}
    for dt in ["employment", "tenancy"]:
        sub = df[df.doc_type == dt]
        rules = rules_for(df, dt)
        for k in range(N_FOLDS):
            tr, te = sub[sub.fold != k], sub[sub.fold == k]
            Xtr, Xte = features(tr["text"], te["text"])
            for r in rules:
                y = tr["label_list"].apply(lambda l: int(r in l)).values
                clf = LogisticRegression(C=C, class_weight="balanced", max_iter=2000)
                clf.fit(Xtr, y)
                p = clf.predict_proba(Xte)[:, 1]
                for cid, pi in zip(te["id"], p):
                    if pi >= THRESHOLD:
                        preds[cid].append(r)
    save_predictions("tfidf_ovr", df["id"], [preds[i] for i in df["id"]])


if __name__ == "__main__":
    main()
    multiclass()
