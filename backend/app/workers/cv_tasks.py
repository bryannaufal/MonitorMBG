"""Computer vision Celery tasks — image verification pipeline."""

from app.workers.celery_app import celery_app


@celery_app.task(name="cv.process_daily_report_images", bind=True)
def process_daily_report_images(self, report_id: int, image_paths: list[str]):
    """
    Full CV verification pipeline for daily report photos.

    Steps:
    1. Compute perceptual hashes → check for duplicates
    2. Run image-text similarity matching
    3. Dispatch nutrition analysis (separate task)
    """
    from app.services.cv_engine.image_hashing import image_hasher
    from app.services.cv_engine.image_text_matching import image_text_matcher

    results = []

    for path in image_paths:
        # Step 1: Perceptual hashing
        phash = image_hasher.compute_phash(path)

        # TODO: Query existing hashes from DB for duplicate detection
        # duplicates = image_hasher.find_duplicates(phash, existing_hashes)

        # Step 2: Image-text matching
        # TODO: Get menu_description from the daily report
        # similarity = image_text_matcher.compute_similarity(path, menu_description)

        results.append({
            "image_path": path,
            "phash": phash,
            "duplicates": [],
            "similarity": 0.0,
        })

    # Step 3: Dispatch nutrition pipeline
    from app.workers.nutrition_tasks import analyze_nutrition
    analyze_nutrition.delay(report_id, image_paths)

    return {
        "report_id": report_id,
        "images_processed": len(image_paths),
        "results": results,
    }


@celery_app.task(name="cv.process_ocr")
def process_ocr(report_id: int, document_path: str):
    """
    Extract text from a document image using OCR.
    """
    from app.services.cv_engine.ocr_parser import ocr_parser

    result = ocr_parser.extract_structured(document_path)

    # TODO: Update the report with OCR results in the database
    return {
        "report_id": report_id,
        "extracted_text": result["raw_text"],
        "structured_data": result,
    }
