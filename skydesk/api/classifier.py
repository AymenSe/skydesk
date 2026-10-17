from typing import Protocol


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
        
        
