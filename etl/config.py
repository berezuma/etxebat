"""
Konfigurazio fitxategia: Open Data Euskadiko datu-iturburuen URLak eta parametroak.
"""

import os

# Datu-iturruen URLak (Open Data Euskadi)
# EME: Etxebizitza Merkatuaren Estatistika - Salerosketa datuak
EME_URL = (
    "https://opendata.euskadi.eus/contenidos/estadistica/"
    "estadistica_mercado_vivienda/opendata/eme.csv"
)

# AME: Alokairu Merkatuaren Estatistika - Alokairu errealen prezioak
AME_URL = (
    "https://opendata.euskadi.eus/contenidos/estadistica/"
    "estadistica_mercado_alquiler/opendata/ame.csv"
)

# GeoJSON: Euskadiko udalerrien muga administratiboak
GEOJSON_URL = (
    "https://opendata.euskadi.eus/contenidos/ds_informes_estudios/"
    "municipios_702/opendata/municipios.geojson"
)

# Fitxategien bideak
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, "data", "processed")

# Prozesatutako fitxategien izenak
PROCESSED_SALES_FILE = os.path.join(PROCESSED_DATA_DIR, "salmenta_prozesatua.json")
PROCESSED_RENTAL_FILE = os.path.join(PROCESSED_DATA_DIR, "alokairua_prozesatua.json")
PROCESSED_GEOJSON_FILE = os.path.join(PROCESSED_DATA_DIR, "udalerri_datuak.geojson")
