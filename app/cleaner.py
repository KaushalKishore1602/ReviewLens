import csv
import io
import hashlib
import re
from typing import List, Tuple, Dict, Any, Optional
from app.models import ProcessedReview

def compute_text_hash(text: str) -> str:
    """Normalize text and return SHA-256 hash for deduplication and caching."""
    normalized = " ".join(text.strip().lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

def parse_rating(raw_val: Any) -> Optional[int]:
    """
    Parse star rating:
    Returns int (1-5) if valid numeric rating.
    Returns None if missing (empty string) or invalid (e.g. 'five', text, out-of-range).
    """
    if raw_val is None:
        return None
    val_str = str(raw_val).strip()
    if not val_str:
        return None
    
    try:
        num = int(float(val_str))
        if 1 <= num <= 5:
            return num
        return None
    except (ValueError, TypeError):
        return None

def clean_and_parse_csv(csv_content: str) -> Tuple[List[ProcessedReview], Dict[str, Any]]:
    """
    Parses CSV content and applies all cleaning rules:
    - Skips or flags empty reviews
    - Treats missing or non-integer ratings as unknown (None)
    - Detects duplicate reviews (same text hash)
    Returns list of ProcessedReview objects and cleaning statistics.
    """
    reader = csv.DictReader(io.StringIO(csv_content.strip()))
    
    # Handle possible BOM or varied column names
    field_map = {}
    if reader.fieldnames:
        for f in reader.fieldnames:
            clean_f = f.strip().lower().replace('"', '').replace("'", "")
            field_map[clean_f] = f

    id_col = field_map.get("review_id", "review_id")
    prod_col = field_map.get("product", "product")
    rating_col = field_map.get("rating", "rating")
    date_col = field_map.get("date", "date")
    text_col = field_map.get("review_text", "review_text")

    reviews: List[ProcessedReview] = []
    seen_hashes: Dict[str, str] = {} # hash -> review_id

    total_rows = 0
    empty_skipped = 0
    duplicates_count = 0
    unknown_ratings_count = 0
    valid_count = 0

    for idx, row in enumerate(reader, start=1):
        total_rows += 1
        review_id = (row.get(id_col) or f"R{idx:03d}").strip()
        product = (row.get(prod_col) or "General").strip()
        raw_rating = (row.get(rating_col) or "").strip()
        date_val = (row.get(date_col) or "").strip()
        raw_text = (row.get(text_col) or "").strip()

        # Parse rating
        rating = parse_rating(raw_rating)
        if rating is None:
            unknown_ratings_count += 1

        # Check for empty review text
        if not raw_text:
            empty_skipped += 1
            rev = ProcessedReview(
                review_id=review_id,
                product=product,
                rating=rating,
                raw_rating=raw_rating or "unknown",
                date=date_val,
                review_text="",
                text_hash="",
                status="empty_skipped",
                source="skipped"
            )
            reviews.append(rev)
            continue

        text_hash = compute_text_hash(raw_text)

        # Check for duplicate review text
        if text_hash in seen_hashes:
            duplicates_count += 1
            first_id = seen_hashes[text_hash]
            rev = ProcessedReview(
                review_id=review_id,
                product=product,
                rating=rating,
                raw_rating=raw_rating or ("unknown" if rating is None else str(rating)),
                date=date_val,
                review_text=raw_text,
                text_hash=text_hash,
                status="duplicate_reused",
                duplicate_of=first_id,
                source="duplicate"
            )
            reviews.append(rev)
            continue

        # Valid new review
        seen_hashes[text_hash] = review_id
        valid_count += 1
        rev = ProcessedReview(
            review_id=review_id,
            product=product,
            rating=rating,
            raw_rating=raw_rating or ("unknown" if rating is None else str(rating)),
            date=date_val,
            review_text=raw_text,
            text_hash=text_hash,
            status="valid",
            source="ai"
        )
        reviews.append(rev)

    stats = {
        "total_rows": total_rows,
        "valid_reviews": valid_count,
        "empty_skipped": empty_skipped,
        "duplicates_reused": duplicates_count,
        "unknown_ratings": unknown_ratings_count,
    }

    return reviews, stats

def evaluate_rating_mismatch(rating: Optional[int], sentiment: str) -> Tuple[bool, Optional[str]]:
    """
    Flags reviews where star rating contradicts the AI sentiment.
    Example: 5 stars with negative sentiment (R008), or 1/2 stars with positive sentiment.
    """
    if rating is None:
        return False, None

    if rating >= 4 and sentiment == "negative":
        return True, f"High rating ({rating}★) contradicts negative sentiment"
    elif rating <= 2 and sentiment == "positive":
        return True, f"Low rating ({rating}★) contradicts positive sentiment"
    
    return False, None
