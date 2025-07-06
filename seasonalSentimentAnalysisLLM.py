from pyspark.sql.functions import col, to_date, udf, count, avg, first
from pyspark.sql.types import StringType
import ollama
import pandas as pd


class SeasonalSentimentAnalysisLLM:
    def __init__(self, df):
        self.df = df.withColumn("Review_Date", to_date(col("Review_Date"), "yyyy-MM-dd"))
        self.df = self.df.withColumn("Season", self._season_udf()(col("Review_Date")))

    def _season_udf(self):
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

    def _get_sentiment_from_llm(self, text):
        try:
            response = ollama.chat(model='deepseek-r1:1.5b', messages=[
                {
                    'role': 'user',
                    'content': f"Classify the overall sentiment of this hotel review (positive, neutral, or negative):\n{text}",
                },
            ])
            output = response['message']['content'].strip().lower()
            if "positive" in output:
                return 1
            elif "neutral" in output:
                return 0
            elif "negative" in output:
                return -1
            else:
                return 0
        except:
            return 0

    def getSeasonalStatsForHotel(self, hotel_name, limit_per_season=1):
        filtered_df = self.df.filter(col("Hotel_Name") == hotel_name)
        seasons = ["Winter", "Spring", "Summer", "Autumn"]
        results = []

        for season in seasons:
            seasonal_df = (
                filtered_df
                .filter(col("Season") == season)
                .select("Positive_Review", "Negative_Review", "Reviewer_Score", "Hotel_Name", "Hotel_Address")
                .limit(limit_per_season)
            )
            pandas_df = seasonal_df.toPandas()
            if pandas_df.empty:
                continue

            sentiments = []
            for _, row in pandas_df.iterrows():
                text = f"{row['Positive_Review']}. {row['Negative_Review']}"
                sentiment = self._get_sentiment_from_llm(text)
                sentiments.append(sentiment)

            avg_sentiment = round(sum(sentiments) / len(sentiments), 4)
            avg_score = round(pandas_df["Reviewer_Score"].mean(), 4)
            num_reviews = len(pandas_df)

            results.append({
                "Hotel_Name": pandas_df["Hotel_Name"].iloc[0],
                "Hotel_Address": pandas_df["Hotel_Address"].iloc[0],
                "Season": season,
                "Avg_Sentiment_Score": avg_sentiment,
                "Avg_Review_Score": avg_score,
                "Num_Reviews": num_reviews
            })

        result_pdf = pd.DataFrame(results)
        return self.df.sql_ctx.createDataFrame(result_pdf)
