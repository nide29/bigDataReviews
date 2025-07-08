import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
from progettoBigData import SparkBuilder
import plotly.express as px

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
    #st.markdown("---")
    st.header(f"Analisi per: {hotel_selected}")

    # 1. Punteggio medio storico
    st.subheader("Punteggio medio storico")
    df_avg = query_manager.punteggio_medio_storico_hotel(hotel_selected).toPandas()
    if not df_avg.empty and "avg_score" in df_avg.columns:
        score = df_avg["avg_score"].iloc[0]
        if score >= 8.5:
            msg = "🏆 L'hotel ha un punteggio <b>molto alto</b>!"
            bgcolor = "#2ecc40"  # verde
        elif score >= 7:
            msg = "😊 L'hotel ha un punteggio <b>alto</b>."
            bgcolor = "#a3e635"  # lime
        elif score >= 5.5:
            msg = "😐 L'hotel ha un punteggio <b>medio</b>."
            bgcolor = "#facc15"  # giallo
        else:
            msg = "⚠️ L'hotel ha un punteggio <b>basso</b>."
            bgcolor = "#ef4444"  # rosso

        st.markdown(
            f"""
            <div style='
                display: inline-block;
                padding: 0.7em 1.5em;
                border-radius: 1.5em;
                background: {bgcolor};
                color: white;
                font-size: 2.5em;
                font-weight: bold;
                box-shadow: 0 2px 8px rgba(0,0,0,0.07);
                margin-bottom: 0.5em;
            '>
                {score:.1f}
            </div>
            <div style='margin-top:0.5em;font-size:1.2em;'>{msg}</div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.info("Nessun dato disponibile per il punteggio medio.")

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
    if not df_stats.empty:
        stats = df_stats.iloc[0]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Totale recensioni", int(stats["Total_Reviews"]))
            st.metric("Recensioni positive", int(stats["Total_Positive_Reviews"]))
        with col2:
            st.metric("Recensioni negative", int(stats["Total_Negative_Reviews"]))
            st.metric("Punteggio medio", f"{stats['Avg_Reviewer_Score']:.2f}")
        with col3:
            st.metric("Punteggio minimo", f"{stats['Min_Reviewer_Score']:.1f}")
            st.metric("Punteggio massimo", f"{stats['Max_Reviewer_Score']:.1f}")

        # Diagramma a torta
        pie_data = {
            "Tipo": ["Positive", "Negative"],
            "Numero": [stats["Total_Positive_Reviews"], stats["Total_Negative_Reviews"]]
        }
        fig = px.pie(pie_data, names="Tipo", values="Numero", color="Tipo",
                     color_discrete_map={"Positive": "green", "Negative": "red"},
                     title="Distribuzione recensioni positive/negative")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nessuna statistica disponibile.")

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
    if not df_rep.empty:
        rep = df_rep.iloc[0]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Media storica", f"{rep['media_storica']:.2f}")
        with col2:
            st.metric("Media ultimi 30gg", f"{rep['media_ultimi_30gg']:.2f}")
        with col3:
            st.metric("Reputazione (Δ)", f"{rep['reputazione']:+.2f}")

        # Box colorato con messaggio
        if rep['reputazione'] > 0:
            msg = "📈 La reputazione dell'hotel sta <b>migliorando</b>!"
            bgcolor = "#2ecc40"  # verde
        else:
            msg = "📉 La reputazione dell'hotel sta <b>peggiorando</b>."
            bgcolor = "#ef4444"  # rosso

        st.markdown(
            f"""
            <div style='
                display: inline-block;
                padding: 0.5em 1.2em;
                border-radius: 1em;
                background: {bgcolor};
                color: white;
                font-size: 1.2em;
                font-weight: 500;
                margin-top: 0.5em;
            '>
                {msg}
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.info("Nessun dato disponibile sulla reputazione.")

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

    if not df_sentiment.empty and "Average_Sentiment_Score" in df_sentiment.columns and pd.notnull(
            df_sentiment["Average_Sentiment_Score"].iloc[0]):
        score = df_sentiment["Average_Sentiment_Score"].iloc[0]
        # Se la tabella contiene anche altri dati, ad esempio conteggi o percentuali:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Sentiment medio", f"{score:.2f}")
        if "Positive_Count" in df_sentiment.columns:
            with col2:
                st.metric("Recensioni positive", int(df_sentiment["Positive_Count"].iloc[0]))
        if "Negative_Count" in df_sentiment.columns:
            with col3:
                st.metric("Recensioni negative", int(df_sentiment["Negative_Count"].iloc[0]))

        # Box colorato con messaggio riassuntivo
        if score > 0.2:
            msg = "😊 Il sentiment generale è <b>positivo</b>!"
            bgcolor = "#2ecc40"
        elif score < -0.2:
            msg = "😞 Il sentiment generale è <b>negativo</b>."
            bgcolor = "#ef4444"
        else:
            msg = "😐 Il sentiment generale è <b>neutrale</b>."
            bgcolor = "#facc15"

        st.markdown(
            f"""
            <div style='
                display: inline-block;
                padding: 0.7em 1.5em;
                border-radius: 1.5em;
                background: {bgcolor};
                color: white;
                font-size: 2.5em;
                font-weight: bold;
                box-shadow: 0 2px 8px rgba(0,0,0,0.07);
                margin-bottom: 0.5em;
            '>
                {score:.2f}
            </div>
            <div style='margin-top:0.5em;font-size:1.2em;'>{msg}</div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.info("Nessun dato disponibile sull'analisi del sentiment.")

    # Se vuoi mostrare anche la tabella dettagliata:
    # st.dataframe(df_sentiment)


    # 8. Summary recensioni
    st.subheader("Riassunto delle recensioni")
    summary = query_manager.summary_recensioni_hotel(hotel_selected)
    st.write(summary)
else:
    st.info("Clicca su un hotel nella mappa per visualizzare l’analisi.")