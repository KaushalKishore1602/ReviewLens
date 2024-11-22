import time
import os
import json
from pathlib import Path
from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse, FileResponse
from starlette.exceptions import HTTPException

from app.config import (
    STATIC_DIR, DATA_DIR, BATCH_SIZE, GEMINI_API_KEY, LLM_MODEL
)
from app.cleaner import clean_and_parse_csv
from app.cache import ReviewCache
from app.ai_service import AIService
from app.replies import generate_suggested_reply
from app.analytics import compute_dashboard_analytics

cache = ReviewCache()
ai_service = AIService()

async def serve_index(request: Request):
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse("<h1>ReviewLens Server Running</h1>")

async def download_sample_csv(request: Request):
    csv_file = DATA_DIR / "reviews.csv"
    if not csv_file.exists():
        csv_file = Path(__file__).resolve().parent.parent / "reviews.csv"
    return FileResponse(
        csv_file,
        media_type="text/csv",
        filename="reviews.csv"
    )

async def process_reviews_pipeline(csv_content: str) -> dict:
    start_time = time.time()
    
    # 1. Clean and parse CSV
    reviews, clean_stats = clean_and_parse_csv(csv_content)
    
    # 2. Query cache for existing reviews
    unique_hashes = list({r.text_hash for r in reviews if r.status == "valid"})
    cached_map = cache.get_batch(unique_hashes)
    
    cache_hits = 0
    ai_calls_made = 0
    to_analyze = []
    hash_to_reviews = {}

    for r in reviews:
        if r.status == "valid":
            hash_to_reviews.setdefault(r.text_hash, []).append(r)
            if r.text_hash in cached_map:
                r.analysis = cached_map[r.text_hash]
                r.source = "cache"
                cache_hits += 1
            else:
                to_analyze.append(r)

    # 3. Batch processing with AI Service for uncached reviews
    new_cache_items = {}
    if to_analyze:
        # Group into batches of BATCH_SIZE (default 5)
        batches = [to_analyze[i:i + BATCH_SIZE] for i in range(0, len(to_analyze), BATCH_SIZE)]
        for batch in batches:
            ai_calls_made += 1
            batch_results = await ai_service.analyze_batch(batch)
            for rev in batch:
                if rev.review_id in batch_results:
                    analysis = batch_results[rev.review_id]
                    rev.analysis = analysis
                    rev.source = "ai"
                    new_cache_items[rev.text_hash] = analysis
                else:
                    rev.status = "analysis_failed"

    # Save newly analyzed results to cache
    if new_cache_items:
        cache.set_batch(new_cache_items)

    # 4. Propagate analysis to duplicate reviews
    for r in reviews:
        if r.status == "duplicate_reused" and r.duplicate_of:
            # Find the original review's analysis
            orig = next((orig for orig in reviews if orig.review_id == r.duplicate_of), None)
            if orig and orig.analysis:
                r.analysis = orig.analysis

    # 5. Compute dashboard analytics
    analytics = compute_dashboard_analytics(reviews)
    processing_time = round(time.time() - start_time, 2)

    return {
        "status": "success",
        "cleaning_stats": clean_stats,
        "analytics": analytics,
        "cost_speed_log": {
            "ai_calls_made": ai_calls_made,
            "cache_hits": cache_hits,
            "cached_total_in_db": cache.count(),
            "processing_time_sec": processing_time,
            "batch_size": BATCH_SIZE,
            "llm_engine": "Gemini 1.5 Live" if ai_service.is_live else "ReviewLens Heuristic Engine (Offline / Safe Demo)"
        },
        "reviews": [r.to_dict() for r in reviews]
    }

async def api_upload_csv(request: Request):
    try:
        form = await request.form()
        file_field = form.get("file")
        if not file_field:
            return JSONResponse({"status": "error", "message": "No file uploaded"}, status_code=400)

        content = await file_field.read()
        csv_text = content.decode("utf-8-sig", errors="ignore")
        result = await process_reviews_pipeline(csv_text)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

async def api_load_sample(request: Request):
    try:
        csv_file = DATA_DIR / "reviews.csv"
        if not csv_file.exists():
            csv_file = Path(__file__).resolve().parent.parent / "reviews.csv"
        
        with open(csv_file, "r", encoding="utf-8") as f:
            csv_text = f.read()

        result = await process_reviews_pipeline(csv_text)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

async def api_generate_reply(request: Request):
    try:
        data = await request.json()
        review_id = data.get("review_id", "")
        product = data.get("product", "")
        review_text = data.get("review_text", "")
        summary = data.get("summary", "")

        reply = await generate_suggested_reply(
            review_id=review_id,
            product=product,
            review_text=review_text,
            summary=summary
        )
        return JSONResponse({"status": "success", "review_id": review_id, "suggested_reply": reply})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

async def api_clear_cache(request: Request):
    try:
        cache.clear()
        return JSONResponse({"status": "success", "message": "Cache successfully cleared"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

async def api_health(request: Request):
    return JSONResponse({
        "status": "healthy",
        "app": "ReviewLens",
        "version": "1.0.0",
        "ai_live": ai_service.is_live,
        "cached_reviews": cache.count()
    })
