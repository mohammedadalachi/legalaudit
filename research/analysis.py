"""Score every results/*.csv identically and write results/summary.md.

Unit of evaluation is a (clause, rule) decision. Reported:
  - micro precision / recall / F1 (95% bootstrap CI over clauses)
  - macro F1 over rules
  - recall split by wording style (standard vs paraphrase)
  - false-alarm rate on clauses that address none of the 38 topics
"""
import glob, os
import numpy as np
import pandas as pd
from common import load, rules_for, RESULTS

BOOT = 1000
rng = np.random.default_rng(0)
df = load()
ALL_RULES = {dt: rules_for(df, dt) for dt in ["employment", "tenancy"]}


def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f


def counts(d):
    """Per-clause TP/FP/FN arrays."""
    tp = d.apply(lambda r: len(set(r.label_list) & set(r.pred_list)), axis=1).values
    fp = d.apply(lambda r: len(set(r.pred_list) - set(r.label_list)), axis=1).values
    fn = d.apply(lambda r: len(set(r.label_list) - set(r.pred_list)), axis=1).values
    return tp, fp, fn


def micro_ci(d):
    tp, fp, fn = counts(d)
    point = prf(tp.sum(), fp.sum(), fn.sum())
    fs = []
    n = len(d)
    for _ in range(BOOT):
        idx = rng.integers(0, n, n)
        fs.append(prf(tp[idx].sum(), fp[idx].sum(), fn[idx].sum())[2])
    return point, np.percentile(fs, [2.5, 97.5])


def macro_f1(d):
    fs = []
    for dt, rules in ALL_RULES.items():
        sub = d[d.doc_type == dt]
        for r in rules:
            tp = sum(r in a and r in b for a, b in zip(sub.label_list, sub.pred_list))
            fp = sum(r not in a and r in b for a, b in zip(sub.label_list, sub.pred_list))
            fn = sum(r in a and r not in b for a, b in zip(sub.label_list, sub.pred_list))
            fs.append(prf(tp, fp, fn)[2])
    return float(np.mean(fs))


def style_recall(d, style):
    sub = d[d["style"] == style]
    tp, fp, fn = counts(sub)
    return tp.sum() / (tp.sum() + fn.sum())


def false_alarm(d):
    sub = d[d.label_list.apply(len) == 0]
    return (sub.pred_list.apply(len) > 0).mean(), sub.pred_list.apply(len).mean()


rows, per_rule = [], []
for path in sorted(glob.glob(os.path.join(RESULTS, "*.csv"))):
    name = os.path.splitext(os.path.basename(path))[0]
    if name in ("summary", "per_rule"):
        continue
    pr = pd.read_csv(path, keep_default_na=False)
    d = df.merge(pr, on="id")
    assert len(d) == len(df), f"{name}: missing predictions"
    d["pred_list"] = d["pred"].apply(lambda s: [x for x in s.split("|") if x])
    (p, r, f), (lo, hi) = micro_ci(d)
    fa_frac, fa_mean = false_alarm(d)
    rows.append({
        "method": name, "micro_P": p, "micro_R": r, "micro_F1": f,
        "F1_CI_low": lo, "F1_CI_high": hi, "macro_F1": macro_f1(d),
        "recall_standard": style_recall(d, "standard"),
        "recall_paraphrase": style_recall(d, "paraphrase"),
        "clauses_with_false_alarm": fa_frac, "false_alarms_per_nonrule_clause": fa_mean,
    })
    for dt, rules in ALL_RULES.items():
        sub = d[d.doc_type == dt]
        for rule in rules:
            tp = sum(rule in a and rule in b for a, b in zip(sub.label_list, sub.pred_list))
            fp = sum(rule not in a and rule in b for a, b in zip(sub.label_list, sub.pred_list))
            fn = sum(rule in a and rule not in b for a, b in zip(sub.label_list, sub.pred_list))
            P, R, F = prf(tp, fp, fn)
            per_rule.append({"method": name, "rule": rule, "P": P, "R": R, "F1": F, "tp": tp, "fp": fp, "fn": fn})

S = pd.DataFrame(rows).round(3)
S.to_csv(os.path.join(RESULTS, "summary.csv"), index=False)
pd.DataFrame(per_rule).round(3).to_csv(os.path.join(RESULTS, "per_rule.csv"), index=False)

with open(os.path.join(RESULTS, "summary.md"), "w") as f:
    f.write("| method | micro P | micro R | micro F1 (95% CI) | macro F1 | recall: standard | recall: paraphrase | non-rule clauses with a false alarm |\n")
    f.write("|---|---|---|---|---|---|---|---|\n")
    for r in S.itertuples():
        f.write(f"| {r.method} | {r.micro_P:.2f} | {r.micro_R:.2f} | {r.micro_F1:.2f} ({r.F1_CI_low:.2f}-{r.F1_CI_high:.2f}) "
                f"| {r.macro_F1:.2f} | {r.recall_standard:.2f} | {r.recall_paraphrase:.2f} | {r.clauses_with_false_alarm:.0%} |\n")
print(open(os.path.join(RESULTS, "summary.md")).read())
