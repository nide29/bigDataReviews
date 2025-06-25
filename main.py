from pyspark.sql.functions import col

from progettoBigData import SparkBuilder, QueryManager

spark_builder = SparkBuilder()
df = spark_builder.dataset
manager = QueryManager(df)


#spark_builder.contaNulli()


# UTILE PER RELAZIONE
#print("RECAP")
#spark_builder.stampa_schema_e_conteggi()

'''QUERY TEST'''
print("🧾 Media punteggio per hotel:")
manager.media_punteggio_per_hotel().show()

print("🌍 Numero recensioni per nazione:")
manager.numero_recensioni_per_nazione().show()

