import sqlite3
import json
from pathlib import Path
from typing import Optional, Dict, List
from app.models import ReviewAnalysis
from app.config import CACHE_DB_PATH

class ReviewCache:
    def __init__(self, db_path: Path = CACHE_DB_PATH):
        self.db_path = str(db_path)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_connection()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS review_cache (
                    text_hash TEXT PRIMARY KEY,
                    sentiment TEXT NOT NULL,
                    topics_json TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    needs_reply INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def get(self, text_hash: str) -> Optional[ReviewAnalysis]:
        if not text_hash:
            return None
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT sentiment, topics_json, summary, needs_reply FROM review_cache WHERE text_hash = ?", (text_hash,))
            row = cur.fetchone()
            if row:
                return ReviewAnalysis(
                    sentiment=row["sentiment"],
                    topics=json.loads(row["topics_json"]),
                    summary=row["summary"],
                    needs_reply=bool(row["needs_reply"])
                )
            return None
        finally:
            conn.close()

    def get_batch(self, text_hashes: List[str]) -> Dict[str, ReviewAnalysis]:
        if not text_hashes:
            return {}
        conn = self._get_connection()
        try:
            results = {}
            placeholders = ",".join("?" for _ in text_hashes)
            cur = conn.cursor()
            cur.execute(
                f"SELECT text_hash, sentiment, topics_json, summary, needs_reply FROM review_cache WHERE text_hash IN ({placeholders})",
                text_hashes
            )
            for row in cur.fetchall():
                results[row["text_hash"]] = ReviewAnalysis(
                    sentiment=row["sentiment"],
                    topics=json.loads(row["topics_json"]),
                    summary=row["summary"],
                    needs_reply=bool(row["needs_reply"])
                )
            return results
        finally:
            conn.close()

    def set(self, text_hash: str, analysis: ReviewAnalysis):
        if not text_hash or not analysis:
            return
        conn = self._get_connection()
        try:
            conn.execute("""
                INSERT OR REPLACE INTO review_cache (text_hash, sentiment, topics_json, summary, needs_reply)
                VALUES (?, ?, ?, ?, ?)
            """, (
                text_hash,
                analysis.sentiment,
                json.dumps(analysis.topics),
                analysis.summary,
                1 if analysis.needs_reply else 0
            ))
            conn.commit()
        finally:
            conn.close()

    def set_batch(self, items: Dict[str, ReviewAnalysis]):
        if not items:
            return
        conn = self._get_connection()
        try:
            for text_hash, analysis in items.items():
                conn.execute("""
                    INSERT OR REPLACE INTO review_cache (text_hash, sentiment, topics_json, summary, needs_reply)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    text_hash,
                    analysis.sentiment,
                    json.dumps(analysis.topics),
                    analysis.summary,
                    1 if analysis.needs_reply else 0
                ))
            conn.commit()
        finally:
            conn.close()

    def count(self) -> int:
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM review_cache")
            return cur.fetchone()[0]
        finally:
            conn.close()

    def clear(self):
        conn = self._get_connection()
        try:
            conn.execute("DELETE FROM review_cache")
            conn.commit()
        finally:
            conn.close()
