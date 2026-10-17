"""Train the intent classifier: MiniLM sentence embeddings + logistic regression."""
import csv
from pathlib import Path

import joblib
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score

DATA = Path("data/intents.csv")
OUT = Path("artifacts")
ENCODER_ID = "sentence-transformers/all-MiniLM-L6-v2"
MIN_ACCURACY = 0.75


def load_data(path: Path) -> tuple[list[str], list[str]]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return [r["text"] for r in rows], [r["intent"] for r in rows]


def main() -> None:
    texts, labels = load_data(DATA)
    encoder = SentenceTransformer(ENCODER_ID, device="cpu")
    X = encoder.encode(texts, normalize_embeddings=True)

    clf = LogisticRegression(C=10.0, max_iter=1000)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(clf, X, labels, cv=cv)
    print(f"cross-validated accuracy: {scores.mean():.3f} (+/- {scores.std():.3f})")

    if scores.mean() < MIN_ACCURACY:
        raise SystemExit(f"accuracy below {MIN_ACCURACY}: add more training examples")

    clf.fit(X, labels)
    OUT.mkdir(exist_ok=True)
    encoder.save(str(OUT / "encoder"))
    joblib.dump(clf, OUT / "intent_clf.joblib")
    print(f"saved encoder and classifier to {OUT}/")


if __name__ == "__main__":
    main()