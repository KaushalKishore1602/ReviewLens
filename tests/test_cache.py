import unittest
import tempfile
import sys
import gc
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.models import ReviewAnalysis
from app.cache import ReviewCache

class TestReviewCache(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_cache.db"
        self.cache = ReviewCache(db_path=self.db_path)

    def tearDown(self):
        del self.cache
        gc.collect()
        try:
            self.temp_dir.cleanup()
        except PermissionError:
            pass

    def test_set_and_get_cache(self):
        analysis = ReviewAnalysis(
            sentiment="positive",
            topics=["quality"],
            summary="High quality materials.",
            needs_reply=False
        )
        sample_hash = "abc123hash"
        self.cache.set(sample_hash, analysis)

        cached = self.cache.get(sample_hash)
        self.assertIsNotNone(cached)
        self.assertEqual(cached.sentiment, "positive")
        self.assertEqual(cached.topics, ["quality"])
        self.assertEqual(cached.summary, "High quality materials.")
        self.assertFalse(cached.needs_reply)

    def test_cache_miss(self):
        self.assertIsNone(self.cache.get("nonexistent_hash"))

    def test_batch_cache(self):
        items = {
            "hash_1": ReviewAnalysis("positive", ["price"], "Good price", False),
            "hash_2": ReviewAnalysis("negative", ["delivery"], "Delayed delivery", True)
        }
        self.cache.set_batch(items)
        fetched = self.cache.get_batch(["hash_1", "hash_2", "hash_3"])
        self.assertIn("hash_1", fetched)
        self.assertIn("hash_2", fetched)
        self.assertNotIn("hash_3", fetched)
        self.assertEqual(self.cache.count(), 2)

if __name__ == "__main__":
    unittest.main()
