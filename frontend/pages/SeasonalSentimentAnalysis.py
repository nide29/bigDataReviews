import streamlit as st
import pydeck as pdk
import pandas as pd
import json
import os
from PIL import Image, ImageDraw

from progettoBigData import SparkBuilder

GEOJSON_PATH = os.path.join(os.path.dirname(__file__), "europe_countries.geojson")

with open(GEOJSON_PATH) as f:
    geojson = json.load(f)

st.set_page_config(
    page_title="Seasonal Sentiment Analysis",
    page_icon="🏖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_resource
def get_query_manager():
    spark_builder = SparkBuilder()
    return spark_builder.query_manager


query_manager = get_query_manager()

# Lista delle 6 nazioni effettivamente presenti nel dataset
available_nations = [
    "Italy",
    "France",
    "United Kingdom",
    "Netherlands",
    "Austria",
    "Spain"
]

# Filtra le features del geojson per mostrare solo queste nazioni
geojson["features"] = [f for f in geojson["features"] if f["properties"]["name"] in available_nations]

st.title("🏖️ Seasonal Sentiment Analysis")

# --- PRIMA QUERY: Sentiment medio annuale per nazione ---
st.header("Sentiment medio annuale per nazione")

# Ottieni il sentiment medio annuale per ogni nazione
df_nation_sentiment = query_manager.averageSentimentByNation().toPandas()

# Mappa nome nazione (dataset) -> nome geojson se necessario
name_map = {
    "italy": "Italy",
    "france": "France",
    "united kingdom": "United Kingdom",
    "netherlands": "Netherlands",
    "austria": "Austria",
    "spain": "Spain"
}

def sentiment_to_color(sentiment):
    if sentiment is None:
        return [180, 180, 180, 80]
    # Intervalli personalizzati per i dati
    if sentiment < 0.37:
        return [180, 255, 180, 180]  # verde molto chiaro
    elif sentiment < 0.39:
        return [100, 220, 100, 180]  # verde chiaro
    elif sentiment < 0.41:
        return [40, 180, 40, 180]    # verde medio
    else:
        return [0, 120, 0, 180]      # verde scuro

# Applica colore alle nazioni in base al sentiment medio
for feature in geojson["features"]:
    nation_name = feature["properties"]["name"]
    row = df_nation_sentiment[df_nation_sentiment["nation"].str.lower() == nation_name.lower()]
    if not row.empty:
        sentiment = row["mean_sentiment"].values[0]
        feature["properties"]["sentiment"] = round(sentiment, 3)
        feature["properties"]["color"] = sentiment_to_color(sentiment)
    else:
        feature["properties"]["sentiment"] = None
        feature["properties"]["color"] = sentiment_to_color(None)

layer = pdk.Layer(
    "GeoJsonLayer",
    data=geojson,
    get_fill_color="properties.color",
    get_line_color=[80, 80, 80, 200],
    pickable=True,
    auto_highlight=True,
)

def draw_legend():
    legend = Image.new("RGBA", (220, 110), (255, 255, 255, 0))
    draw = ImageDraw.Draw(legend)
    colors = [
        ([180, 255, 180, 255], "Sentiment < 0.37"),
        ([100, 220, 100, 255], "0.37 <= Sentiment < 0.39"),
        ([40, 180, 40, 255], "0.39 <= Sentiment < 0.41"),
        ([0, 120, 0, 255], "Sentiment >= 0.41"),
    ]
    for i, (color, label) in enumerate(colors):
        y = 10 + i * 25
        draw.rectangle([10, y, 30, y + 20], fill=tuple(color))
        draw.text((40, y), label, fill=(0, 0, 0, 255))
    return legend


st.image(draw_legend(), caption="Legenda sentiment", use_container_width=False)

view_state = pdk.ViewState(latitude=48, longitude=10, zoom=4)
r = pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    tooltip={"text": "{name}\nSentiment: {sentiment}"},
)

st.pydeck_chart(r)
st.dataframe(df_nation_sentiment.rename(columns={"nation": "Nazione", "mean_sentiment": "Sentiment medio"}))



# --- SECONDA QUERY: Sentiment stagionale per nazione selezionata ---
st.header("Sentiment stagionale per nazione")

# 6 bottoni in linea
cols = st.columns(6)
nation_selected = None
for i, nation in enumerate(available_nations):
    if cols[i].button(nation):
        nation_selected = nation

# Se nessun bottone è stato premuto, seleziona la prima nazione di default
if nation_selected is None:
    nation_selected = available_nations[0]

df_season = query_manager.seasonalSentimentTrendForNation(nation_selected).toPandas()

# Mostra la tabella
st.subheader(f"Sentiment stagionale per: {nation_selected}")
st.table(df_season)

# Analisi automatica del trend
if not df_season.empty:
    max_row = df_season.loc[df_season["Avg_Sentiment_Score"].idxmax()]
    min_row = df_season.loc[df_season["Avg_Sentiment_Score"].idxmin()]
    st.info(
        f"Il sentiment più alto si registra in **{max_row['Season']}** ({max_row['Avg_Sentiment_Score']:.4f}), "
        f"mentre il più basso in **{min_row['Season']}** ({min_row['Avg_Sentiment_Score']:.4f})."
    )
