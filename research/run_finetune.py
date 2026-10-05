"""Fine-tune a small transformer as a clause classifier, 5-fold out-of-fold predictions.

One model per document type per fold, classes = that document type's rules + "NONE".
Plain PyTorch loop (no Trainer). Fixed hyper-parameters, no tuning on test folds.
On CPU this takes roughly 20-40 minutes; on a GPU a few minutes.

usage:  python run_finetune.py [model_name] [epochs]
examples:
  python run_finetune.py distilbert-base-uncased 15
  python run_finetune.py nlpaueb/legal-bert-base-uncased 15
"""
import sys
import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, get_linear_schedule_with_warmup
from common import load, rules_for, save_predictions, N_FOLDS

MODEL = sys.argv[1] if len(sys.argv) > 1 else "distilbert-base-uncased"
EPOCHS = int(sys.argv[2]) if len(sys.argv) > 2 else 15
LR, BATCH, MAXLEN, SEED = 3e-5, 16, 96, 42
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def train_predict(tok, train_texts, train_y, test_texts, n_classes):
    torch.manual_seed(SEED)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL, num_labels=n_classes).to(DEVICE)
    enc = tok(list(train_texts), truncation=True, padding=True, max_length=MAXLEN, return_tensors="pt")
    ds = TensorDataset(enc["input_ids"], enc["attention_mask"], torch.tensor(train_y))
    dl = DataLoader(ds, batch_size=BATCH, shuffle=True)
    opt = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=0.01)
    sched = get_linear_schedule_with_warmup(opt, int(0.1 * EPOCHS * len(dl)), EPOCHS * len(dl))
    # class-balanced loss: rules have ~5 training clauses, NONE has more
    counts = np.bincount(train_y, minlength=n_classes).astype(float)
    weights = torch.tensor(len(train_y) / (n_classes * np.maximum(counts, 1)), dtype=torch.float).to(DEVICE)
    loss_fn = torch.nn.CrossEntropyLoss(weight=weights)
    model.train()
    for _ in range(EPOCHS):
        for ids, mask, y in dl:
            opt.zero_grad()
            out = model(input_ids=ids.to(DEVICE), attention_mask=mask.to(DEVICE))
            loss_fn(out.logits, y.to(DEVICE)).backward()
            opt.step(); sched.step()
    model.eval()
    tenc = tok(list(test_texts), truncation=True, padding=True, max_length=MAXLEN, return_tensors="pt")
    with torch.no_grad():
        logits = model(input_ids=tenc["input_ids"].to(DEVICE), attention_mask=tenc["attention_mask"].to(DEVICE)).logits
    return logits.argmax(-1).cpu().numpy()


def main():
    df = load()
    tok = AutoTokenizer.from_pretrained(MODEL)
    preds = {i: [] for i in df["id"]}
    for dt in ["employment", "tenancy"]:
        classes = ["NONE"] + rules_for(df, dt)
        cidx = {c: i for i, c in enumerate(classes)}
        sub = df[df.doc_type == dt]
        y_all = sub["label_list"].apply(lambda l: cidx[l[0]] if l else 0).values
        for k in range(N_FOLDS):
            tr, te = (sub.fold != k).values, (sub.fold == k).values
            pred = train_predict(tok, sub["text"].values[tr], y_all[tr], sub["text"].values[te], len(classes))
            for cid, p in zip(sub["id"].values[te], pred):
                if p != 0:
                    preds[cid].append(classes[p])
            print(f"{dt} fold {k} done", flush=True)
    save_predictions("ft_" + MODEL.split("/")[-1], df["id"], [preds[i] for i in df["id"]])


if __name__ == "__main__":
    main()
