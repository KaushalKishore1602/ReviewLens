from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any

ALLOWED_SENTIMENTS = {"positive", "neutral", "negative"}
ALLOWED_TOPICS = {"quality", "delivery", "price", "packaging", "support", "size_fit", "other"}

@dataclass
class ReviewAnalysis:
    sentiment: str
    topics: List[str]
    summary: str
    needs_reply: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def validate_and_create(cls, data: Dict[str, Any]) -> "ReviewAnalysis":
        """
        Validates the dictionary against the strict schema.
        Raises ValueError if invalid.
        """
        if not isinstance(data, dict):
            raise ValueError("Analysis result is not a JSON object")

        sentiment = data.get("sentiment")
        if not isinstance(sentiment, str) or sentiment.lower() not in ALLOWED_SENTIMENTS:
            raise ValueError(f"Invalid sentiment '{sentiment}'. Allowed: {ALLOWED_SENTIMENTS}")
        sentiment = sentiment.lower()

        topics = data.get("topics")
        if not isinstance(topics, list) or len(topics) == 0:
            raise ValueError("Topics must be a non-empty list")
        
        cleaned_topics = []
        for t in topics:
            if not isinstance(t, str):
                raise ValueError(f"Invalid topic format: {t}")
            t_clean = t.strip().lower()
            if t_clean not in ALLOWED_TOPICS:
                raise ValueError(f"Topic '{t_clean}' outside allowed list: {ALLOWED_TOPICS}")
            if t_clean not in cleaned_topics:
                cleaned_topics.append(t_clean)

        summary = data.get("summary")
        if not isinstance(summary, str) or not summary.strip():
            raise ValueError("Summary must be a non-empty string")
        summary = summary.strip().replace("\n", " ")

        needs_reply = data.get("needs_reply")
        if not isinstance(needs_reply, bool):
            if isinstance(needs_reply, str):
                if needs_reply.lower() in ("true", "1", "yes"):
                    needs_reply = True
                elif needs_reply.lower() in ("false", "0", "no"):
                    needs_reply = False
                else:
                    raise ValueError(f"needs_reply must be a boolean, got {needs_reply}")
            else:
                raise ValueError(f"needs_reply must be a boolean, got {type(needs_reply)}")

        return cls(
            sentiment=sentiment,
            topics=cleaned_topics,
            summary=summary,
            needs_reply=needs_reply
        )

@dataclass
class ProcessedReview:
    review_id: str
    product: str
    rating: Optional[int]
    raw_rating: str
    date: str
    review_text: str
    text_hash: str
    status: str = "valid"  # 'valid', 'empty_skipped', 'duplicate_reused', 'analysis_failed'
    duplicate_of: Optional[str] = None
    is_rating_mismatch: bool = False
    mismatch_reason: Optional[str] = None
    analysis: Optional[ReviewAnalysis] = None
    suggested_reply: Optional[str] = None
    source: str = "ai"  # 'ai', 'cache', 'skipped', 'duplicate'

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        if self.analysis:
            res["analysis"] = self.analysis.to_dict()
        return res
