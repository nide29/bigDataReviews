import streamlit as st
from progettoBigData import SparkBuilder
from wordcloud import WordCloud
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Analisi delle Recensioni",
    page_icon="📝",
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
st.sidebar.markdown("- 📝 **Analisi delle Recensioni**")

@st.cache_resource
def get_query_manager():
    spark_builder = SparkBuilder()
    return spark_builder.query_manager

query_manager = get_query_manager()

st.markdown("<h1 style='text-align: center;'>📝 Analisi delle Recensioni</h1>", unsafe_allow_html=True)
st.markdown("---")

# 1. Analisi aggettivi e avverbi
st.subheader("🔤 Analisi aggettivi e avverbi nelle recensioni")
min_freq = st.slider("Frequenza minima della parola", min_value=100, max_value=5000, value=1000, step=100)
n_words = st.slider("Quante parole visualizzare?", min_value=1, max_value=100, value=20, step=1)

positive_words, negative_words = query_manager.words_score_analysis(min_frequency=min_freq)
positive_pd = positive_words.toPandas().head(n_words)
negative_pd = negative_words.toPandas().head(n_words)

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Parole positive più associate a punteggi alti:**")
    st.dataframe(positive_pd, use_container_width=True)
    st.markdown("**Word Cloud parole positive:**")
    wc_pos = WordCloud(width=400, height=200, background_color="white").generate_from_frequencies(
        dict(zip(positive_pd["word"], positive_pd["word_count"]))
    )
    fig1, ax1 = plt.subplots()
    ax1.imshow(wc_pos, interpolation="bilinear")
    ax1.axis("off")
    st.pyplot(fig1)

with col2:
    st.markdown("**Parole negative più associate a punteggi bassi:**")
    st.dataframe(negative_pd, use_container_width=True)
    st.markdown("**Word Cloud parole negative:**")
    wc_neg = WordCloud(width=400, height=200, background_color="white").generate_from_frequencies(
        dict(zip(negative_pd["word"], negative_pd["word_count"]))
    )
    fig2, ax2 = plt.subplots()
    ax2.imshow(wc_neg, interpolation="bilinear")
    ax2.axis("off")
    st.pyplot(fig2)



# 2. Tag più e meno usati
st.subheader("🏷️ Tag più e meno usati")
tag_freq = query_manager.mostAndLeastTagUsed()
tag_pd = tag_freq.toPandas()
top_tags = tag_pd.head(10)
bottom_tags = tag_pd.tail(10)

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Tag più usati:**")
    st.dataframe(top_tags, use_container_width=True)
    st.markdown("**Word Cloud tag più usati:**")
    wc_top = WordCloud(width=400, height=200, background_color="white").generate_from_frequencies(
        dict(zip(top_tags["word"], top_tags["count"]))
    )
    fig_top, ax_top = plt.subplots()
    ax_top.imshow(wc_top, interpolation="bilinear")
    ax_top.axis("off")
    st.pyplot(fig_top)

with col2:
    st.markdown("**Tag meno usati:**")
    st.dataframe(bottom_tags, use_container_width=True)
    st.markdown("**Word Cloud tag meno usati:**")
    wc_bottom = WordCloud(width=400, height=200, background_color="white").generate_from_frequencies(
        dict(zip(bottom_tags["word"], bottom_tags["count"]))
    )
    fig_bottom, ax_bottom = plt.subplots()
    ax_bottom.imshow(wc_bottom, interpolation="bilinear")
    ax_bottom.axis("off")
    st.pyplot(fig_bottom)



# 3. Analisi influenza dei tag sui punteggi
st.subheader("⭐ Influenza dei tag sui punteggi delle recensioni")
tag_influence = query_manager.tag_influence_analysis(min_count=1000)
st.dataframe(tag_influence.toPandas(), use_container_width=True)


# 4. Recensione più e meno lunga
st.subheader("📝 Recensione più e meno lunga (positive e negative)")
import pandas as pd

rec_lunghezza = query_manager.recensioni_lunghezza()
rec_lunghezza_pd = rec_lunghezza.toPandas()

# Mostra tutto il testo delle recensioni senza troncamento
pd.set_option("display.max_colwidth", None)

st.dataframe(rec_lunghezza_pd, use_container_width=True)
