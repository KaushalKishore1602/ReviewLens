import unittest
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.models import ReviewAnalysis, ALLOWED_SENTIMENTS, ALLOWED_TOPICS

class TestSchemaValidation(unittest.TestCase):
    def test_valid_schema(self):
        valid_data = {
            "sentiment": "positive",
            "topics": ["quality", "price"],
            "summary": "Great bedsheet with soft cotton fabric.",
            "needs_reply": False
        }
        analysis = ReviewAnalysis.validate_and_create(valid_data)
        self.assertEqual(analysis.sentiment, "positive")
        self.assertEqual(analysis.topics, ["quality", "price"])
        self.assertEqual(analysis.summary, "Great bedsheet with soft cotton fabric.")
        self.assertFalse(analysis.needs_reply)

    def test_invalid_sentiment_rejected(self):
        invalid_data = {
            "sentiment": "ecstatic",
            "topics": ["quality"],
            "summary": "Best ever",
            "needs_reply": False
        }
        with self.assertRaises(ValueError) as ctx:
            ReviewAnalysis.validate_and_create(invalid_data)
        self.assertIn("Invalid sentiment", str(ctx.exception))

    def test_invalid_topic_rejected(self):
        invalid_data = {
            "sentiment": "negative",
            "topics": ["space_travel", "quality"],
            "summary": "Terrible fit",
            "needs_reply": True
        }
        with self.assertRaises(ValueError) as ctx:
            ReviewAnalysis.validate_and_create(invalid_data)
        self.assertIn("Topic 'space_travel' outside allowed list", str(ctx.exception))

    def test_empty_summary_rejected(self):
        invalid_data = {
            "sentiment": "neutral",
            "topics": ["quality"],
            "summary": "   ",
            "needs_reply": False
        }
        with self.assertRaises(ValueError) as ctx:
            ReviewAnalysis.validate_and_create(invalid_data)
        self.assertIn("Summary must be a non-empty string", str(ctx.exception))

    def test_needs_reply_coercion_and_validation(self):
        data_str_bool = {
            "sentiment": "negative",
            "topics": ["support"],
            "summary": "Customer support never replied.",
            "needs_reply": "true"
        }
        analysis = ReviewAnalysis.validate_and_create(data_str_bool)
        self.assertTrue(analysis.needs_reply)

if __name__ == "__main__":
    unittest.main()
