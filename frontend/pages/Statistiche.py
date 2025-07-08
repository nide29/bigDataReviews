import streamlit as st
import sys
import os
from progettoBigData import SparkBuilder
import plotly.express as px

#sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configurazione della pagina
st.set_page_config(
    page_title="Statistiche",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.sidebar.title("🔍 Navigazione")
st.sidebar.markdown("### Sezioni disponibili:")
st.sidebar.markdown("- 🏠 **Home**")
st.sidebar.markdown("- 📊 **Statistiche**")
st.sidebar.markdown("- 🗺️ **Esplora con mappa**")
st.sidebar.markdown("- 📍 **Esplora per punto di interesse**")
st.sidebar.markdown("- #️⃣ **Esplora per tag**")
st.sidebar.markdown("- 🇮🇹 **Recensione-Nazionalità**")
st.sidebar.markdown("- 🏖️ **Sentiment Stagionale**")

@st.cache_resource
def get_query_manager():
    spark_builder = SparkBuilder()
    return spark_builder.query_manager


query_manager = get_query_manager()


st.markdown("<h1 style='text-align: center;'>📊 Statistiche sugli Hotel</h1>", unsafe_allow_html=True)
st.markdown("---")

# 1. Voti medi per nazione
st.subheader("🌍 Voti Medi per Nazione")
voti_nazione_df = query_manager.cityHotelInformation().toPandas()

# Seleziona le 6 nazioni principali (puoi modificarle in base ai dati)
nazioni_disponibili = voti_nazione_df["Hotel_City"].unique()[:6]
nazione_scelta = st.radio("Seleziona una nazione:", nazioni_disponibili, horizontal=True)

# Filtra la tabella per la nazione selezionata
df_nazione = voti_nazione_df[voti_nazione_df["Hotel_City"] == nazione_scelta]

if not df_nazione.empty:
    # Mostra i dati principali in modo leggibile
    info = df_nazione.iloc[0]
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Numero Hotel", int(info["Number_Hotel"]))
        st.metric("Totale Recensioni", int(info["Total_Reviews"]))
    with col2:
        st.metric("Punteggio Medio", f"{info['Average_Score']:.2f}")
    with col3:
        st.metric("Recensioni Positive", int(info["TotalP"]))
        st.metric("Recensioni Negative", int(info["TotalN"]))

    # Grafico a torta per TotalP e TotalN
    pie_data = {
        "Tipo": ["Positive", "Negative"],
        "Numero": [info["TotalP"], info["TotalN"]]
    }
    fig = px.pie(pie_data, names="Tipo", values="Numero", color="Tipo",
                 color_discrete_map={"Positive": "green", "Negative": "red"},
                 title="Distribuzione recensioni positive/negative")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Nessun dato disponibile per la nazione selezionata.")

# 2. Top N hotel per ogni città (con selezione città)
st.subheader("🏨 Top N Hotel per ogni Città")
# Recupera le 6 città disponibili
citta_disponibili = [row["Hotel_City"] for row in query_manager.df.select("Hotel_City").distinct().limit(6).collect()]
citta_disponibili.sort()
# Menu a tendina per la città
citta_scelta = st.selectbox("Seleziona una città:", citta_disponibili)
# Slider per N
n = st.slider("Quanti hotel vuoi visualizzare per la città selezionata?", min_value=1, max_value=10, value=3)
# Query e visualizzazione
if citta_scelta:
    top_hotel_df = query_manager.top_hotel_per_citta(citta_scelta, n)
    st.dataframe(top_hotel_df.toPandas(), use_container_width=True)


# 3. Preferenze culturali: città preferite per nazionalità
st.subheader("🌐 Preferenze culturali: città preferite per nazionalità")
# Recupera le nazionalità disponibili ed escludi 'Unknown'
nazionalita_disponibili = [
    row["Reviewer_Nationality"] for row in query_manager.df.select("Reviewer_Nationality").distinct().collect()
]
nazionalita_disponibili = [n for n in nazionalita_disponibili if n != "Unknown"]
nazionalita_disponibili.sort()

# Trova l'indice di "Italy" (se presente), altrimenti 0
default_index = nazionalita_disponibili.index("italy") if "italy" in nazionalita_disponibili else 0

# Menu a tendina per la nazionalità senza 'Unknown'
nazionalita_scelta = st.selectbox(
    "Seleziona una nazionalità:",
    nazionalita_disponibili,
    index=default_index,
    key="nazionalita"
)

# Query e visualizzazione (top_n fisso a 6)
if nazionalita_scelta:
    preferenze_df = query_manager.preferenze_citta_per_nazionalita_df(nazionalita=nazionalita_scelta, top_n=6)
    st.dataframe(preferenze_df.toPandas(), use_container_width=True)