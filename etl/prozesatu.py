"""
ETL prozesu nagusia: datuak deskargatu, normalizatu, kalkulatu eta GeoJSON-ekin bateratu.
"""

import json
import logging
import os

import pandas as pd

from etl.config import (
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    PROCESSED_SALES_FILE,
    PROCESSED_RENTAL_FILE,
    PROCESSED_GEOJSON_FILE,
)
from etl.datuak_kargatu import (
    deskargatu_guztiak,
    kargatu_csv,
    kargatu_geojson,
)
from etl.normalizatu import normalizatu_dataframe, lurraldea_identifikatu
from etl.kalkuluak import prezio_aldakuntza, metro_koadroko_prezioa, estatistikak_kalkulatu

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Open Data Euskadiko CSV zutabe-izen ohikoenak
# Hauek egokitu behar dira benetako datuetara
EME_ZUTABEAK = {
    "municipio": "udalerria",
    "codigo_ine": "ine_kodea",
    "año": "urtea",
    "anyo": "urtea",
    "year": "urtea",
    "precio_medio": "batez_besteko_prezioa",
    "precio_m2": "euro_m2",
    "superficie_media": "batez_besteko_azalera",
}

AME_ZUTABEAK = {
    "municipio": "udalerria",
    "codigo_ine": "ine_kodea",
    "año": "urtea",
    "anyo": "urtea",
    "year": "urtea",
    "renta_media": "batez_besteko_errenta",
    "renta_m2": "errenta_m2",
}


def _berrizendatu_zutabeak(df: pd.DataFrame, mapa: dict) -> pd.DataFrame:
    """Zutabe-izenak berrizendatu, existitzen direnak soilik."""
    zutabe_izenak_lower = {z.lower().strip(): z for z in df.columns}
    berrizendaketak = {}
    for jatorrizkoa, berria in mapa.items():
        jat_lower = jatorrizkoa.lower().strip()
        if jat_lower in zutabe_izenak_lower:
            berrizendaketak[zutabe_izenak_lower[jat_lower]] = berria
    if berrizendaketak:
        df = df.rename(columns=berrizendaketak)
    return df


def _identifikatu_zutabeak(df: pd.DataFrame) -> dict:
    """
    Heuristikoki zutabe garrantzitsuenak identifikatu.
    Izenak ezberdinak izan daitezke datu-multzo bakoitzean.
    """
    zutabeak = [z.lower().strip() for z in df.columns]
    emaitza = {}

    # Udalerria identifikatu
    for kandidatua in ["udalerria", "municipio", "municipality", "nombre", "izena"]:
        if kandidatua in zutabeak:
            emaitza["udalerria"] = df.columns[zutabeak.index(kandidatua)]
            break

    # Urtea identifikatu
    for kandidatua in ["urtea", "año", "anyo", "year", "periodo"]:
        if kandidatua in zutabeak:
            emaitza["urtea"] = df.columns[zutabeak.index(kandidatua)]
            break

    # Prezioa identifikatu
    for kandidatua in ["batez_besteko_prezioa", "precio_medio", "precio", "prezioa", "price"]:
        if kandidatua in zutabeak:
            emaitza["prezioa"] = df.columns[zutabeak.index(kandidatua)]
            break

    # Euro/m2 identifikatu
    for kandidatua in ["euro_m2", "precio_m2", "prezioa_m2", "price_m2"]:
        if kandidatua in zutabeak:
            emaitza["euro_m2"] = df.columns[zutabeak.index(kandidatua)]
            break

    # Azalera identifikatu
    for kandidatua in ["batez_besteko_azalera", "superficie_media", "superficie", "azalera"]:
        if kandidatua in zutabeak:
            emaitza["azalera"] = df.columns[zutabeak.index(kandidatua)]
            break

    # Errenta identifikatu
    for kandidatua in ["batez_besteko_errenta", "renta_media", "renta", "errenta"]:
        if kandidatua in zutabeak:
            emaitza["errenta"] = df.columns[zutabeak.index(kandidatua)]
            break

    # INE kodea identifikatu
    for kandidatua in ["ine_kodea", "codigo_ine", "cod_ine", "ine", "codigo"]:
        if kandidatua in zutabeak:
            emaitza["ine_kodea"] = df.columns[zutabeak.index(kandidatua)]
            break

    return emaitza


def prozesatu_salmentak(fitxategia: str) -> pd.DataFrame:
    """
    Salmenta datuak prozesatu: kargatu, normalizatu, kalkuluak egin.

    Args:
        fitxategia: CSV fitxategiaren bidea.

    Returns:
        Prozesatutako DataFrame-a.
    """
    logger.info("=== SALMENTA DATUAK PROZESATZEN ===")

    df = kargatu_csv(fitxategia)
    df = _berrizendatu_zutabeak(df, EME_ZUTABEAK)
    zutabeak = _identifikatu_zutabeak(df)

    logger.info("Identifikatutako zutabeak: %s", zutabeak)

    # Udalerri-izenak normalizatu
    if "udalerria" in zutabeak:
        ine_zut = zutabeak.get("ine_kodea")
        df = normalizatu_dataframe(df, zutabeak["udalerria"], ine_zut)

    # Prezio-aldakuntza kalkulatu
    if "prezioa" in zutabeak and "urtea" in zutabeak:
        df = prezio_aldakuntza(df, zutabeak["prezioa"], zutabeak["urtea"])

    # Metro koadroko prezioa kalkulatu (zuzenean ez badago)
    if "euro_m2" not in zutabeak and "prezioa" in zutabeak and "azalera" in zutabeak:
        df = metro_koadroko_prezioa(df, zutabeak["prezioa"], zutabeak["azalera"])

    # Lurraldea gehitu INE kodearen bidez
    if "ine_kodea" in df.columns:
        df["lurraldea"] = df["ine_kodea"].apply(lurraldea_identifikatu)

    return df


def prozesatu_alokairuak(fitxategia: str) -> pd.DataFrame:
    """
    Alokairu datuak prozesatu: kargatu, normalizatu, kalkuluak egin.

    Args:
        fitxategia: CSV fitxategiaren bidea.

    Returns:
        Prozesatutako DataFrame-a.
    """
    logger.info("=== ALOKAIRU DATUAK PROZESATZEN ===")

    df = kargatu_csv(fitxategia)
    df = _berrizendatu_zutabeak(df, AME_ZUTABEAK)
    zutabeak = _identifikatu_zutabeak(df)

    logger.info("Identifikatutako zutabeak: %s", zutabeak)

    # Udalerri-izenak normalizatu
    if "udalerria" in zutabeak:
        ine_zut = zutabeak.get("ine_kodea")
        df = normalizatu_dataframe(df, zutabeak["udalerria"], ine_zut)

    # Errenta-aldakuntza kalkulatu
    if "errenta" in zutabeak and "urtea" in zutabeak:
        df = prezio_aldakuntza(df, zutabeak["errenta"], zutabeak["urtea"])

    # Lurraldea gehitu
    if "ine_kodea" in df.columns:
        df["lurraldea"] = df["ine_kodea"].apply(lurraldea_identifikatu)

    return df


def bateratu_geojson(geojson: dict, salmenta_df: pd.DataFrame,
                     alokairu_df: pd.DataFrame) -> dict:
    """
    GeoJSON-a salmenta eta alokairu datuekin bateratu.
    Udalerri bakoitzeko azken urteko datuak gehitzen ditu.

    Args:
        geojson: Udalerrien GeoJSON dict-a.
        salmenta_df: Prozesatutako salmenta datuak.
        alokairu_df: Prozesatutako alokairu datuak.

    Returns:
        Datuekin aberastutako GeoJSON-a.
    """
    logger.info("=== GeoJSON BATERATZEN ===")

    # Salmenta estatistikak kalkulatu (azken urtea)
    salmenta_estatistikak = {}
    if salmenta_df is not None and "udalerri_normalizatua" in salmenta_df.columns:
        sal_zutabeak = _identifikatu_zutabeak(salmenta_df)
        prezio_zut = sal_zutabeak.get("prezioa", sal_zutabeak.get("euro_m2"))

        if prezio_zut and "urtea" in sal_zutabeak:
            urtea_zut = sal_zutabeak["urtea"]
            # Azken urtea hartu
            salmenta_df[urtea_zut] = pd.to_numeric(salmenta_df[urtea_zut], errors="coerce")
            azken_urtea = salmenta_df[urtea_zut].max()
            azken_df = salmenta_df[salmenta_df[urtea_zut] == azken_urtea]

            for _, errenkada in azken_df.iterrows():
                izena = errenkada.get("udalerri_normalizatua", "")
                if izena:
                    salmenta_estatistikak[izena] = {
                        "salmenta_prezioa": _segurua(errenkada, prezio_zut),
                        "salmenta_euro_m2": _segurua(errenkada, "euro_m2"),
                        "salmenta_aldakuntza_pct": _segurua(errenkada, "prezio_aldakuntza_pct"),
                        "salmenta_urtea": int(azken_urtea) if pd.notna(azken_urtea) else None,
                    }

    # Alokairu estatistikak kalkulatu (azken urtea)
    alokairu_estatistikak = {}
    if alokairu_df is not None and "udalerri_normalizatua" in alokairu_df.columns:
        alo_zutabeak = _identifikatu_zutabeak(alokairu_df)
        errenta_zut = alo_zutabeak.get("errenta")

        if errenta_zut and "urtea" in alo_zutabeak:
            urtea_zut = alo_zutabeak["urtea"]
            alokairu_df[urtea_zut] = pd.to_numeric(alokairu_df[urtea_zut], errors="coerce")
            azken_urtea = alokairu_df[urtea_zut].max()
            azken_df = alokairu_df[alokairu_df[urtea_zut] == azken_urtea]

            for _, errenkada in azken_df.iterrows():
                izena = errenkada.get("udalerri_normalizatua", "")
                if izena:
                    alokairu_estatistikak[izena] = {
                        "alokairu_errenta": _segurua(errenkada, errenta_zut),
                        "alokairu_errenta_m2": _segurua(errenkada, "errenta_m2"),
                        "alokairu_aldakuntza_pct": _segurua(errenkada, "prezio_aldakuntza_pct"),
                        "alokairu_urtea": int(azken_urtea) if pd.notna(azken_urtea) else None,
                    }

    # GeoJSON ezaugarrietan datuak gehitu
    bateratuak = 0
    for feature in geojson.get("features", []):
        props = feature.get("properties", {})

        # Udalerriaren izena normalizatu GeoJSON-etik
        izena_raw = (
            props.get("NOMBRE_MUNICIPIO")
            or props.get("nombre")
            or props.get("izena")
            or props.get("name")
            or props.get("MUNICIPIO")
            or ""
        )

        from etl.normalizatu import normalizatu_izena
        izena = normalizatu_izena(izena_raw)

        if izena:
            props["udalerri_normalizatua"] = izena
            if izena in salmenta_estatistikak:
                props.update(salmenta_estatistikak[izena])
                bateratuak += 1
            if izena in alokairu_estatistikak:
                props.update(alokairu_estatistikak[izena])

    logger.info("GeoJSON bateratuta: %d udalerri datuekin", bateratuak)
    return geojson


def _segurua(errenkada, zutabea):
    """Balio bat segurtasunez atera errenkada batetik."""
    if zutabea and zutabea in errenkada.index:
        balioa = errenkada[zutabea]
        if pd.notna(balioa):
            try:
                return round(float(balioa), 2)
            except (ValueError, TypeError):
                return None
    return None


def gorde_emaitzak(salmenta_df: pd.DataFrame, alokairu_df: pd.DataFrame, geojson: dict):
    """Prozesatutako emaitzak diskoan gorde."""
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

    if salmenta_df is not None:
        salmenta_df.to_json(PROCESSED_SALES_FILE, orient="records", force_ascii=False, indent=2)
        logger.info("Salmenta datuak gordeta: %s", PROCESSED_SALES_FILE)

    if alokairu_df is not None:
        alokairu_df.to_json(PROCESSED_RENTAL_FILE, orient="records", force_ascii=False, indent=2)
        logger.info("Alokairu datuak gordeta: %s", PROCESSED_RENTAL_FILE)

    if geojson is not None:
        with open(PROCESSED_GEOJSON_FILE, "w", encoding="utf-8") as f:
            json.dump(geojson, f, ensure_ascii=False, indent=2)
        logger.info("GeoJSON gordeta: %s", PROCESSED_GEOJSON_FILE)


def exekutatu_etl():
    """
    ETL prozesu osoa exekutatu:
    1. Datuak deskargatu
    2. Salmentak prozesatu
    3. Alokairuak prozesatu
    4. GeoJSON-ekin bateratu
    5. Emaitzak gorde
    """
    logger.info("========================================")
    logger.info("ETL PROZESUA HASTEN")
    logger.info("========================================")

    # 1. Datuak deskargatu
    fitxategiak = deskargatu_guztiak()

    # 2. Salmentak prozesatu
    salmenta_df = None
    if fitxategiak.get("eme"):
        try:
            salmenta_df = prozesatu_salmentak(fitxategiak["eme"])
        except Exception as e:
            logger.error("Errorea salmentak prozesatzen: %s", e)

    # 3. Alokairuak prozesatu
    alokairu_df = None
    if fitxategiak.get("ame"):
        try:
            alokairu_df = prozesatu_alokairuak(fitxategiak["ame"])
        except Exception as e:
            logger.error("Errorea alokairuak prozesatzen: %s", e)

    # 4. GeoJSON kargatu eta bateratu
    geojson = None
    if fitxategiak.get("geojson"):
        try:
            geojson = kargatu_geojson(fitxategiak["geojson"])
            geojson = bateratu_geojson(geojson, salmenta_df, alokairu_df)
        except Exception as e:
            logger.error("Errorea GeoJSON bateratzen: %s", e)

    # 5. Emaitzak gorde
    gorde_emaitzak(salmenta_df, alokairu_df, geojson)

    logger.info("========================================")
    logger.info("ETL PROZESUA AMAITUTA")
    logger.info("========================================")

    return salmenta_df, alokairu_df, geojson


if __name__ == "__main__":
    exekutatu_etl()
