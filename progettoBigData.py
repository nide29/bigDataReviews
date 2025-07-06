from pyspark.sql import SparkSession, Window
from pyspark.sql.functions import col, lower, trim, length, row_number
from pyspark.sql.types import IntegerType, FloatType, BooleanType, StringType
from pyspark.sql.functions import regexp_replace, split, expr, col, to_date, regexp_extract, udf, count, array_contains, datediff, avg, first, explode, abs, desc, asc, stddev, coalesce, to_date, when, date_format, lower, lit, sum, max, min, countDistinct, broadcast, round
from utils import estraiCitta, udf_haversine, is_adjective_or_adverb
from pyspark.sql.functions import udf, explode, lower, col
from pyspark.sql.types import ArrayType, StringType
from Summary import SummaryLLM
from seasonalSentimentAnalysis import SeasonalSentimentAnalysis
from seasonalSentimentAnalysisLLM import SeasonalSentimentAnalysisLLM

import os
os.environ['NLTK_DATA'] = '/Users/alessandro/nltk_data'

dataset_path = "/Users/alessandro/Desktop"


is_adj_adv_udf = udf(is_adjective_or_adverb, ArrayType(StringType()))
class SparkBuilder:
    def __init__(self):
        self.spark = SparkSession.builder \
            .appName("BigDataProject") \
            .getOrCreate()
        print("Sessione Spark <PROGETTO BIG DATA> avviata.")

        self.spark.sparkContext.setLogLevel("ERROR")  # per evitare di stampare sempre i Warning

        # Lettura del DataSet
        self.dataset = self.spark.read.csv(dataset_path, header=True, inferSchema=True, encoding="UTF-8")

        # Stampare lo schema del dataset prima del pre-process
        #print("Dataset Schema before pre-process")
        #self.dataset.printSchema()

        # Pre-Process del Dataset
        self.casting()
        self.preprocess()

        # Stampare schema dopo pre-process
        #print("Dataset Schema after pre-process")
        #self.dataset.printSchema()



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

        # Aggiungiamo una colonna per la nazionalità degli Hotel (utile per le Query)
        df = df.withColumn("Hotel_Nationality",
                           regexp_extract(col("Hotel_Address"), r'(United\s+Kingdom|\b[A-Z][a-z]+)$', 1))
        udf_estraiCitta = udf(estraiCitta, StringType())
        # Aggiungiamo anche una colonna per la città degli Hotel
        df = df.withColumn("Hotel_City", udf_estraiCitta(col("Hotel_Address"), col("Hotel_Nationality")))


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

        # 2. Rimozione duplicati
        df = df.dropDuplicates()

        # 2. Trim delle colonne testuali per eliminare spazi vuoti + tutto in lowercase
        text_columns = ['Positive_Review', 'Negative_Review', 'Reviewer_Nationality']
        for col_name in text_columns:
            df = df.withColumn(col_name, lower(trim(col(col_name))))

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
        df = df.dropna(subset=["lat", "lng"])

        # 5. Salva nel dataset della classe
        self.dataset = df

        print("Preprocessing completato: dati puliti e pronti per l'analisi.")

    def contaNulli(self):
        df = self.dataset
        total_count = df.count()
        for field in df.schema.fields:
            column = field.name
            if str(field.dataType) == "StringType()":
                non_null_count = df.filter(col(column).isNotNull() & (trim(col(column)) != '') & (trim(col(column)) != ' ')).count()
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

    def stampa_schema_e_conteggi(self):
        df = self.dataset
        print("Schema del dataset dopo il preprocessing:\n")
        df.printSchema()
        print("\nConteggio valori non nulli per ogni colonna:")
        total_count = df.count()
        for field in df.schema.fields:
            column = field.name
            non_null_count = df.filter(col(column).isNotNull()).count()
            print(f"{column}: {non_null_count} valori non nulli su {total_count} righe totali")



############################################
###     QUERY MANAGER PER ANALISI DATI   ###
############################################
class QueryManager:

    def __init__(self, df):
        self.df = df

    def schema_dataset(self):
        return self.df.printSchema

    def info_dataset(self, nRighe):
        return self.df.show(nRighe, truncate=False)



    '''======================== QUERY 3.1 ========================'''
    # Il compito di questa query è quello di restituire le informazioni medie delle città (come numero di Hotel,
    # punteggio medio delle recensioni, ecc...)
    def cityHotelInformation(self):
        df = self.df

        all_info = df.groupby("Hotel_City").agg(
            count("*").alias("Total_Reviews"),
            countDistinct("Hotel_Name").alias("Number_Hotel"),
            avg("Average_Score").alias("Average_Score"),
            sum(when((col("Negative_Review").like("No Negative")) | (col("Negative_Review").like("Nothing")),
                     0).otherwise(1)).alias("TotalN"),
            sum(when((col("Positive_Review").like("No Positive")) | (col("Positive_Review").like("Nothing")),
                     0).otherwise(1)).alias("TotalP"),
        )
        return all_info




    '''======================== QUERY 3.2 ========================'''
    # Il compito di questa Query è quello di restituire i top n Hotel per ogni città
    def top_hotel_per_citta_per_nazione(self, n=5):
        df = self.df

        # Media dei voti per ogni hotel, città e nazione
        hotel_avg = df.groupBy("Hotel_Nationality", "Hotel_City", "Hotel_Name") \
            .agg(avg("Reviewer_Score").alias("avg_score"))

        # Finestra per ordinare i migliori hotel per città e nazione
        window = Window.partitionBy("Hotel_Nationality", "Hotel_City").orderBy(desc("avg_score"))

        # Ranking e top 5 per città
        ranked = hotel_avg.withColumn("rank", row_number().over(window)) \
            .filter(col("rank") <= n)

        # Media dei voti per città e nazione
        city_avg = df.groupBy("Hotel_Nationality", "Hotel_City") \
            .agg(avg("Reviewer_Score").alias("city_avg_score"))

        # Unione risultati
        result = ranked.join(city_avg, on=["Hotel_Nationality", "Hotel_City"]) \
            .select("Hotel_Nationality", "Hotel_City", "city_avg_score", "Hotel_Name", "avg_score", "rank") \
            .orderBy("Hotel_Nationality", "Hotel_City", "rank")

        return result

    #QUERY DI SUPPORTO PER LA STAMPA DEI RISULTATI
    def stampa_query2(self):
        result = self.top_hotel_per_citta_per_nazione()
        nazioni = [row["Hotel_Nationality"] for row in result.select("Hotel_Nationality").distinct().collect()]
        for nazione in nazioni:
            print(f"\n=== {nazione} ===")
            citta = [row["Hotel_City"] for row in
                     result.filter(col("Hotel_Nationality") == nazione).select("Hotel_City").distinct().collect()]
            for city in citta:
                print(f"\n--- {city} ---")
                result.filter((col("Hotel_Nationality") == nazione) & (col("Hotel_City") == city)).orderBy("rank").show(
                    truncate=False)




    '''=====QUERY 3.3====='''
    '''
    # Questa Query permette di effettuare un'analisi degli aggettivi e degli avverbi per capire quali parole sono
    # indicatori di punteggi alti o bassi
    def analisi_aggettivi_avverbi(self, min_freq=10):
        df = self.df.withColumn(
            "review_text",
            col("Positive_Review") + " " + col("Negative_Review")   # non mettiamo in lowercase in quanto wordnet è addestrato con la capitalizzazione corretta, quindi con il lower la funzione ha problemi
        )
        df = df.withColumn("parole", udf_estrai_aggettivi_avverbi(col("review_text")))
        df_words = df.select(col("Reviewer_Score"), explode(col("parole")).alias("word"))
        result = df_words.groupBy("word") \
            .agg(count("*").alias("freq"), avg("Reviewer_Score").alias("avg_score")) \
            .filter(col("freq") >= min_freq) \
            .orderBy(col("avg_score").desc())
        return result
    '''

    def words_score_analysis(self, min_frequency=1000):
        # UDF per filtrare aggettivi e avverbi
        is_adj_adv_udf = udf(is_adjective_or_adverb, BooleanType())

        # Positive reviews
        positive_words = self.df.select(
            col("Reviewer_Score"),
            explode(split(col("Positive_Review"), r"\s+")).alias("word")
        ).filter(col("word") != "")
        positive_words_filtered = positive_words.filter(is_adj_adv_udf(col("word")))
        positive_word_scores = positive_words_filtered.groupBy("word") \
            .agg(
            avg("Reviewer_Score").alias("avg_score"),
            count("word").alias("word_count")
        ) \
            .filter(col("word_count") >= min_frequency) \
            .orderBy(desc("avg_score"))

        # Negative reviews
        negative_words = self.df.select(
            col("Reviewer_Score"),
            explode(split(col("Negative_Review"), r"\s+")).alias("word")
        ).filter(col("word") != "")
        negative_words_filtered = negative_words.filter(is_adj_adv_udf(col("word")))
        negative_word_scores = negative_words_filtered.groupBy("word") \
            .agg(
            avg("Reviewer_Score").alias("avg_score"),
            count("word").alias("word_count")
        ) \
            .filter(col("word_count") >= min_frequency) \
            .orderBy("avg_score")

        return positive_word_scores, negative_word_scores


    '''=========QUERY 3.4========'''

    def mostAndLeastTagUsed(self):
        df = self.df

        df_tags = df.select(explode("Tags").alias("word"))
        frequenza_tag = df_tags.groupBy("word").count()
        frequenza_tag = frequenza_tag.orderBy("count", ascending=False)
        return frequenza_tag


    '''=================QUERY 3.5================'''

    def tag_influence_analysis(self, min_count=1000):
        df = self.df

        # Esplodi la colonna Tags in righe individuali
        exploded_tags = df.select(
            col("Reviewer_Score"),
            explode(col("Tags")).alias("tag")
        )
        # Calcola la media del punteggio e il conteggio per ciascun tag
        tag_scores_desc = exploded_tags.groupBy("tag") \
            .agg(
            avg("Reviewer_Score").alias("avg_score"),
            count("*").alias("tag_count")
        ) \
            .filter(col("tag_count") >= min_count).orderBy(desc("avg_score"))

        return tag_scores_desc


    '''==========QUERY 3.6============='''
    def recensioni_lunghezza(self):
        from pyspark.sql.functions import length, lit, col, desc, asc, row_number
        from pyspark.sql import Window

        # Sostituisci 'Hotel_Address' con 'City' se la colonna si chiama diversamente
        # Recensioni positive
        df_pos = self.df.select(
            col("Positive_Review").alias("review_text"),
            col("Reviewer_Score"),
            col("Hotel_Name"),
            col("Hotel_City"),
            lit("positiva").alias("type")
        ).withColumn("length", length(col("review_text")))

        window_pos_long = Window.orderBy(desc("length"))
        pos_longest = df_pos.withColumn("rn", row_number().over(window_pos_long)).filter(col("rn") == 1).drop("rn")

        window_pos_short = Window.orderBy(asc("length"))
        pos_shortest = df_pos.withColumn("rn", row_number().over(window_pos_short)).filter(col("rn") == 1).drop("rn")

        # Recensioni negative
        df_neg = self.df.select(
            col("Negative_Review").alias("review_text"),
            col("Reviewer_Score"),
            col("Hotel_Name"),
            col("Hotel_City"),
            lit("negativa").alias("type")
        ).withColumn("length", length(col("review_text")))

        window_neg_long = Window.orderBy(desc("length"))
        neg_longest = df_neg.withColumn("rn", row_number().over(window_neg_long)).filter(col("rn") == 1).drop("rn")

        window_neg_short = Window.orderBy(asc("length"))
        neg_shortest = df_neg.withColumn("rn", row_number().over(window_neg_short)).filter(col("rn") == 1).drop("rn")

        # Unisci tutti i risultati
        return pos_longest.unionByName(pos_shortest).unionByName(neg_longest).unionByName(neg_shortest)


    '''=================QUERY 3.7==============='''
    # SEASONAL SENTIMENT ANALYSIS
    def seasonalSentimentTrend(self):
        """
        Mostra il sentiment medio per stagione basato su VADER.
        """
        df = self.df
        seasonal_analyzer = SeasonalSentimentAnalysis(df)
        return seasonal_analyzer.getAverageSentimentBySeason()

    def seasonalSentimentTrendForHotel(self, hotel_name):
        df = self.df
        analyzer = SeasonalSentimentAnalysis(df)
        return analyzer.getAverageSentimentBySeasonForHotel(hotel_name)


    # Vediamo ora anche una versione che invece di utilizzare VADER utilizza DeepSeek 1.5B per il sentiment
    # Questa funzione non verrà utilizzata, in quanto è molto più lenta e costosa, inoltre per far si che il risultato
    # venga prodotto in un termine ragionevole, è necessario limitare fortemente il numero di recensioni per stagione
    def seasonalStatsForHotelWithLLM(self, hotel_name):
        analyzer = SeasonalSentimentAnalysisLLM(self.df)
        return analyzer.getSeasonalStatsForHotel(hotel_name)


    '''=================QUERY 3.8==============='''

    def preferenze_citta_per_nazionalita_dict(self, top_n=10):
        from pyspark.sql import Window
        from pyspark.sql.functions import avg, desc, row_number, col

        # Calcola la media dei punteggi per ogni nazionalità e città
        df_grouped = self.df.groupBy("Reviewer_Nationality", "Hotel_City") \
            .agg(avg("Reviewer_Score").alias("avg_score"))

        # Finestra per ranking per ogni nazionalità
        window = Window.partitionBy("Reviewer_Nationality").orderBy(desc("avg_score"))

        # Aggiungi ranking e filtra i top N per ogni nazionalità
        ranked = df_grouped.withColumn("rank", row_number().over(window)) \
            .filter(col("rank") <= top_n)

        # Colleziona i risultati in un dizionario Python
        result = {}
        for row in ranked.orderBy("Reviewer_Nationality", "rank").collect():
            naz = row["Reviewer_Nationality"]
            city = row["Hotel_City"]
            if naz not in result:
                result[naz] = []
            result[naz].append(city)
        return result

    def stampa_query8(self):
        preferenze = self.preferenze_citta_per_nazionalita_dict()
        for naz, cities in preferenze.items():
            print(f"\nNazionalità: {naz}\nPreference: {{")
            for i, city in enumerate(cities, 1):
                print(f"{i}. {city}")
            print("}")

    def classifica_citta_preferite_df(self, top_n=10):
        from pyspark.sql import Window
        from pyspark.sql.functions import avg, desc, row_number, col

        # Calcola la media dei punteggi per ogni nazionalità e città
        df_grouped = self.df.groupBy("Reviewer_Nationality", "Hotel_City") \
            .agg(avg("Reviewer_Score").alias("avg_score"))

        # Finestra per ranking per ogni nazionalità
        window = Window.partitionBy("Reviewer_Nationality").orderBy(desc("avg_score"))

        # Aggiungi ranking e filtra i top N per ogni nazionalità
        ranked = df_grouped.withColumn("rank", row_number().over(window)) \
            .filter(col("rank") <= top_n) \
            .orderBy("Reviewer_Nationality", "rank")

        return ranked




    '''=================================================================================================================='''

    '''=================== QUERY 4.1 ====================='''
    def punteggio_medio_storico_hotel(self, hotel_name):
        return self.df.filter(col("Hotel_Name") == hotel_name) \
            .agg(round(avg("Reviewer_Score"), 1).alias("avg_score"))


    '''=================== QUERY 4.2 ====================='''
    def trend_mensile_hotel(self, hotel_name):
        from pyspark.sql.functions import year, month

        return self.df.filter(col("Hotel_Name") == hotel_name) \
            .groupBy(year(col("Review_Date")).alias("anno"), month(col("Review_Date")).alias("mese")) \
            .agg(round(avg("Reviewer_Score"), 1).alias("media_mensile")) \
            .orderBy("anno", "mese")


    '''=================== QUERY 4.3 ====================='''

    def hotel_vicini(self, hotel_name, raggio_km=1.0):
        from pyspark.sql.functions import col

        hotel_unici_df = self.hotel_unici()

        # Recupera le coordinate dell'hotel richiesto
        hotel_coord = hotel_unici_df.filter(col("Hotel_Name") == hotel_name) \
            .select("lat", "lng").limit(1).collect()
        if not hotel_coord:
            print("Hotel non trovato.")
            return None
        lat0, lng0 = hotel_coord[0]["lat"], hotel_coord[0]["lng"]

        # Calcola la distanza Haversine solo sugli hotel unici
        df_dist = hotel_unici_df.withColumn(
            "distanza",
            udf_haversine(col("lat"), col("lng"), lit(lat0), lit(lng0))
        )

        vicini = df_dist.filter(
            (col("distanza") <= raggio_km) & (col("Hotel_Name") != hotel_name)
        ).select("Hotel_Name", "Hotel_City", "distanza").orderBy("distanza")

        return vicini



    '''=================== QUERY 4.4 ====================='''

    def hotel_vicini_a_punto(self, lat, lng, raggio_km=500.0):
        """Restituisce gli hotel entro raggio_km dal punto (lat, lng)."""
        # Usa il DataFrame degli hotel unici
        hotel_unici_df = self.hotel_unici()
        # Calcola la distanza Haversine dal punto dato
        df_dist = hotel_unici_df.withColumn(
            "distanza",
            udf_haversine(col("lat"), col("lng"), lit(lat), lit(lng))
        )
        # Filtra gli hotel entro il raggio specificato
        vicini = df_dist.filter(col("distanza") <= raggio_km) \
            .select("Hotel_Name", "Hotel_City", "lat", "lng", "distanza") \
            .orderBy("distanza")
        return vicini


    '''=================== QUERY 4.5 ====================='''
    def reputazione_hotel(self, hotel_name):
        from pyspark.sql.functions import col, max as spark_max, datediff, avg, lit, round

        # Filtra le recensioni dell'hotel
        df_hotel = self.df.filter(col("Hotel_Name") == hotel_name)

        # Trova la data più recente nel dataset
        max_date = self.df.agg(spark_max("Review_Date").alias("max_date")).collect()[0]["max_date"]

        # Media storica
        media_storica_df = df_hotel.agg(avg("Reviewer_Score").alias("media_storica"))
        # Media ultimi 30 giorni
        df_recenti = df_hotel.filter(datediff(lit(max_date), col("Review_Date")) <= 30)
        media_recenti_df = df_recenti.agg(avg("Reviewer_Score").alias("media_ultimi_30gg"))

        # Unisci i risultati in un unico DataFrame
        result = media_storica_df.crossJoin(media_recenti_df) \
            .withColumn("Hotel_Name", lit(hotel_name)) \
            .withColumn("reputazione", col("media_ultimi_30gg") - col("media_storica")) \
            .select("Hotel_Name", "media_storica", "media_ultimi_30gg", "reputazione")

        return result


    '''=================== QUERY 4.6 ====================='''
    def recensioni_anomale(self, hotel_name):

        # Calcola media e deviazione standard per ogni hotel
        hotel_stats = self.df.groupBy("Hotel_Name").agg(
            avg("Reviewer_Score").alias("avg_score"),
            stddev("Reviewer_Score").alias("stddev_score")
        )

        # Unisci le statistiche al DataFrame originale
        df_with_stats = self.df.join(hotel_stats, on="Hotel_Name")

        # Filtra le recensioni anomale per l'hotel richiesto
        anomalie = df_with_stats.filter(
            (col("Hotel_Name") == hotel_name) &
            (abs(col("Reviewer_Score") - col("avg_score")) > (2 * col("stddev_score")))
        ).select(
            "Hotel_Name", "Reviewer_Score", "avg_score", "stddev_score", "Positive_Review", "Negative_Review"
        ).orderBy(asc("Reviewer_Score"))

        return anomalie


    '''=================== QUERY 4.7 ====================='''
    def statistiche_generali_hotel(self, hotel_name):

        stats = self.df.filter(col("Hotel_Name") == hotel_name).agg(
            count("*").alias("Total_Reviews"),
            sum(when(col("Reviewer_Score") >= 6, 1).otherwise(0)).alias("Total_Positive_Reviews"),
            sum(when(col("Reviewer_Score") < 6, 1).otherwise(0)).alias("Total_Negative_Reviews"),
            max("Reviewer_Score").alias("Max_Reviewer_Score"),
            min("Reviewer_Score").alias("Min_Reviewer_Score"),
            avg("Reviewer_Score").alias("Avg_Reviewer_Score"),
            first("lat").alias("Latitude"),
            first("lng").alias("Longitude")
        ).withColumn("Hotel_Name", lit(hotel_name)).select(
            "Hotel_Name", "Total_Reviews", "Total_Positive_Reviews", "Total_Negative_Reviews",
            "Max_Reviewer_Score", "Min_Reviewer_Score", "Avg_Reviewer_Score", "Latitude", "Longitude"
        )
        return stats


    '''=================== QUERY 4.8 ====================='''

    def summary_recensioni_hotel(self, hotel_name):
        summary_llm = SummaryLLM(self.df)
        return summary_llm.getSummary(hotel_name)


    '''=================== QUERY 4.9 ====================='''

    def averageSentimentForHotel_RoBERTa(self, hotel_name: str):
        from RoBERTa_SentimentAnalyzer import RoBERTa_SentimentAnalyzer
        analyzer = RoBERTa_SentimentAnalyzer(self.df)
        return analyzer.getHotelSentiment(hotel_name)


    '''=================== QUERY DI SUPPORTO ====================='''
    def hotel_unici(self):
        return self.df.select("Hotel_Name", "Hotel_City", "lat", "lng").distinct()
