"""
Backend-a: FastAPI aplikazioa Euskadiko higiezinen datuak eskaintzeko.
API endpointak udalerri-datuak eta GeoJSON geometriak itzultzen ditu.
"""

import json
import logging
import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Etxebat - Euskadiko Higiezinen Analisia",
    description="Euskadiko higiezinen merkatuaren datu-analisi tresna",
    version="1.0.0",
)

# CORS konfigurazioa (frontend-a beste zerbitzari batetik serbitzatzen bada)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Fitxategien bideak
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

GEOJSON_FILE = os.path.join(PROCESSED_DIR, "udalerri_datuak.geojson")
SALES_FILE = os.path.join(PROCESSED_DIR, "salmenta_prozesatua.json")
RENTAL_FILE = os.path.join(PROCESSED_DIR, "alokairua_prozesatua.json")


def _kargatu_json(fitxategia: str) -> list | dict | None:
    """JSON fitxategia kargatu."""
    if not os.path.exists(fitxategia):
        return None
    with open(fitxategia, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/")
async def hasiera():
    """Frontend-aren HTML fitxategia itzuli."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"mezua": "Etxebat API martxan dago", "bertsioa": "1.0.0"}


@app.get("/api/geojson")
async def geojson_lortu():
    """
    Udalerri guztien GeoJSON geometria eta estatistikak itzuli.
    Mapa koropletikoa marrazteko erabiltzen da.

    Returns:
        GeoJSON FeatureCollection bat, udalerri bakoitzeko propietateekin:
        - salmenta_prezioa: batez besteko salmenta prezioa (€)
        - salmenta_euro_m2: metro koadroko salmenta prezioa (€/m²)
        - salmenta_aldakuntza_pct: urte arteko prezio-aldakuntza (%)
        - alokairu_errenta: batez besteko alokairu errenta (€/hilabetea)
        - alokairu_aldakuntza_pct: urte arteko errenta-aldakuntza (%)
    """
    geojson = _kargatu_json(GEOJSON_FILE)
    if geojson is None:
        raise HTTPException(
            status_code=404,
            detail="GeoJSON fitxategia ez da aurkitu. Exekutatu ETL prozesua lehenik.",
        )
    return JSONResponse(content=geojson)


@app.get("/api/udalerria/{izena}")
async def udalerri_datuak(izena: str):
    """
    Udalerri baten datu estatistiko osoak itzuli.

    Args:
        izena: Udalerriaren izena (normalizatua edo jatorrizkoa).

    Returns:
        Udalerriaren salmenta eta alokairu datuak.
    """
    from etl.normalizatu import normalizatu_izena

    izena_norm = normalizatu_izena(izena)

    salmenta_datuak = _kargatu_json(SALES_FILE) or []
    alokairu_datuak = _kargatu_json(RENTAL_FILE) or []

    # Salmenta datuak bilatu
    salmenta = [
        d for d in salmenta_datuak
        if d.get("udalerri_normalizatua") == izena_norm
    ]

    # Alokairu datuak bilatu
    alokairua = [
        d for d in alokairu_datuak
        if d.get("udalerri_normalizatua") == izena_norm
    ]

    if not salmenta and not alokairua:
        raise HTTPException(
            status_code=404,
            detail=f"'{izena}' udalerriaren daturik ez da aurkitu.",
        )

    return {
        "udalerria": izena_norm,
        "salmenta": salmenta,
        "alokairua": alokairua,
    }


@app.get("/api/estatistikak")
async def estatistika_orokorrak(
    mota: str = Query("salmenta", description="Datu mota: 'salmenta' edo 'alokairua'"),
):
    """
    Estatistika orokorrak lurraldeka.

    Args:
        mota: 'salmenta' edo 'alokairua'.

    Returns:
        Lurraldeen araberako laburpen estatistikoa.
    """
    if mota == "salmenta":
        datuak = _kargatu_json(SALES_FILE) or []
    elif mota == "alokairua":
        datuak = _kargatu_json(RENTAL_FILE) or []
    else:
        raise HTTPException(status_code=400, detail="Mota ez da baliozkoa. Erabili 'salmenta' edo 'alokairua'.")

    if not datuak:
        return {"datuak": [], "guztira": 0}

    return {
        "mota": mota,
        "guztira": len(datuak),
        "datuak": datuak,
    }


@app.get("/api/udalerri-zerrenda")
async def udalerri_zerrenda():
    """Datuak dituzten udalerrien zerrenda itzuli."""
    geojson = _kargatu_json(GEOJSON_FILE)
    if geojson is None:
        return {"udalerri_zerrenda": []}

    udalerri_izenak = set()
    for feature in geojson.get("features", []):
        props = feature.get("properties", {})
        izena = props.get("udalerri_normalizatua")
        if izena:
            udalerri_izenak.add(izena)

    return {"udalerri_zerrenda": sorted(udalerri_izenak)}


# Frontend fitxategi estatikoak serbitzatu
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
