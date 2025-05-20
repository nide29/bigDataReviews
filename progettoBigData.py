from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lower, trim, length
from pyspark.sql.types import IntegerType, FloatType, BooleanType, StringType
from pyspark.sql.functions import regexp_replace, split, expr, col, to_date, regexp_extract, udf, count, array_contains, avg, first, explode, abs, desc, asc, stddev, coalesce, to_date, when, date_format, lower, lit, sum, max, min


dataset_path = "/Users/alessandro/Desktop"
class SparkBuilder:
    def __init__(self):
        self.spark = SparkSession.builder \
            .appName("BigDataProject") \
            .getOrCreate()
        print("Sessione Spark <PROGETTO BIG DATA> avviata.")

        self.spark.sparkContext.setLogLevel("ERROR")  # per evitare di stampare sempre i Warning

        # Lettura del DataSet
        self.dataset = self.spark.read.csv(dataset_path, header=True, inferSchema=True)

        # Stampare lo schema del dataset prima del pre-process
        print("Dataset Schema before pre-process")
        self.dataset.printSchema()

        # Pre-Process del Dataset
        self.casting()
        self.preprocess()

        # Stampare schema dopo pre-process
        print("Dataset Schema after pre-process")
        self.dataset.printSchema()



        # QueryManager associato alla sessione corrente
        #self.query_manager = QueryManager(self)


    def casting(self):
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

    def preprocess(self):
        df = self.dataset  # usa il dataset già caricato nella classe

        # 1. Colonne critiche con pochi missing → drop diretto
        critical_columns = [
            'Additional_Number_of_Scoring', 'Review_Date', 'Average_Score',
            'Hotel_Name', 'Review_Total_Negative_Word_Counts',
            'Total_Number_of_Reviews', 'Review_Total_Positive_Word_Counts',
            'Total_Number_of_Reviews_Reviewer_Has_Given',
            'Reviewer_Score', 'Tags', 'days_since_review'
        ]
        df = df.dropna(subset=critical_columns)

        # 2. Trim delle colonne testuali per eliminare spazi vuoti
        text_columns = ['Positive_Review', 'Negative_Review', 'Reviewer_Nationality']
        for col_name in text_columns:
            df = df.withColumn(col_name, trim(col(col_name)))

        # 3. Imputazione testuale su valori mancanti o vuoti
        df = df.withColumn(
            "Positive_Review",
            when(col("Positive_Review").isNull() | (col("Positive_Review") == ''), lit("No positive comment"))
            .otherwise(col("Positive_Review"))
        )
        df = df.withColumn(
            "Negative_Review",
            when(col("Negative_Review").isNull() | (col("Negative_Review") == ''), lit("No negative comment"))
            .otherwise(col("Negative_Review"))
        )
        df = df.withColumn(
            "Reviewer_Nationality",
            when(col("Reviewer_Nationality").isNull() | (col("Reviewer_Nationality") == ''), lit("Unknown"))
            .otherwise(col("Reviewer_Nationality"))
        )

        # 4. Drop righe con coordinate mancanti (dopo eventuale geocoding)
        #df = df.dropna(subset=["lat", "lng"])

        # 5. Salva nel dataset della classe
        self.dataset = df

        print("Preprocessing completato: dati puliti e pronti per l'analisi.")

    def contaNulli(self):
        df = self.dataset
        total_count = df.count()
        for field in df.schema.fields:
            column = field.name
            if str(field.dataType) == "StringType()":
                non_null_count = df.filter(col(column).isNotNull() & (trim(col(column)) != '')).count()
            else:
                non_null_count = df.filter(col(column).isNotNull()).count()
            missing_count = total_count - non_null_count
            print(f">Colonna: ###{column}### \nNon Null: {non_null_count}, Mancanti: {missing_count}\n")

    def mostra_righe_con_nulli_or_vuoti(self):
        df = self.dataset
        conditions = []
        for field in df.schema.fields:
            column = field.name
            if isinstance(field.dataType, StringType):
                conditions.append(col(column).isNull() | (trim(col(column)) == ''))
            else:
                conditions.append(col(column).isNull())
        if not conditions:
            print("Nessuna colonna trovata.")
            return
        combined_condition = conditions[0]
        for cond in conditions[1:]:
            combined_condition = combined_condition | cond
        righe_nulli_ou_vuoti = df.filter(combined_condition)
        # Stampa header
        print(" | ".join(righe_nulli_ou_vuoti.columns))
        for row in righe_nulli_ou_vuoti.collect():
            print(" | ".join([str(x) if x is not None else "" for x in row]))




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