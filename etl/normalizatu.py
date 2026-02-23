"""
Normalizazio-modulua: udalerrien izenak eta INE kodeak bateratzeko.
Datu-iturburu guztiak gurutzatu ahal izateko beharrezkoa.
"""

import logging
import re

import pandas as pd
from unidecode import unidecode

logger = logging.getLogger(__name__)

# Euskadiko lurralde historikoen INE kode-aurrizkiak
LURRALDE_KODEAK = {
    "01": "Araba",
    "20": "Gipuzkoa",
    "48": "Bizkaia",
}

# Udalerri-izen normalizazio taula (ohiko aldaerak)
IZEN_BALIOKIDETZAK = {
    "vitoria-gasteiz": "vitoria-gasteiz",
    "vitoria": "vitoria-gasteiz",
    "gasteiz": "vitoria-gasteiz",
    "donostia-san sebastian": "donostia-san sebastian",
    "donostia": "donostia-san sebastian",
    "san sebastian": "donostia-san sebastian",
    "bilbao": "bilbao",
    "bilbo": "bilbao",
    "irun": "irun",
    "iruñea": "irun",
    "barakaldo": "barakaldo",
    "baracaldo": "barakaldo",
    "getxo": "getxo",
    "guecho": "getxo",
    "portugalete": "portugalete",
    "santurtzi": "santurtzi",
    "santurce": "santurtzi",
    "basauri": "basauri",
    "errenteria": "errenteria",
    "renteria": "errenteria",
    "leioa": "leioa",
    "lejona": "leioa",
    "durango": "durango",
    "galdakao": "galdakao",
    "galdacano": "galdakao",
    "erandio": "erandio",
    "sestao": "sestao",
    "zarautz": "zarautz",
    "zarauz": "zarautz",
    "eibar": "eibar",
    "hernani": "hernani",
    "bermeo": "bermeo",
    "hondarribia": "hondarribia",
    "fuenterrabia": "hondarribia",
    "tolosa": "tolosa",
    "amorebieta-etxano": "amorebieta-etxano",
    "amorebieta": "amorebieta-etxano",
    "gernika-lumo": "gernika-lumo",
    "gernika": "gernika-lumo",
    "guernica": "gernika-lumo",
    "arrasate/mondragon": "arrasate/mondragon",
    "arrasate": "arrasate/mondragon",
    "mondragon": "arrasate/mondragon",
    "llodio": "llodio",
    "laudio": "llodio",
    "laudio/llodio": "llodio",
    "bergara": "bergara",
    "vergara": "bergara",
    "azpeitia": "azpeitia",
    "azkoitia": "azkoitia",
    "azcoitia": "azkoitia",
    "mungia": "mungia",
    "munguia": "mungia",
    "sopela": "sopela",
    "sopelana": "sopela",
}


def normalizatu_izena(izena: str) -> str:
    """
    Udalerriaren izena normalizatu: minuskulak, azentoak kendu, zuriuneak garbitu.

    Args:
        izena: Udalerriaren jatorrizko izena.

    Returns:
        Normalizatutako izena.
    """
    if not isinstance(izena, str):
        return ""

    # Minuskulak eta zuriuneak garbitu
    normalizatua = izena.strip().lower()

    # Azentoak kendu (unidecode)
    normalizatua = unidecode(normalizatua)

    # Zuriune bikoitzak kendu
    normalizatua = re.sub(r"\s+", " ", normalizatua)

    # Baliokidetza taulan bilatu
    if normalizatua in IZEN_BALIOKIDETZAK:
        normalizatua = IZEN_BALIOKIDETZAK[normalizatua]

    return normalizatua


def normalizatu_ine_kodea(kodea) -> str:
    """
    INE kodea normalizatu: 5 digituko formatura bihurtu.

    Args:
        kodea: INE kodea (int edo str).

    Returns:
        5 digituko INE kode normalizatua.
    """
    if pd.isna(kodea):
        return ""
    return str(int(float(str(kodea).strip()))).zfill(5)


def normalizatu_dataframe(df: pd.DataFrame, izen_zutabea: str, ine_zutabea: str = None) -> pd.DataFrame:
    """
    DataFrame baten udalerri-izenak eta INE kodeak normalizatu.

    Args:
        df: Jatorrizko DataFrame-a.
        izen_zutabea: Udalerri-izena duen zutabearen izena.
        ine_zutabea: INE kodea duen zutabearen izena (aukerakoa).

    Returns:
        Normalizatutako DataFrame-a, zutabe berri hauekin:
        - 'udalerri_normalizatua': izena normalizatua
        - 'ine_kodea': INE kode normalizatua (baldin badago)
    """
    df = df.copy()

    if izen_zutabea in df.columns:
        df["udalerri_normalizatua"] = df[izen_zutabea].apply(normalizatu_izena)
        logger.info("Udalerri-izenak normalizatuta: %d errenkada", len(df))
    else:
        logger.warning("'%s' zutabea ez da aurkitu", izen_zutabea)

    if ine_zutabea and ine_zutabea in df.columns:
        df["ine_kodea"] = df[ine_zutabea].apply(normalizatu_ine_kodea)
        logger.info("INE kodeak normalizatuta: %d errenkada", len(df))

    return df


def lurraldea_identifikatu(ine_kodea: str) -> str:
    """
    INE kodearen bidez lurralde historikoa identifikatu.

    Args:
        ine_kodea: 5 digituko INE kodea.

    Returns:
        Lurralde historikoaren izena.
    """
    if len(ine_kodea) >= 2:
        aurrizkia = ine_kodea[:2]
        return LURRALDE_KODEAK.get(aurrizkia, "Ezezaguna")
    return "Ezezaguna"
