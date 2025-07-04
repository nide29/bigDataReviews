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

'''
print("📊 Analisi giorni della settimana:")
manager.analisi_giorni_settimana().show()

print("📊 Trend ANNUALE dei punteggi:")
manager.trend_annuale_punteggi().show(100)

print("📅 Picchi recensioni mensili:")
manager.picchi_recensioni_mensili().show()

print("🗺️ Densità hotel per coordinate:")
manager.densita_hotel_per_coordinate().show()

print("🏙️ Confronto città europee:")
manager.confronto_citta_europee().show()

print("👤 Profili recensori:")
manager.profili_recensori().show()
'''


#print("🏙️ TEST QUERY 1:")
#manager.cityHotelInformation().show()

#print("🏙️ TEST QUERY 2:")
#manager.top_hotel_per_citta_per_nazione().show()

#print("🏙️ TEST QUERY 4:")
#manager.mostAndLeastTagUsed().show()

#print("🏙️ TEST QUERY 5:")
#manager.tag_influence_analysis().show()

#print("🏙️ TEST QUERY 6:")
#manager.recensioni_lunghezza().show(truncate=False)

#print("🏙️ TEST QUERY 7 - TODO:")

#print("🏙️ TEST QUERY 8:")
#manager.classifica_citta_preferite_df().show()


#print("🏙️ TEST QUERY 4.1:")
#manager.punteggio_medio_storico_hotel('Hotel Arena').show()

#print("🏙️ TEST QUERY 4.2:")
#manager.trend_mensile_hotel('Hotel Arena').show()

#print("🏙️ TEST QUERY 4.3:")
#manager.hotel_vicini('Hotel Arena').show(truncate=False)

print("🏙️ TEST QUERY 4.4:")
manager.hotel_vicini_a_punto(45.4477479, 9.1835306).show(truncate=False)
