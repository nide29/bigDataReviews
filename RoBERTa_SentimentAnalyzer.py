from transformers import AutoTokenizer, AutoModelForSequenceClassification
from torch.nn.functional import softmax
import torch
import pandas as pd
from pyspark.sql import DataFrame as SparkDataFrame
from pyspark.sql import SparkSession
from pyspark.sql.functions import col


class RoBERTa_SentimentAnalyzer:
    def __init__(self, spark_df: SparkDataFrame):
        self.df = spark_df
        self.spark = SparkSession.builder.getOrCreate()

        # Load model and tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained("cardiffnlp/twitter-roberta-base-sentiment")
        self.model = AutoModelForSequenceClassification.from_pretrained("cardiffnlp/twitter-roberta-base-sentiment")
        self.model.eval()

        # Sentiment label mapping
        self.labels = ['negative', 'neutral', 'positive']

    def classify_sentiment(self, text: str) -> str:
        if not text or text.strip() == '':
            return 'neutral'  # Default to neutral for empty reviews

        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = softmax(outputs.logits, dim=1)
            predicted = torch.argmax(probs, dim=1).item()
        return self.labels[predicted]

    def getHotelSentiment(self, hotel_name: str) -> SparkDataFrame:
        # Filter reviews for the hotel
        filtered_df = self.df.filter(col("Hotel_Name") == hotel_name).select("Hotel_Name", "Hotel_Address",
                                                                             "Positive_Review", "Negative_Review")
        reviews_pdf = filtered_df.toPandas()

        # Concatenate positive and negative reviews into a single string
        reviews_pdf["Full_Review"] = reviews_pdf["Positive_Review"].fillna("") + ". " + reviews_pdf[
            "Negative_Review"].fillna("")

        # Classify each review
        sentiments = [self.classify_sentiment(text) for text in reviews_pdf["Full_Review"]]
        reviews_pdf["Sentiment"] = sentiments

        # Count and compute average
        total = len(sentiments)
        pos = sentiments.count("positive")
        neu = sentiments.count("neutral")
        neg = sentiments.count("negative")

        # Score encoding: pos = 1, neu = 0, neg = -1
        sentiment_score = round(((pos * 1) + (neu * 0) + (neg * -1)) / total, 3) if total > 0 else 0.0

        # Sentiment message
        if sentiment_score < -0.2:
            sentiment_text = f"Il sentiment medio dell'hotel {hotel_name} è piuttosto negativo 🥵"
        elif sentiment_score > 0.2:
            sentiment_text = f"Il sentiment medio dell'hotel {hotel_name} è piuttosto positivo 😄"
        else:
            sentiment_text = f"Il sentiment medio dell'hotel {hotel_name} è neutrale 😐"

        result = pd.DataFrame([{
            "Hotel_Name": hotel_name,
            "Hotel_Address": reviews_pdf["Hotel_Address"].iloc[0] if not reviews_pdf.empty else None,
            "Num_Reviews": total,
            "Positive_Count": pos,
            "Neutral_Count": neu,
            "Negative_Count": neg,
            "Average_Sentiment_Score": sentiment_score,
            "Sentiment": sentiment_text
        }])

        return self.spark.createDataFrame(result)
