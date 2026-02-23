"""Generate sample GeoJSON data for Euskadi municipalities for GitHub Pages demo."""

import json
import math
import random

random.seed(42)

# Euskadiko udalerri nagusien kokapena eta datuak
# (izena, lat, lon, biztanleria_aprox, lurraldea, he_kod)
UDALERRI_DATUAK = [
    # Bizkaia (48)
    ("Bilbao", 43.263, -2.935, 346000, "Bizkaia", "48"),
    ("Barakaldo", 43.296, -2.993, 100000, "Bizkaia", "48"),
    ("Getxo", 43.357, -3.012, 78000, "Bizkaia", "48"),
    ("Portugalete", 43.321, -3.021, 46000, "Bizkaia", "48"),
    ("Santurtzi", 43.329, -3.033, 47000, "Bizkaia", "48"),
    ("Basauri", 43.237, -2.885, 41000, "Bizkaia", "48"),
    ("Leioa", 43.330, -2.984, 31000, "Bizkaia", "48"),
    ("Durango", 43.171, -2.634, 30000, "Bizkaia", "48"),
    ("Galdakao", 43.232, -2.845, 29000, "Bizkaia", "48"),
    ("Erandio", 43.310, -2.969, 24000, "Bizkaia", "48"),
    ("Sestao", 43.310, -3.006, 27000, "Bizkaia", "48"),
    ("Bermeo", 43.422, -2.722, 17000, "Bizkaia", "48"),
    ("Amorebieta-Etxano", 43.219, -2.733, 19000, "Bizkaia", "48"),
    ("Gernika-Lumo", 43.316, -2.676, 17000, "Bizkaia", "48"),
    ("Mungia", 43.354, -2.845, 18000, "Bizkaia", "48"),
    ("Sopela", 43.381, -2.981, 13000, "Bizkaia", "48"),
    ("Arrigorriaga", 43.208, -2.895, 12000, "Bizkaia", "48"),
    ("Berango", 43.367, -2.993, 10000, "Bizkaia", "48"),
    ("Derio", 43.301, -2.879, 6000, "Bizkaia", "48"),
    ("Lekeitio", 43.363, -2.501, 7000, "Bizkaia", "48"),
    ("Ondarroa", 43.321, -2.418, 9000, "Bizkaia", "48"),
    ("Markina-Xemein", 43.271, -2.495, 5000, "Bizkaia", "48"),
    ("Zornotza", 43.194, -2.730, 8000, "Bizkaia", "48"),
    ("Zalla", 43.209, -3.131, 9000, "Bizkaia", "48"),
    ("Balmaseda", 43.195, -3.193, 8000, "Bizkaia", "48"),
    # Gipuzkoa (20)
    ("Donostia-San Sebastian", 43.320, -1.985, 188000, "Gipuzkoa", "20"),
    ("Irun", 43.339, -1.789, 63000, "Gipuzkoa", "20"),
    ("Errenteria", 43.312, -1.870, 39000, "Gipuzkoa", "20"),
    ("Zarautz", 43.284, -2.170, 23000, "Gipuzkoa", "20"),
    ("Eibar", 43.185, -2.472, 27000, "Gipuzkoa", "20"),
    ("Hernani", 43.266, -1.976, 20000, "Gipuzkoa", "20"),
    ("Hondarribia", 43.366, -1.796, 17000, "Gipuzkoa", "20"),
    ("Tolosa", 43.135, -2.080, 20000, "Gipuzkoa", "20"),
    ("Arrasate/Mondragon", 43.064, -2.491, 22000, "Gipuzkoa", "20"),
    ("Bergara", 43.119, -2.412, 15000, "Gipuzkoa", "20"),
    ("Azpeitia", 43.183, -2.266, 15000, "Gipuzkoa", "20"),
    ("Azkoitia", 43.179, -2.310, 12000, "Gipuzkoa", "20"),
    ("Pasaia", 43.327, -1.926, 16000, "Gipuzkoa", "20"),
    ("Andoain", 43.218, -2.024, 15000, "Gipuzkoa", "20"),
    ("Lasarte-Oria", 43.268, -2.020, 19000, "Gipuzkoa", "20"),
    ("Oiartzun", 43.298, -1.848, 10000, "Gipuzkoa", "20"),
    ("Ordizia", 43.055, -2.177, 10000, "Gipuzkoa", "20"),
    ("Beasain", 43.050, -2.192, 14000, "Gipuzkoa", "20"),
    ("Zumaia", 43.295, -2.252, 10000, "Gipuzkoa", "20"),
    ("Deba", 43.295, -2.351, 5500, "Gipuzkoa", "20"),
    ("Legazpi", 43.050, -2.333, 8500, "Gipuzkoa", "20"),
    ("Zumarraga", 43.080, -2.315, 10000, "Gipuzkoa", "20"),
    ("Oñati", 43.033, -2.414, 11000, "Gipuzkoa", "20"),
    # Araba (01)
    ("Vitoria-Gasteiz", 42.846, -2.673, 253000, "Araba", "01"),
    ("Llodio", 43.142, -2.964, 18000, "Araba", "01"),
    ("Amurrio", 43.053, -3.000, 10000, "Araba", "01"),
    ("Agurain/Salvatierra", 42.851, -2.392, 5000, "Araba", "01"),
    ("Zuia", 42.964, -2.851, 3000, "Araba", "01"),
    ("Ayala/Aiara", 43.028, -3.068, 3000, "Araba", "01"),
    ("Arrazua-Ubarrundia", 42.903, -2.604, 3000, "Araba", "01"),
    ("Iruña Oka/Iruña de Oca", 42.852, -2.789, 4000, "Araba", "01"),
]


def prezioa_kalkulatu(izena, bizt, lurraldea):
    """Generate realistic price per m2 based on municipality characteristics."""
    base = {"Bizkaia": 2600, "Gipuzkoa": 3200, "Araba": 2100}[lurraldea]

    if bizt > 150000:
        base *= 1.25
    elif bizt > 50000:
        base *= 1.10
    elif bizt < 10000:
        base *= 0.80

    # Well-known expensive areas
    overrides = {
        "Donostia": 4500, "Hondarribia": 3800, "Getxo": 3500,
        "Sopela": 3200, "Berango": 3200,
    }
    for key, val in overrides.items():
        if key in izena:
            base = val
            break

    base *= random.uniform(0.92, 1.08)
    return round(base, 2)


def errenta_kalkulatu(euro_m2):
    """Derive monthly rent from sale price per m2."""
    m2_factor = random.uniform(0.004, 0.006)
    return round(euro_m2 * m2_factor * 80, 2)


def poligonoa_sortu(lat, lon, tamaina=0.02):
    """Create a hexagonal polygon around the given center point."""
    puntuak = []
    for i in range(6):
        a = math.radians(60 * i + random.uniform(-8, 8))
        r = tamaina * random.uniform(0.8, 1.2)
        plat = lat + r * math.cos(a)
        plon = lon + r * math.sin(a) / math.cos(math.radians(lat))
        puntuak.append([round(plon, 5), round(plat, 5)])
    puntuak.append(puntuak[0])
    return [puntuak]


def main():
    features = []
    for izena, lat, lon, bizt, lurraldea, he_kod in UDALERRI_DATUAK:
        euro_m2 = prezioa_kalkulatu(izena, bizt, lurraldea)
        salmenta_prezioa = round(euro_m2 * random.uniform(75, 95), 2)
        errenta = errenta_kalkulatu(euro_m2)
        aldakuntza_sal = round(random.uniform(-3, 8), 1)
        aldakuntza_alo = round(random.uniform(0, 12), 1)

        tam = 0.015 + (bizt / 350000) * 0.04

        feature = {
            "type": "Feature",
            "properties": {
                "iz_ofizial": izena,
                "udalerri_normalizatua": izena.lower(),
                "he_kod": he_kod,
                "lurraldea": lurraldea,
                "biztanleria": bizt,
                "salmenta_euro_m2": euro_m2,
                "salmenta_prezioa": salmenta_prezioa,
                "salmenta_aldakuntza_pct": aldakuntza_sal,
                "salmenta_urtea": 2024,
                "alokairu_errenta": errenta,
                "alokairu_aldakuntza_pct": aldakuntza_alo,
                "alokairu_urtea": 2024,
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": poligonoa_sortu(lat, lon, tam),
            },
        }
        features.append(feature)

    geojson = {"type": "FeatureCollection", "features": features}

    with open("datuak/udalerri_datuak.geojson", "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)

    print(f"Sortuta: {len(features)} udalerri")


if __name__ == "__main__":
    main()
