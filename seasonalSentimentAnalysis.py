from pyspark.sql.functions import col, udf, to_date, count, avg, first
from pyspark.sql.types import StringType, FloatType
from pyspark.sql.functions import round as spark_round
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk

# Assicurati che il lexicon sia disponibile
nltk.download('vader_lexicon')


class SeasonalSentimentAnalysis:

    def __init__(self, df):
        """
        Inizializza il dataset e aggiunge colonne per data, stagione e sentiment score.
        """
        self.df = df.withColumn("Review_Date", to_date(col("Review_Date"), "yyyy-MM-dd"))
        self.df = self.df.withColumn("Season", self._season_udf()(col("Review_Date")))

        # Calcolo del punteggio di sentiment usando VADER
        self.df = self.df.withColumn(
            "Sentiment_Score",
            self._sentiment_score_udf()(col("Positive_Review"), col("Negative_Review"))
        )

    def _season_udf(self):
        """
        Restituisce una UDF per estrarre la stagione da una data.
        """
        def get_season(date):
            if not date:
                return "Unknown"
            month = date.month
            if month in [12, 1, 2]:
                return "Winter"
            elif month in [3, 4, 5]:
                return "Spring"
            elif month in [6, 7, 8]:
                return "Summer"
            elif month in [9, 10, 11]:
                return "Autumn"
            else:
                return "Unknown"
        return udf(get_season, StringType())

    def _sentiment_score_udf(self):
        """
        UDF per calcolare il punteggio di sentiment combinando recensioni positive e negative.
        """
        sia = SentimentIntensityAnalyzer()

        def score_sentiment(pos, neg):
            text = f"{pos}. {neg}"
            score = sia.polarity_scores(text)
            return score["compound"]  # Valore tra -1 (negativo) e +1 (positivo)

        return udf(score_sentiment, FloatType())

    def getAverageSentimentBySeason(self):
        """
        Restituisce il punteggio medio di sentiment per stagione.
        """
        return self.df.groupBy("Season").avg("Sentiment_Score").orderBy("Season")

    def getAverageSentimentBySeasonForHotel(self, hotel_name):
        """
        Restituisce le statistiche stagionali (sentiment, review score, numero recensioni)
        per uno specifico hotel.
        """
        filtered_df = self.df.filter(col("Hotel_Name") == hotel_name)

        result = filtered_df.groupBy("Season").agg(
            first("Hotel_Name").alias("Hotel_Name"),
            first("Hotel_Address").alias("Hotel_Address"),  # alternativamente possiamo prendere la nazione con 'Hotel_Nationality'
            spark_round(avg("Sentiment_Score"), 4).alias("Avg_Sentiment_Score"),
            spark_round(avg("Reviewer_Score"), 4).alias("Avg_Review_Score"),
            count("*").alias("Num_Reviews")
        ).orderBy("Season")

        return result

    def getAverageSentimentBySeasonForNation(self, nation):
        """
        Restituisce il sentiment medio per stagione per una specifica nazione dell'hotel.
        """
        filtered_df = self.df.filter(col("Hotel_Nationality") == nation)
        return filtered_df.groupBy("Season") \
            .agg(avg("Sentiment_Score").alias("Avg_Sentiment_Score")) \
            .orderBy("Season")

    def getAverageSentimentByNation(self):
        """
        Restituisce il sentiment medio annuale per ogni nazione.
        """
        df = self.df
        # Calcola il sentiment medio per ogni nazione sull'intero dataset
        return df.groupBy("Hotel_Nationality").agg(
            spark_round(avg("Sentiment_Score"), 3).alias("mean_sentiment")
        ).withColumnRenamed("Hotel_Nationality", "nation")
