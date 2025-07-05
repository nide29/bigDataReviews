import nltk
from nltk.corpus import wordnet
from nltk import word_tokenize, pos_tag
import math
from pyspark.sql.functions import udf
from pyspark.sql.types import FloatType

import os
os.environ['NLTK_DATA'] = '/Users/alessandro/nltk_data'

#Metodo per estrarre la città da un indirizzo
def estraiCitta(indirizzo: str, country: str) -> str:
    # NB: Gli indirizzi del Regno Unito hanno un formato specifico, quindi gestiamo il caso separatamente
    if country == "United Kingdom":
        indirizzo_split = indirizzo.split(' ')
        country_index = indirizzo_split.index("Kingdom") #Troviamo la posizione
        # La città si trova generalmente prima dello stato nel formato dell'indirizzo
        city_index = country_index - 6 if "6BD" in indirizzo_split else country_index - 4
        return indirizzo_split[city_index]
    else:
        indirizzo_split = indirizzo.split(' ')
        country_index = indirizzo_split.index(country)
        city_index = country_index - 1
        return indirizzo_split[city_index]



    # Assicurati di aver scaricato i dati necessari:
    # nltk.download('punkt')
    # nltk.download('averaged_perceptron_tagger')
    # nltk.download('wordnet')

'''
def estrai_aggettivi_avverbi(text):
    """
    Estrae aggettivi e avverbi da una stringa usando NLTK e WordNet.
    Restituisce una lista di parole.
    """
    if not isinstance(text, str):
        return []

    tokens = word_tokenize(text)
    tagged = pos_tag(tokens)    # lang = 'eng'
    # JJ, JJR, JJS = aggettivi; RB, RBR, RBS = avverbi
    parole = [word for word, pos in tagged if pos.startswith('JJ') or pos.startswith('RB')]
    return parole
'''


def is_adjective_or_adverb(word):
    """
    Restituisce True se la parola è un aggettivo ('a') o un avverbio ('r') secondo WordNet.
    """
    if not isinstance(word, str) or not word:
        return False
    synsets = wordnet.synsets(word)
    return any(s.pos() in ('a', 'r') for s in synsets)


def haversine(lat1, lon1, lat2, lon2):
    """
    Calcola la distanza Haversine tra due punti (in gradi decimali).
    Restituisce la distanza in km.
    """
    R = 6371.0  # Raggio medio della Terra in km
    lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return float(R * c)

udf_haversine = udf(haversine, FloatType())
