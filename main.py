from pyspark.sql.functions import col
import pprint
from progettoBigData import SparkBuilder, QueryManager

spark_builder = SparkBuilder()
df = spark_builder.dataset
manager = QueryManager(df)


#spark_builder.contaNulli()


# UTILE PER RELAZIONE
#print("RECAP")
#spark_builder.stampa_schema_e_conteggi()

'''QUERY TEST'''
#print("🧾 Media punteggio per hotel:")
#manager.media_punteggio_per_hotel().show()

#print("🌍 Numero recensioni per nazione:")
#manager.numero_recensioni_per_nazione().show()

#print("STATISTICHE GENERALI DEL DATASET:")
#pprint.pprint(manager.statistiche_generali_dataset())




print("🏙️ TEST QUERY 1:")
manager.cityHotelInformation().show()

#print("🏙️ TEST QUERY 2:")
#manager.top_hotel_per_citta('Milan').show()

#print("🏙️ TEST QUERY 3:")
#positive_df, negative_df = manager.words_score_analysis()

#print("=== Aggettivi/Avverbi più associati a punteggi alti (recensioni positive) ===")
#positive_df.show(truncate=False)

#print("\n=== Aggettivi/Avverbi più associati a punteggi bassi (recensioni negative) ===")
#negative_df.show(truncate=False)

#print("🏙️ TEST QUERY 4:")
#manager.mostAndLeastTagUsed().show()

#print("🏙️ TEST QUERY 5:")
#manager.tag_influence_analysis().show()

#print("🏙️ TEST QUERY 6:")
#manager.recensioni_lunghezza().show(truncate=False)

#print("🏙️ TEST QUERY 7:")
#manager.seasonalSentimentTrend().show(truncate=False)
#manager.seasonalSentimentTrendForNation('Italy').show(truncate=False)
#manager.seasonalSentimentTrendForHotel('Best Western Seraphine Kensington Olympia').show(truncate=False)
#print('\n🍤VERSIONE CON LLM:')
#manager.seasonalStatsForHotelWithLLM('Best Western Seraphine Kensington Olympia').show(truncate=False)

#print("🏙️ TEST QUERY 8:")
#manager.classifica_citta_preferite_df().show()


#print("🏙️ TEST QUERY 4.1:")
#manager.punteggio_medio_storico_hotel('Hotel Arena').show()

#print("🏙️ TEST QUERY 4.2:")
#manager.trend_mensile_hotel('Hotel Arena').show()

#print("🏙️ TEST QUERY 4.3:")
#manager.hotel_vicini('Hotel Arena').show(truncate=False)

#print("🏙️ TEST QUERY 4.4:")
#manager.hotel_vicini_a_punto(45.4477479, 9.1835306).show(truncate=False)

#print("🏙️ TEST QUERY 4.5:")
#manager.reputazione_hotel('Hotel Arena').show(truncate=False)

#print("🏙️ TEST QUERY 4.6:")
#manager.recensioni_anomale('Hotel Arena').show(truncate=False)

#print("🏙️ TEST QUERY 4.7:")
#manager.statistiche_generali_hotel('Hotel Arena').show(truncate=False)

#print("🏙️ TEST QUERY 4.8:")
#print(manager.summary_recensioni_hotel('Hotel Arena'))

#print("🏙️ TEST QUERY 4.9:")
#manager.averageSentimentForHotel_RoBERTa('Best Western Seraphine Kensington Olympia').show(truncate=False)
