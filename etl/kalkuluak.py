"""
Kalkulu-modulua: prezioen aldakuntza (Δ%) eta metro koadroko prezioa (€/m²) kalkulatzeko.
"""

import logging

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def prezio_aldakuntza(df: pd.DataFrame, prezio_zutabea: str, urtea_zutabea: str,
                      talde_zutabea: str = "udalerri_normalizatua") -> pd.DataFrame:
    """
    Prezioen urte arteko aldakuntza portzentajea kalkulatu (Δ%).

    Formula: Δ% = ((prezio_t - prezio_t-1) / prezio_t-1) * 100

    Args:
        df: Datu-multzoa prezio eta urte zutabeekin.
        prezio_zutabea: Prezio-balioa duen zutabea.
        urtea_zutabea: Urtea duen zutabea.
        talde_zutabea: Taldekatzeko zutabea (udalerria).

    Returns:
        DataFrame-a 'prezio_aldakuntza_pct' zutabe berriarekin.
    """
    df = df.copy()

    # Zenbakizko balioak bermatu
    df[prezio_zutabea] = pd.to_numeric(df[prezio_zutabea], errors="coerce")
    df[urtea_zutabea] = pd.to_numeric(df[urtea_zutabea], errors="coerce")

    # Urtearen arabera ordenatu
    df = df.sort_values([talde_zutabea, urtea_zutabea])

    # Aurreko urtearen prezioa kalkulatu talde bakoitzean
    df["aurreko_prezioa"] = df.groupby(talde_zutabea)[prezio_zutabea].shift(1)

    # Aldakuntza portzentajea kalkulatu
    df["prezio_aldakuntza_pct"] = np.where(
        df["aurreko_prezioa"] > 0,
        ((df[prezio_zutabea] - df["aurreko_prezioa"]) / df["aurreko_prezioa"]) * 100,
        np.nan,
    )

    # Biribildu 2 dezimaletara
    df["prezio_aldakuntza_pct"] = df["prezio_aldakuntza_pct"].round(2)

    # Laguntza-zutabea kendu
    df = df.drop(columns=["aurreko_prezioa"])

    logger.info("Prezio-aldakuntza kalkulatuta: %d errenkada", df["prezio_aldakuntza_pct"].notna().sum())
    return df


def metro_koadroko_prezioa(df: pd.DataFrame, prezio_zutabea: str,
                            azalera_zutabea: str) -> pd.DataFrame:
    """
    Metro koadroko prezioa kalkulatu (€/m²).

    Formula: €/m² = prezioa / azalera

    Args:
        df: Datu-multzoa prezio eta azalera zutabeekin.
        prezio_zutabea: Prezio totala duen zutabea.
        azalera_zutabea: Azalera (m²) duen zutabea.

    Returns:
        DataFrame-a 'euro_m2' zutabe berriarekin.
    """
    df = df.copy()

    # Zenbakizko balioak bermatu
    df[prezio_zutabea] = pd.to_numeric(df[prezio_zutabea], errors="coerce")
    df[azalera_zutabea] = pd.to_numeric(df[azalera_zutabea], errors="coerce")

    # Metro koadroko prezioa kalkulatu (zero zatiketa saihestu)
    df["euro_m2"] = np.where(
        df[azalera_zutabea] > 0,
        df[prezio_zutabea] / df[azalera_zutabea],
        np.nan,
    )

    # Biribildu 2 dezimaletara
    df["euro_m2"] = df["euro_m2"].round(2)

    logger.info("€/m² kalkulatuta: %d errenkada", df["euro_m2"].notna().sum())
    return df


def estatistikak_kalkulatu(df: pd.DataFrame, prezio_zutabea: str,
                           talde_zutabea: str = "udalerri_normalizatua") -> pd.DataFrame:
    """
    Udalerri bakoitzeko estatistika deskriptiboak kalkulatu.

    Args:
        df: Datu-multzoa.
        prezio_zutabea: Prezio-balioa duen zutabea.
        talde_zutabea: Taldekatzeko zutabea.

    Returns:
        Estatistikak udalerrika.
    """
    df[prezio_zutabea] = pd.to_numeric(df[prezio_zutabea], errors="coerce")

    estatistikak = df.groupby(talde_zutabea).agg(
        batez_bestekoa=(prezio_zutabea, "mean"),
        mediana=(prezio_zutabea, "median"),
        min_prezioa=(prezio_zutabea, "min"),
        max_prezioa=(prezio_zutabea, "max"),
        kopurua=(prezio_zutabea, "count"),
    ).round(2)

    estatistikak = estatistikak.reset_index()
    logger.info("Estatistikak kalkulatuta: %d udalerri", len(estatistikak))
    return estatistikak
