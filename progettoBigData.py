from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lower, trim, length
from pyspark.sql.types import IntegerType, FloatType, BooleanType
from pyspark.sql.functions import regexp_replace, split, expr, col, to_date, regexp_extract, udf, count, array_contains, avg, first, explode, abs, desc, asc, stddev, coalesce, to_date, when, date_format, lower, lit, sum, max, min


dataset_path = "/Users/alessandro/Desktop"
class SparkBuilder:
    def __init__(self):
        self.spark = SparkSession.builder \
            .appName("BigDataProject") \
            .getOrCreate()
        print("Sessione Spark avviata.")

        self.spark.sparkContext.setLogLevel("ERROR")  # per evitare di stampare sempre i Warning

        # Lettura del DataSet
        self.dataset = self.spark.read.csv(dataset_path, header=True, inferSchema=True)

        # Stampare lo schema del dataset prima del pre-process
        print("Dataset Schema before pre-process")
        self.dataset.printSchema()

        # Pre-Process del Dataset
        self.preprocess()

        # Stampare schema dopo pre-process
        print("Dataset Schema after pre-process")
        self.dataset.printSchema()



        # QueryManager associato alla sessione corrente
        #self.query_manager = QueryManager(self)


    def preprocess(self):
        df = self.dataset

        # Casting delle colonne
        df = df.withColumn("Additional_Number_of_Scoring", df["Additional_Number_of_Scoring"].cast(IntegerType()))
        df = df.withColumn("Review_Date", to_date(df["Review_Date"], "M/d/yyyy"))
        df = df.withColumn("Average_Score", df["Average_Score"].cast(FloatType()))
        df = df.withColumn("Review_Total_Negative_Word_Counts",
                           df["Review_Total_Negative_Word_Counts"].cast(IntegerType()))
        df = df.withColumn("Total_Number_of_Reviews", df["Total_Number_of_Reviews"].cast(IntegerType()))
        df = df.withColumn("Review_Total_Positive_Word_Counts",
                           df["Review_Total_Positive_Word_Counts"].cast(IntegerType()))
        df = df.withColumn("Total_Number_of_Reviews_Reviewer_Has_Given",
                           df["Total_Number_of_Reviews_Reviewer_Has_Given"].cast(IntegerType()))
        df = df.withColumn("Reviewer_Score", df["Reviewer_Score"].cast(FloatType()))
        df = df.withColumn("days_since_review",
                           regexp_extract(col("days_since_review"), r"(\d+)", 1).cast(IntegerType()))
        df = df.withColumn("lat", df["lat"].cast(FloatType()))
        df = df.withColumn("lng", df["lng"].cast(FloatType()))

        # Conversione della colonna Tags in un array di stringhe
        df = df.withColumn("Tags", regexp_replace(col("Tags"), "[\[\]']", ""))
        df = df.withColumn("Tags", split(col("Tags"), ", "))
        df = df.withColumn("Tags", expr("transform(Tags, x -> trim(x))"))

        self.dataset = df

    def contaNulli(self):
        df = self.dataset
        # Conta i valori non nulli per ogni colonna
        for column in df.columns:
            non_null_count = df.filter(col(column).isNotNull()).count()
            total_count = df.count()
            missing_count = total_count - non_null_count
            print(f"Colonna: {column}, Non Null: {non_null_count}, Mancanti: {missing_count}")

class QueryManager:
    def __init__(self, df):
        self.df = df

    def schema_dataset(self):
        return self.df.printSchema

    def info_dataset(self):
        return self.df.show(10)

    def media_punteggio_per_hotel(self):
        return self.df.groupBy("Hotel_Name").avg("Reviewer_Score").orderBy("avg(Reviewer_Score)", ascending=False)

    def numero_recensioni_per_nazione(self):
        return self.df.groupBy("Reviewer_Nationality").count().orderBy("count", ascending=False)

    def top_hotels_per_recensioni_positive(self, min_length=100):
        return self.df.filter(col("pos_review_len") > min_length).groupBy("Hotel_Name").count().orderBy("count",
                                                                                                        ascending=False)


'''
    print("🧾 Media punteggio per hotel:")
    manager.media_punteggio_per_hotel().show(5)

    print("🌍 Numero recensioni per nazione:")
    manager.numero_recensioni_per_nazione().show(5)

    print("🏨 Hotel con molte recensioni positive:")
    manager.top_hotels_per_recensioni_positive().show(5)
'''