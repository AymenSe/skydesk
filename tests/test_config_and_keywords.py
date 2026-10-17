from skydesk.api.classifier import KeywordClassifier
from skydesk.core.config import Settings


def test_password_comes_from_file(tmp_path):
    secret = tmp_path / "pw.txt"
    secret.write_text("s3cret\n")
    settings = Settings(database_url=None, db_password_file=secret, db_host="postgres")
    assert settings.sqlalchemy_url == "postgresql+psycopg://skydesk:s3cret@postgres:5432/skydesk"


def test_keyword_classifier():
    clf = KeywordClassifier()
    assert clf.predict("My SUITCASE is missing") == ("baggage", 1.0)
    assert clf.predict("Do you serve vegan meals?") == ("other", 1.0)
