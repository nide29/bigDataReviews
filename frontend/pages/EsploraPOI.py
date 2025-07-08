import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
from progettoBigData import SparkBuilder

st.set_page_config(page_title="EsploraPOI", page_icon="🗺️", layout="wide")


@st.cache_resource
def get_query_manager():
    spark_builder = SparkBuilder()
    return spark_builder.query_manager


query_manager = get_query_manager()

st.title("🗺️ Esplora Punti di Interesse e Hotel")

# Coordinate città e POI (da personalizzare con i tuoi dati reali)
city_coords = {
    "Milano": [45.4642, 9.1900],
    "Vienna": [48.2082, 16.3738],
    "Barcellona": [41.3851, 2.1734],
    "Londra": [51.5074, -0.1278],
    "Parigi": [48.8566, 2.3522],
    "Amsterdam": [52.3709, 4.8902]
}

# Esempio di POI per città (aggiungi/aggiorna secondo necessità)
city_poi = {
    "Milano": [
        {"nome": "Duomo di Milano", "lat": 45.4642, "lng": 9.1916},
        {"nome": "Castello Sforzesco", "lat": 45.4700, "lng": 9.1793},
        {"nome": "Galleria Vittorio Emanuele II", "lat": 45.4668, "lng": 9.1899},
        {"nome": "Teatro alla Scala", "lat": 45.4670, "lng": 9.1899},
        {"nome": "Santa Maria delle Grazie", "lat": 45.4658, "lng": 9.1704},
        {"nome": "Navigli", "lat": 45.4495, "lng": 9.1700},
        {"nome": "Piazza Gae Aulenti", "lat": 45.4841, "lng": 9.1920}
    ],
    "Vienna": [
        {"nome": "Schönbrunn Palace", "lat": 48.1845, "lng": 16.3122},
        {"nome": "Stephansdom", "lat": 48.2082, "lng": 16.3738},
        {"nome": "Belvedere Palace", "lat": 48.1914, "lng": 16.3804},
        {"nome": "Hofburg Palace", "lat": 48.2065, "lng": 16.3656},
        {"nome": "Prater", "lat": 48.2167, "lng": 16.4000},
        {"nome": "Kunsthistorisches Museum", "lat": 48.2035, "lng": 16.3615},
        {"nome": "Vienna State Opera", "lat": 48.2026, "lng": 16.3686}
    ],
    "Barcellona": [
        {"nome": "Sagrada Familia", "lat": 41.4036, "lng": 2.1744},
        {"nome": "Parc Güell", "lat": 41.4145, "lng": 2.1527},
        {"nome": "Casa Batlló", "lat": 41.3916, "lng": 2.1649},
        {"nome": "Casa Milà (La Pedrera)", "lat": 41.3954, "lng": 2.1615},
        {"nome": "La Rambla", "lat": 41.3809, "lng": 2.1730},
        {"nome": "Barri Gòtic", "lat": 41.3839, "lng": 2.1760},
        {"nome": "Montjuïc", "lat": 41.3634, "lng": 2.1585}
    ],
    "Amsterdam": [
        {"nome": "Rijksmuseum", "lat": 52.3599, "lng": 4.8852},
        {"nome": "Van Gogh Museum", "lat": 52.3584, "lng": 4.8811},
        {"nome": "Anne Frank House", "lat": 52.3752, "lng": 4.8838},
        {"nome": "Dam Square", "lat": 52.3731, "lng": 4.8922},
        {"nome": "Vondelpark", "lat": 52.3580, "lng": 4.8687},
        {"nome": "Heineken Experience", "lat": 52.3570, "lng": 4.8910},
        {"nome": "Amsterdam Central Station", "lat": 52.3791, "lng": 4.9003}
    ],
    "Parigi": [
        {"nome": "Torre Eiffel", "lat": 48.8584, "lng": 2.2945},
        {"nome": "Louvre", "lat": 48.8606, "lng": 2.3376},
        {"nome": "Cattedrale di Notre-Dame", "lat": 48.8530, "lng": 2.3499},
        {"nome": "Montmartre - Sacré-Cœur", "lat": 48.8867, "lng": 2.3431},
        {"nome": "Arco di Trionfo", "lat": 48.8738, "lng": 2.2950},
        {"nome": "Champs-Élysées", "lat": 48.8698, "lng": 2.3075},
        {"nome": "Museo d'Orsay", "lat": 48.8599, "lng": 2.3266}
    ],
    "Londra": [
        {"nome": "Buckingham Palace", "lat": 51.5014, "lng": -0.1419},
        {"nome": "Tower of London", "lat": 51.5081, "lng": -0.0759},
        {"nome": "British Museum", "lat": 51.5194, "lng": -0.1270},
        {"nome": "London Eye", "lat": 51.5033, "lng": -0.1195},
        {"nome": "Big Ben", "lat": 51.5007, "lng": -0.1246},
        {"nome": "Trafalgar Square", "lat": 51.5080, "lng": -0.1281},
        {"nome": "Hyde Park", "lat": 51.5073, "lng": -0.1657}
    ]
}


cities = sorted(city_coords.keys())
city_selected = st.selectbox("Seleziona la città", cities)

poi_list = city_poi[city_selected]
poi_names = [poi["nome"] for poi in poi_list]
poi_selected_name = st.selectbox("Scegli un punto di interesse", poi_names)
poi_selected = next(poi for poi in poi_list if poi["nome"] == poi_selected_name)

radius_km = st.slider("Seleziona il raggio di ricerca (km)", min_value=0.5, max_value=10.0, value=1.0, step=0.5)

# Mappa con marker per il POI
mappa = folium.Map(location=city_coords[city_selected], zoom_start=13)
folium.Marker(
    location=[poi_selected["lat"], poi_selected["lng"]],
    popup=f"<b>{poi_selected['nome']}</b>",
    tooltip=poi_selected["nome"],
    icon=folium.Icon(color='red', icon='star')
).add_to(mappa)

# Query hotel vicini al POI
df_vicini = query_manager.hotel_vicini_a_punto(poi_selected["lat"], poi_selected["lng"], raggio_km=radius_km)
df_vicini_pd = df_vicini.toPandas()

# Aggiungi i marker degli hotel trovati
if not df_vicini_pd.empty:
    for _, row in df_vicini_pd.iterrows():
        folium.Marker(
            location=[row["lat"], row["lng"]],
            popup=f"<b>{row['Hotel_Name']}</b><br>{row['Hotel_City']}<br>Distanza: {row['distanza']:.2f} km",
            tooltip=row["Hotel_Name"],
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(mappa)

st_folium(mappa, width=900, height=500)

st.markdown(
    """
    <style>
    .element-container:has(.folium-map) + div { margin-top: -2.5em !important; }
    </style>
    """,
    unsafe_allow_html=True
)


st.subheader(f"Hotel entro {radius_km} km da {poi_selected['nome']}")
if not df_vicini_pd.empty:
    st.dataframe(df_vicini_pd)
else:
    st.info("Nessun hotel trovato nel raggio selezionato.")
