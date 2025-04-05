# backend/app/utils/helpers.py
# Add helper functions as you go.

def map_sentiment_label(label: str) -> str:
    """Maps the sentiment label from the model to a consistent format."""
    if label == "LABEL_0":
        return "negative"
    elif label == "LABEL_1":
        return "neutral"
    elif label == "LABEL_2":
        return "positive"
    return "unknown"