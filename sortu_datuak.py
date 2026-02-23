"""
Euskadiko udalerrien GeoJSON fitxategia sortu datu estatistikoekin.
Benetako muga administratiboak erabiltzen ditu (montera34/airbnbeuskadi),
geometria sinplifikatuekin eta prezio-datu errealistekin.
"""

import json
import math
import random
import sys

random.seed(42)

# Udalerri ezagunen prezio-datuak (errealistak, 2024ko datuetan oinarrituta)
# izena_lower -> (euro_m2, salmenta_prezioa_aprox, errenta_hileko)
PREZIO_EZAGUNAK = {
    "bilbao": (3200, 272000, 1050),
    "donostia / san sebastián": (4500, 405000, 1350),
    "donostia-san sebastián": (4500, 405000, 1350),
    "donostia/san sebastián": (4500, 405000, 1350),
    "vitoria-gasteiz": (2300, 195000, 780),
    "barakaldo": (2400, 192000, 850),
    "getxo": (3500, 332000, 1100),
    "irun": (2900, 246000, 900),
    "portugalete": (2600, 208000, 850),
    "santurtzi": (2200, 176000, 780),
    "basauri": (2300, 184000, 800),
    "errenteria": (2700, 216000, 880),
    "leioa": (3100, 279000, 1000),
    "durango": (2500, 200000, 820),
    "galdakao": (2400, 192000, 800),
    "eibar": (2200, 176000, 750),
    "zarautz": (3400, 306000, 1100),
    "hernani": (2800, 224000, 900),
    "bermeo": (2300, 184000, 780),
    "tolosa": (2600, 208000, 850),
    "hondarribia": (3800, 342000, 1200),
    "sestao": (2100, 168000, 750),
    "erandio": (2500, 200000, 830),
    "sopela": (3200, 288000, 1050),
    "gernika-lumo": (2200, 176000, 750),
    "mungia": (2300, 184000, 780),
    "arrasate/mondragón": (2100, 168000, 720),
    "bergara": (2200, 176000, 750),
    "azpeitia": (2400, 192000, 800),
    "azkoitia": (2300, 184000, 780),
    "llodio": (1900, 152000, 650),
    "laudio/llodio": (1900, 152000, 650),
    "amurrio": (1800, 144000, 620),
    "pasaia": (2600, 208000, 850),
    "andoain": (2700, 216000, 870),
    "lasarte-oria": (2800, 224000, 890),
    "oiartzun": (3000, 270000, 950),
    "berango": (3200, 288000, 1050),
}

# Lurralde bakoitzeko batez besteko prezioak
LURRALDE_BASE = {
    "01": {"euro_m2": 2100, "errenta": 700},  # Araba
    "20": {"euro_m2": 2800, "errenta": 880},  # Gipuzkoa
    "48": {"euro_m2": 2400, "errenta": 800},  # Bizkaia
}

LURRALDE_IZENAK = {"01": "Araba", "20": "Gipuzkoa", "48": "Bizkaia"}


def simplify_coords(coords, tolerance=0.001):
    """Ramer-Douglas-Peucker line simplification."""
    if len(coords) <= 2:
        return coords

    # Find point with max distance from line between first and last
    dmax = 0
    index = 0
    start = coords[0]
    end = coords[-1]

    for i in range(1, len(coords) - 1):
        d = point_line_distance(coords[i], start, end)
        if d > dmax:
            dmax = d
            index = i

    if dmax > tolerance:
        left = simplify_coords(coords[:index + 1], tolerance)
        right = simplify_coords(coords[index:], tolerance)
        return left[:-1] + right
    else:
        return [coords[0], coords[-1]]


def point_line_distance(point, start, end):
    """Distance from point to line segment."""
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    if dx == 0 and dy == 0:
        return math.sqrt((point[0] - start[0]) ** 2 + (point[1] - start[1]) ** 2)
    t = max(0, min(1, ((point[0] - start[0]) * dx + (point[1] - start[1]) * dy) / (dx * dx + dy * dy)))
    proj_x = start[0] + t * dx
    proj_y = start[1] + t * dy
    return math.sqrt((point[0] - proj_x) ** 2 + (point[1] - proj_y) ** 2)


def simplify_geometry(geometry, tolerance=0.001):
    """Simplify a GeoJSON geometry."""
    if geometry["type"] == "Polygon":
        new_coords = []
        for ring in geometry["coordinates"]:
            simplified = simplify_coords(ring, tolerance)
            if len(simplified) >= 4:
                new_coords.append([[round(c[0], 4), round(c[1], 4)] for c in simplified])
            elif len(ring) >= 4:
                new_coords.append([[round(c[0], 4), round(c[1], 4)] for c in ring])
        if new_coords:
            return {"type": "Polygon", "coordinates": new_coords}
        return geometry

    elif geometry["type"] == "MultiPolygon":
        new_polygons = []
        for polygon in geometry["coordinates"]:
            new_rings = []
            for ring in polygon:
                simplified = simplify_coords(ring, tolerance)
                if len(simplified) >= 4:
                    new_rings.append([[round(c[0], 4), round(c[1], 4)] for c in simplified])
                elif len(ring) >= 4:
                    new_rings.append([[round(c[0], 4), round(c[1], 4)] for c in ring])
            if new_rings:
                new_polygons.append(new_rings)
        if new_polygons:
            return {"type": "MultiPolygon", "coordinates": new_polygons}
        return geometry

    return geometry


def prezioa_udalerri(izena, he_kod):
    """Get or generate price data for a municipality."""
    izena_lower = izena.lower() if izena else ""

    # Check known prices first
    if izena_lower in PREZIO_EZAGUNAK:
        euro_m2, prezioa, errenta = PREZIO_EZAGUNAK[izena_lower]
    else:
        base = LURRALDE_BASE.get(he_kod, LURRALDE_BASE["01"])
        # Add random variation (+-25%)
        faktorea = random.uniform(0.75, 1.25)
        euro_m2 = round(base["euro_m2"] * faktorea, 2)
        prezioa = round(euro_m2 * random.uniform(75, 90), 2)
        errenta = round(base["errenta"] * faktorea, 2)

    aldakuntza_sal = round(random.uniform(-3, 8), 1)
    aldakuntza_alo = round(random.uniform(0, 12), 1)

    return {
        "salmenta_euro_m2": euro_m2,
        "salmenta_prezioa": prezioa,
        "salmenta_aldakuntza_pct": aldakuntza_sal,
        "salmenta_urtea": 2024,
        "alokairu_errenta": errenta,
        "alokairu_aldakuntza_pct": aldakuntza_alo,
        "alokairu_urtea": 2024,
    }


def main():
    input_file = "/tmp/municipios-euskadi.geojson"

    print(f"Kargatzen: {input_file}", file=sys.stderr)
    with open(input_file, "r", encoding="utf-8") as f:
        geojson = json.load(f)

    features_in = geojson.get("features", [])
    print(f"Jatorrizko features: {len(features_in)}", file=sys.stderr)

    features_out = []
    for feature in features_in:
        props = feature.get("properties", {})

        # Skip partzoneriak (shared communal lands)
        if props.get("fazeria") == "1":
            continue

        iz_ofizial = props.get("iz_ofizial")
        if not iz_ofizial:
            continue

        he_kod = props.get("he_kod", "")
        lurraldea = LURRALDE_IZENAK.get(he_kod, "Ezezaguna")

        # Simplify geometry to reduce file size
        geometry = simplify_geometry(feature["geometry"], tolerance=0.0008)

        # Build new properties
        new_props = {
            "iz_ofizial": iz_ofizial,
            "udalerri_normalizatua": iz_ofizial.lower(),
            "ud_kodea": props.get("ud_kodea", ""),
            "he_kod": he_kod,
            "lurraldea": lurraldea,
        }
        new_props.update(prezioa_udalerri(iz_ofizial, he_kod))

        features_out.append({
            "type": "Feature",
            "properties": new_props,
            "geometry": geometry,
        })

    output = {
        "type": "FeatureCollection",
        "features": features_out,
    }

    out_path = "datuak/udalerri_datuak.geojson"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False)

    size_kb = len(json.dumps(output, ensure_ascii=False)) / 1024
    print(f"Sortuta: {len(features_out)} udalerri ({size_kb:.0f} KB) -> {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
