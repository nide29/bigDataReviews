import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import streamlit as st

from progettoBigData import SparkBuilder

# Configurazione avanzata della pagina
st.set_page_config(
    page_title="Hotel Dataset Analysis",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.sidebar.title("🔍 Navigazione")
st.sidebar.markdown("### Sezioni disponibili:")

st.sidebar.markdown("- 🏠 **Home**")
st.sidebar.markdown("- 📊 **Statistiche**")
st.sidebar.markdown("- 📝 **Analisi delle Recensioni**")
st.sidebar.markdown("- 🗺️ **Esplora con mappa**")
st.sidebar.markdown("- 📍 **Esplora per punto di interesse**")
st.sidebar.markdown("- #️⃣ **Esplora per tag**")
st.sidebar.markdown("- 🇮🇹 **Recensione-Nazionalità**")
st.sidebar.markdown("- 🏖️ **Sentiment Stagionale**")

@st.cache_resource
def get_spark_and_query_manager():
    """Inizializza SparkBuilder e QueryManager."""
    spark_builder = SparkBuilder()
    query_manager = spark_builder.query_manager()
    return query_manager

def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

# Funzione per la homepage migliorata
def show_landing_page():
    st.markdown(
        "<h1 style='text-align: center; color: #000000;'>🔍 Analisi delle Recensioni degli Hotel</h1>",
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        image_path = os.path.join(os.path.dirname(__file__), "images", "5stelle.jpg")
        if os.path.exists(image_path):
            st.image(image_path, width=700, caption="Visualizzazione dei dati sulle recensioni degli hotel")
        else:
            st.warning(
                "📸 Immagine non trovata: assicurati che 'PNY_Exterior_with_Rolls_Royce.jpg' sia nella cartella 'frontend/images'.")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(
            """
            <h3 style='color: #333;'>📌 Scopo del Progetto</h3>
            <p style='font-size: 18px;'>
            Questo progetto sfrutta Spark per analizzare le recensioni degli hotel in Europa.
            </p>
            """, unsafe_allow_html=True
        )

        st.markdown("### 🚀 Tecnologie Utilizzate")
        st.markdown("- 🔥 **Apache Spark** per il processamento massivo dei dati")
        st.markdown("- 🎨 **Streamlit** per un’interfaccia intuitiva e interattiva")
        st.markdown("- 📌 **Folium & Matplotlib** per la visualizzazione dei dati")
        st.markdown("- 🧠 **RoBERTa** per l'analisi del sentiment delle recensioni")
        st.markdown("- 🤖 **DeepSeek** per la generazione dei riassunti delle recensioni")

    st.markdown("---")

    st.markdown(
        """
        <h3 style='color: #333;'>🎯 Obiettivi Principali</h3>
        """, unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("✅ **Analisi del testo delle recensioni**")
        st.markdown("✅ **Valutazione della reputazione degli hotel**")
    with col2:
        st.markdown("✅ **Analisi del sentiment**")
        st.markdown("✅ **Individuazione di recensioni sospette**")
    with col3:
        st.markdown("✅ **Analisi dei trend temporali**")
        st.markdown("✅ **Correlazione tra nazionalità e punteggi**")

    st.markdown("---")

    st.markdown("<h3 style='text-align: center;'>💡 Inizia ora selezionando una pagina dal menu laterale!</h3>", unsafe_allow_html=True)


def main():
    clear_terminal()
    show_landing_page()


if __name__ == "__main__":
    main()
