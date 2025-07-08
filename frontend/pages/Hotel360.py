import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
from progettoBigData import SparkBuilder

st.set_page_config(page_title="Hotel360", page_icon="🏨", layout="wide")

@st.cache_resource
def get_query_manager():
    spark_builder = SparkBuilder()
    return spark_builder.query_manager


query_manager = get_query_manager()

st.title("🏨 Hotel360: Analisi completa degli hotel")

# Carica hotel unici
df_hotels = query_manager.hotel_unici().toPandas()

# Coordinate città (puoi aggiornarle in base ai tuoi dati)
city_coords = {
    "Milano": [45.4642, 9.1900],
    "Vienna": [48.2082, 16.3738],
    "Barcellona": [41.3851, 2.1734],
    "Londra": [51.5074, -0.1278],
    "Parigi": [48.8566, 2.3522],
    "Amsterdam": [52.3709, 4.8902]
}

cities = sorted(df_hotels["Hotel_City"].dropna().unique())
city_selected = st.selectbox("Seleziona la città", [c for c in cities if c in city_coords])

hotels_in_city = df_hotels[df_hotels["Hotel_City"] == city_selected].copy()
hotels_in_city = hotels_in_city.dropna(subset=["lat", "lng"])
hotels_in_city["lat"] = hotels_in_city["lat"].astype(float)
hotels_in_city["lng"] = hotels_in_city["lng"].astype(float)

# Crea la mappa con marker cliccabili
mappa = folium.Map(location=city_coords[city_selected], zoom_start=12)
for _, row in hotels_in_city.iterrows():
    folium.Marker(
        location=[row['lat'], row['lng']],
        popup=f"<b>{row['Hotel_Name']}</b>",
        tooltip=row['Hotel_Name'],
        icon=folium.Icon(color='blue', icon='info-sign')
    ).add_to(mappa)

map_data = st_folium(mappa, width=1000, height=550)

# Selezione hotel tramite click
hotel_selected = None
if map_data and map_data.get('last_object_clicked_tooltip') is not None:
    hotel_selected = map_data.get('last_object_clicked_tooltip')

if hotel_selected:
    st.markdown("---")
    st.header(f"Analisi per: {hotel_selected}")

    # 1. Punteggio medio storico
    st.subheader("Punteggio medio storico")
    df_avg = query_manager.punteggio_medio_storico_hotel(hotel_selected).toPandas()
    st.table(df_avg)

    # 2. Trend mensile
    st.subheader("Trend mensile")
    df_trend = query_manager.trend_mensile_hotel(hotel_selected).toPandas()

    # Assicurati che le colonne siano presenti e ordinate
    if not df_trend.empty and {"anno", "mese", "media_mensile"}.issubset(df_trend.columns):
        df_trend = df_trend.sort_values(["anno", "mese"])
        df_trend["periodo"] = df_trend["anno"].astype(str) + "-" + df_trend["mese"].astype(str).str.zfill(2)
        st.line_chart(df_trend.set_index("periodo")["media_mensile"])
    else:
        st.info("Nessun dato disponibile per il trend mensile.")

    # 3. Statistiche generali
    st.subheader("Statistiche generali")
    df_stats = query_manager.statistiche_generali_hotel(hotel_selected).toPandas()
    st.table(df_stats)

    # 4. Hotel vicini
    st.subheader("Consigli: hotel vicini")
    df_vicini = query_manager.hotel_vicini(hotel_selected, raggio_km=1.0)
    if df_vicini is not None:
        st.table(df_vicini.toPandas())
    else:
        st.info("Nessun hotel vicino trovato.")

    # 5. Reputazione hotel
    st.subheader("Reputazione dell’hotel")
    df_rep = query_manager.reputazione_hotel(hotel_selected).toPandas()
    st.table(df_rep)

    # 6. Recensioni anomale
    st.subheader("Recensioni anomale")
    df_anomale = query_manager.recensioni_anomale(hotel_selected).toPandas()
    if not df_anomale.empty:
        st.dataframe(df_anomale)
    else:
        st.info("Nessuna recensione anomala trovata.")

    # 7. Analisi sentiment RoBERTa
    st.subheader("Analisi del sentiment (RoBERTa)")
    df_sentiment = query_manager.averageSentimentForHotel_RoBERTa(hotel_selected).toPandas()
    st.table(df_sentiment)

    # 8. Summary recensioni
    st.subheader("Riassunto delle recensioni")
    summary = query_manager.summary_recensioni_hotel(hotel_selected)
    st.write(summary)
else:
    st.info("Clicca su un hotel nella mappa per visualizzare l’analisi.")