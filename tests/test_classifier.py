from pathlib import Path

import pytest

from skydesk.api.classifier import IntentClassifier

ARTIFACTS = Path("artifacts")
needs_model = pytest.mark.skipif(
    not (ARTIFACTS / "intent_clf.joblib").exists(), reason="run training first"
)


@needs_model
@pytest.mark.parametrize(
    "text,intent",
    [
        ("My luggage is missing after landing in Madrid", "baggage"),
        ("I would like my money back please", "refund"),
        ("Can I move my trip to Sunday instead", "booking_change"),
    ],
)
def test_real_model_predicts_intent(text, intent):
    assert IntentClassifier(ARTIFACTS, threshold=0.0).predict(text)[0] == intent


@needs_model
def test_low_confidence_becomes_other():
    clf = IntentClassifier(ARTIFACTS, threshold=0.999)
    assert clf.predict("banana keyboard sunshine")[0] == "other"
