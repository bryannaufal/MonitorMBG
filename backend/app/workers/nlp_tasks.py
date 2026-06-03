"""NLP processing Celery tasks — sentiment, clustering, anomaly detection."""

from app.workers.celery_app import celery_app


@celery_app.task(name="nlp.analyze_sentiment", bind=True)
def analyze_sentiment(self, complaint_id: int, text: str):
    """
    Run sentiment analysis on a complaint.

    Uses IndoBERTweet for Indonesian text classification.
    """
    from app.services.nlp_engine.sentiment import sentiment_analyzer
    from app.services.nlp_engine.text_preprocessor import TextPreprocessor

    # Preprocess text
    clean_text = TextPreprocessor.clean(text)

    # Run sentiment analysis
    result = sentiment_analyzer.predict(clean_text)

    # TODO: Update complaint in database with sentiment results
    return {
        "complaint_id": complaint_id,
        "sentiment": result["label"],
        "score": result["score"],
    }


@celery_app.task(name="nlp.analyze_sentiment_batch")
def analyze_sentiment_batch(complaints: list[dict]):
    """Run sentiment analysis on a batch of complaints."""
    from app.services.nlp_engine.sentiment import sentiment_analyzer
    from app.services.nlp_engine.text_preprocessor import TextPreprocessor

    texts = [TextPreprocessor.clean(c["text"]) for c in complaints]
    results = sentiment_analyzer.predict_batch(texts)

    return [
        {"complaint_id": c["id"], **r}
        for c, r in zip(complaints, results)
    ]


@celery_app.task(name="nlp.cluster_topics")
def cluster_topics(texts: list[str]):
    """
    Run BERTopic clustering on a batch of complaint texts.
    """
    from app.services.nlp_engine.topic_clustering import topic_clusterer
    from app.services.nlp_engine.text_preprocessor import TextPreprocessor

    clean_texts = TextPreprocessor.clean_batch(texts)
    topic_ids, topic_info = topic_clusterer.fit_transform(clean_texts)

    return {"topic_ids": topic_ids, "num_topics": len(set(topic_ids))}


@celery_app.task(name="nlp.detect_anomalies")
def detect_anomalies(timestamps: list[str], values: list[float]):
    """
    Detect anomalous spikes in complaint time-series data.
    """
    from datetime import datetime
    from app.services.nlp_engine.anomaly_detection import anomaly_detector

    dt_timestamps = [datetime.fromisoformat(ts) for ts in timestamps]
    anomalies = anomaly_detector.detect_spikes(dt_timestamps, values)

    return {"anomalies": anomalies, "count": len(anomalies)}
