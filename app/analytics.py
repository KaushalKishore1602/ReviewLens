from typing import List, Dict, Any
from collections import Counter
from app.models import ProcessedReview
from app.cleaner import evaluate_rating_mismatch

def compute_dashboard_analytics(reviews: List[ProcessedReview]) -> Dict[str, Any]:
    """
    Computes summary cards, top 3 complaints, top 3 praises,
    rating mismatches, and per-product breakdown.
    """
    valid_analysed = [r for r in reviews if r.analysis is not None and r.status != "empty_skipped"]
    total_analysed = len(valid_analysed)

    sentiment_counts = Counter([r.analysis.sentiment for r in valid_analysed])
    pos_count = sentiment_counts.get("positive", 0)
    neu_count = sentiment_counts.get("neutral", 0)
    neg_count = sentiment_counts.get("negative", 0)

    pos_pct = round((pos_count / total_analysed * 100), 1) if total_analysed > 0 else 0
    neu_pct = round((neu_count / total_analysed * 100), 1) if total_analysed > 0 else 0
    neg_pct = round((neg_count / total_analysed * 100), 1) if total_analysed > 0 else 0

    needs_reply_count = sum(1 for r in valid_analysed if r.analysis.needs_reply)

    # Top complaints & praises by topic frequency and representative summaries
    complaint_topics: Counter = Counter()
    praise_topics: Counter = Counter()
    complaint_samples: Dict[str, List[str]] = {}
    praise_samples: Dict[str, List[str]] = {}

    for r in valid_analysed:
        for t in r.analysis.topics:
            if r.analysis.sentiment == "negative":
                complaint_topics[t] += 1
                complaint_samples.setdefault(t, []).append(r.analysis.summary)
            elif r.analysis.sentiment == "positive":
                praise_topics[t] += 1
                praise_samples.setdefault(t, []).append(r.analysis.summary)

    top_3_complaints = []
    for topic, count in complaint_topics.most_common(3):
        samples = complaint_samples.get(topic, [])
        sample_text = samples[0] if samples else f"Issues related to {topic}"
        top_3_complaints.append({
            "topic": topic.replace("_", " ").title(),
            "count": count,
            "sample": sample_text
        })

    top_3_praises = []
    for topic, count in praise_topics.most_common(3):
        samples = praise_samples.get(topic, [])
        sample_text = samples[0] if samples else f"High praise for {topic}"
        top_3_praises.append({
            "topic": topic.replace("_", " ").title(),
            "count": count,
            "sample": sample_text
        })

    # Rating Mismatches Check
    mismatches = []
    rated_count = 0
    agreement_count = 0

    for r in valid_analysed:
        if r.rating is not None:
            rated_count += 1
            is_mismatch, reason = evaluate_rating_mismatch(r.rating, r.analysis.sentiment)
            r.is_rating_mismatch = is_mismatch
            r.mismatch_reason = reason
            if is_mismatch:
                mismatches.append(r.review_id)
            else:
                agreement_count += 1

    agreement_pct = round((agreement_count / rated_count * 100), 1) if rated_count > 0 else 100.0

    # Per-product View Breakdown
    product_map: Dict[str, List[ProcessedReview]] = {}
    for r in reviews:
        product_map.setdefault(r.product, []).append(r)

    product_views = []
    for prod_name, prod_reviews in product_map.items():
        prod_analysed = [r for r in prod_reviews if r.analysis is not None]
        prod_ratings = [r.rating for r in prod_reviews if r.rating is not None]
        avg_rating = round(sum(prod_ratings) / len(prod_ratings), 1) if prod_ratings else None

        prod_sentiments = Counter([r.analysis.sentiment for r in prod_analysed])
        prod_complaints = Counter([t for r in prod_analysed if r.analysis.sentiment == "negative" for t in r.analysis.topics])
        prod_praises = Counter([t for r in prod_analysed if r.analysis.sentiment == "positive" for t in r.analysis.topics])

        product_views.append({
            "product": prod_name,
            "total_reviews": len(prod_reviews),
            "analysed_count": len(prod_analysed),
            "avg_rating": avg_rating,
            "positive_count": prod_sentiments.get("positive", 0),
            "neutral_count": prod_sentiments.get("neutral", 0),
            "negative_count": prod_sentiments.get("negative", 0),
            "top_issues": [t.replace("_", " ").title() for t, _ in prod_complaints.most_common(2)],
            "top_praises": [t.replace("_", " ").title() for t, _ in prod_praises.most_common(2)],
        })

    return {
        "total_analysed": total_analysed,
        "positive_count": pos_count,
        "positive_pct": pos_pct,
        "neutral_count": neu_count,
        "neutral_pct": neu_pct,
        "negative_count": neg_count,
        "negative_pct": neg_pct,
        "needs_reply_count": needs_reply_count,
        "top_3_complaints": top_3_complaints,
        "top_3_praises": top_3_praises,
        "rating_mismatches_count": len(mismatches),
        "rating_mismatches_ids": mismatches,
        "rating_agreement_pct": agreement_pct,
        "product_views": product_views
    }
