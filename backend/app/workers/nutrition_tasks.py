"""Nutrition estimation Celery tasks — food detection + calorie calculation."""

from app.workers.celery_app import celery_app


@celery_app.task(name="nutrition.analyze_nutrition", bind=True)
def analyze_nutrition(self, report_id: int, image_paths: list[str]):
    """
    Full nutrition estimation pipeline for daily report photos.

    Steps:
    1. Detect food items using object detection (YOLO)
    2. Estimate portion sizes from bounding boxes
    3. Calculate calories and macronutrients
    """
    from app.services.cv_engine.object_detection import food_detector
    from app.services.cv_engine.portion_estimator import portion_estimator
    from app.services.cv_engine.nutrition_calculator import nutrition_calculator

    all_results = []

    for path in image_paths:
        # Step 1: Detect food items
        detections = food_detector.detect(path)

        if not detections:
            all_results.append({
                "image_path": path,
                "detected_items": [],
                "nutrition": {"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0},
            })
            continue

        # Step 2: Estimate portions
        portions = portion_estimator.estimate_plate(detections)

        # Step 3: Calculate nutrition
        plate_nutrition = nutrition_calculator.calculate_plate(portions)

        all_results.append({
            "image_path": path,
            "detected_items": portions,
            "nutrition": plate_nutrition,
        })

    # TODO: Store nutrition results in the database
    # TODO: Dispatch scoring task
    from app.workers.scoring_tasks import compute_scores
    compute_scores.delay(report_id, "daily")

    return {
        "report_id": report_id,
        "images_analyzed": len(image_paths),
        "results": all_results,
    }
