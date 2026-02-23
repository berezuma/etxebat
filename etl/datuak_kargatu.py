"""
Datuen karga-modulua: CSV/JSON/GeoJSON fitxategiak deskargatu eta kargatzeko.
Open Data Euskadiko datu-iturriak erabiltzen ditu.
"""

import os
import logging
import time

import pandas as pd
import requests

from etl.config import (
    EME_URL,
    AME_URL,
    GEOJSON_URL,
    RAW_DATA_DIR,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

MAX_RETRIES = 3
BACKOFF_SECONDS = 2


def _deskargatu(url: str, helburua: str) -> str:
    """
    URL batetik fitxategia deskargatu eta lokalean gorde.

    Args:
        url: Datu-iturriaren URLa.
        helburua: Fitxategiaren helburu-bidea.

    Returns:
        Gordetako fitxategiaren bidea.

    Raises:
        requests.HTTPError: Eskaera arrakastatsu ez bada.
    """
    os.makedirs(os.path.dirname(helburua), exist_ok=True)

    for saiakera in range(MAX_RETRIES):
        try:
            logger.info("Deskargatzen: %s", url)
            erantzuna = requests.get(url, timeout=60)
            erantzuna.raise_for_status()

            with open(helburua, "wb") as f:
                f.write(erantzuna.content)

            logger.info("Gordeta: %s (%.1f KB)", helburua, len(erantzuna.content) / 1024)
            return helburua
        except requests.RequestException as e:
            logger.warning("Errorea deskargatzen (%d/%d): %s", saiakera + 1, MAX_RETRIES, e)
            if saiakera < MAX_RETRIES - 1:
                time.sleep(BACKOFF_SECONDS * (saiakera + 1))
            else:
                raise


def deskargatu_eme() -> str:
    """Etxebizitza Merkatuaren Estatistika (salmenta) datuak deskargatu."""
    return _deskargatu(EME_URL, os.path.join(RAW_DATA_DIR, "eme.csv"))


def deskargatu_ame() -> str:
    """Alokairu Merkatuaren Estatistika datuak deskargatu."""
    return _deskargatu(AME_URL, os.path.join(RAW_DATA_DIR, "ame.csv"))


def deskargatu_geojson() -> str:
    """Euskadiko udalerrien GeoJSON fitxategia deskargatu."""
    return _deskargatu(GEOJSON_URL, os.path.join(RAW_DATA_DIR, "udalerri_mugak.geojson"))


def kargatu_csv(fitxategia: str, kodeketa: str = "latin-1") -> pd.DataFrame:
    """
    CSV fitxategia DataFrame batean kargatu.

    Args:
        fitxategia: CSV fitxategiaren bidea.
        kodeketa: Fitxategiaren karaktere-kodeketa.

    Returns:
        Kargatutako DataFrame-a.
    """
    logger.info("CSV kargatzen: %s", fitxategia)
    try:
        df = pd.read_csv(fitxategia, encoding=kodeketa, sep=";")
    except UnicodeDecodeError:
        logger.info("latin-1 kodeketarekin saiatzen...")
        df = pd.read_csv(fitxategia, encoding="latin-1", sep=";")

    # Zutabe-izenak garbitu
    df.columns = df.columns.str.strip()
    logger.info("Kargatuta: %d errenkada x %d zutabe", len(df), len(df.columns))
    return df


def kargatu_geojson(fitxategia: str) -> dict:
    """
    GeoJSON fitxategia dict gisa kargatu.

    Args:
        fitxategia: GeoJSON fitxategiaren bidea.

    Returns:
        GeoJSON edukia dict formatuan.
    """
    import json

    logger.info("GeoJSON kargatzen: %s", fitxategia)
    with open(fitxategia, "r", encoding="utf-8") as f:
        geojson = json.load(f)
    logger.info("Kargatuta: %d ezaugarri", len(geojson.get("features", [])))
    return geojson


def deskargatu_guztiak() -> dict:
    """
    Datu-iturburu guztiak deskargatu.

    Returns:
        Deskargatutako fitxategien bideak dict formatuan.
    """
    emaitzak = {}
    for izena, funtzioa in [
        ("eme", deskargatu_eme),
        ("ame", deskargatu_ame),
        ("geojson", deskargatu_geojson),
    ]:
        try:
            emaitzak[izena] = funtzioa()
        except Exception as e:
            logger.error("Ezin izan da '%s' deskargatu: %s", izena, e)
            emaitzak[izena] = None
    return emaitzak
