from pathlib import Path
from typing import Protocol

import joblib

class Classifier(Protocol):
    def predict(self, text: str) -> tuple[str, float]:
        """Return (intent, confidence between 0 and 1)."""
        ...


KEYWORDS = {
    "baggage": ["bag", "luggage", "suitcase"],
    "refund": ["refund", "money back", "reimburse"],
    "booking_change": ["change", "rebook", "reschedule"],
    "flight_status": ["delay", "status", "on time", "cancelled", "gate"],
    "complaint": ["rude", "terrible", "worst", "complaint"],
}


class KeywordClassifier:
    """A deliberately naive stand-in until the real model arrives in Lab 4."""

    def predict(self, text: str) -> tuple[str, float]:
        lowered = text.lower()
        for intent, words in KEYWORDS.items():
            if any(word in lowered for word in words):
                return intent, 1.0
        return "other", 1.0
        
        
class IntentClassifier:
    def __init__(self, artifacts_dir: Path, threshold: float) -> None:
        from sentence_transformers import SentenceTransformer  # heavy import, load once

        self.encoder = SentenceTransformer(str(artifacts_dir / "encoder"), device="cpu")
        self.clf = joblib.load(artifacts_dir / "intent_clf.joblib")
        self.threshold = threshold

    def predict(self, text: str) -> tuple[str, float]:
        embedding = self.encoder.encode([text], normalize_embeddings=True)
        probs = self.clf.predict_proba(embedding)[0]
        best = int(probs.argmax())
        intent, confidence = str(self.clf.classes_[best]), float(probs[best])
        if confidence < self.threshold:
            return "other", confidence
        return intent, confidence