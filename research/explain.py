"""Explanations for the TF-IDF classifier, so it stays an explainable system.

1. top_terms():  the words and word pairs that push a clause towards each rule
                 (largest positive weights of the linear model).
2. occlusion():  for one clause, delete each word in turn and measure how much the
                 predicted rule's probability drops. Words with a big drop are the
                 evidence for the prediction. Works for any model that returns
                 probabilities, so the same function can wrap a transformer later.

usage:
  python explain.py terms employment
  python explain.py clause employment "Pay shall be credited no later than the seventh day after the month ends."
"""
import sys
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from common import load


def fit(doc_type, C=100.0):
    df = load()
    sub = df[df.doc_type == doc_type]
    y = sub["label_list"].apply(lambda l: l[0] if l else "NONE")
    vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
    X = vec.fit_transform(sub["text"])
    clf = LogisticRegression(C=C, max_iter=5000, class_weight="balanced").fit(X, y)
    return vec, clf


def top_terms(doc_type, n=6):
    vec, clf = fit(doc_type)
    names = np.array(vec.get_feature_names_out())
    for cls, w in zip(clf.classes_, clf.coef_):
        if cls == "NONE":
            continue
        print(f"{cls}: " + ", ".join(names[np.argsort(w)[::-1][:n]]))


def occlusion(doc_type, clause, top=5):
    vec, clf = fit(doc_type)
    proba = lambda t: clf.predict_proba(vec.transform([t]))[0]
    base = proba(clause)
    k = int(base.argmax())
    pred = clf.classes_[k]
    words = clause.split()
    drops = []
    for i, w in enumerate(words):
        reduced = " ".join(words[:i] + words[i + 1:])
        drops.append((base[k] - proba(reduced)[k], w))
    drops.sort(reverse=True)
    print(f"predicted: {pred} (p={base[k]:.2f})")
    print("evidence words:", ", ".join(f"{w} (-{d:.3f})" for d, w in drops[:top]))


if __name__ == "__main__":
    cmd, dt = sys.argv[1], sys.argv[2]
    top_terms(dt) if cmd == "terms" else occlusion(dt, sys.argv[3])
