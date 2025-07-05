from pyspark.sql.functions import col
import ollama

class SummaryLLM:
    def __init__(self, dataframe, model_name='deepseek-r1:1.5b'):
        """
        dataframe: DataFrame PySpark contenente le recensioni.
        model_name: Nome del modello Ollama da usare.
        """
        self.df = dataframe
        self.model = model_name

    def getReviews(self, hotel_name, limit=50):
        """
        Estrae le recensioni per l'hotel specificato.
        """
        reviews_df = self.df.filter(
            (col("Hotel_Name") == hotel_name) &
            (col("Positive_Review") != "No Positive") &
            (col("Negative_Review") != "No Negative")
        ).orderBy(col("Total_Number_of_Reviews_Reviewer_Has_Given")) \
         .select("Positive_Review", "Negative_Review") \
         .limit(limit)

        reviews_Pandas = reviews_df.toPandas()
        if reviews_Pandas.empty:
            return ""

        # Combina le recensioni
        combined_reviews = ""
        for _, row in reviews_Pandas.iterrows():
            combined_reviews += f"Positiva: {row['Positive_Review']} | Negativa: {row['Negative_Review']}. "
        return combined_reviews

    def getSummary(self, hotel_name):
        """
        Restituisce il riassunto generato dal modello LLM per l'hotel.
        """
        reviews = self.getReviews(hotel_name)
        if not reviews:
            return "Nessuna recensione trovata per questo hotel."

        prompt = (
            f"Give me a detailed and elegant summary of the following reviews (Return only the summary itself):\n{reviews}"
        )

        try:
            response = ollama.chat(model=self.model, messages=[
                {'role': 'user', 'content': prompt}
            ])
            content = response['message']['content']

            # Pulisce eventuali tag speciali
            while "<think>" in content and "</think>" in content:
                start = content.find("<think>")
                end = content.find("</think>") + len("</think>")
                content = content[:start] + content[end:]

            return content.strip()

        except Exception as e:
            return f"Errore durante la generazione del riassunto: {str(e)}"
