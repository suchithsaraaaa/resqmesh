"""
ResQMesh AI — Offline Road Vector Tile Pyramid Generator
Partitions the 175,803 Hyderabad/Telangana road network into:
1. Fast Arterial Regional Layer (motorways, trunks, primaries, secondaries, tertiaries)
2. High-Performance Spatial Grid Tiles at Zoom 13 for local/residential streets
3. Tile manifest index for instant O(1) viewport intersection
"""

import json
import math
import os
import time

TILES_DIR = os.path.join("desktop", "public", "geo", "tiles", "13")
os.makedirs(TILES_DIR, exist_ok=True)

def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)

def num2deg(xtile, ytile, zoom):
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return (lat_deg, lon_deg)

def main():
    src_file = os.path.join("desktop", "public", "geo", "hyderabad-roads.json")
    print(f"[*] Reading {src_file}...")
    t0 = time.perf_counter()
    with open(src_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    features = data.get("features", [])
    print(f"[*] Loaded {len(features)} total features in {time.perf_counter()-t0:.2f}s")

    primary_types = {
        "motorway", "motorway_link",
        "trunk", "trunk_link",
        "primary", "primary_link",
        "secondary", "secondary_link",
        "tertiary", "tertiary_link"
    }

    arterials = []
    tile_features = {}

    for feat in features:
        hw = feat.get("properties", {}).get("highway", "")
        coords = feat.get("geometry", {}).get("coordinates", [])
        if not coords:
            continue

        # Round coordinates to 5 decimal places (~1.1m precision) for high compression & speed
        rounded_coords = [[round(pt[0], 5), round(pt[1], 5)] for pt in coords]
        feat["geometry"]["coordinates"] = rounded_coords

        if hw in primary_types:
            arterials.append(feat)
        else:
            mid_lon = sum(pt[0] for pt in rounded_coords) / len(rounded_coords)
            mid_lat = sum(pt[1] for pt in rounded_coords) / len(rounded_coords)
            tx, ty = deg2num(mid_lat, mid_lon, 13)
            key = f"{tx}_{ty}"
            if key not in tile_features:
                tile_features[key] = []
            tile_features[key].append(feat)

    # 1. Save arterials dataset
    art_path = os.path.join("desktop", "public", "geo", "hyderabad-arterials.json")
    with open(art_path, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": arterials}, f, separators=(",", ":"))
    art_sz = os.path.getsize(art_path) / (1024 * 1024)
    print(f"[+] Saved {len(arterials)} arterial features to {art_path} ({art_sz:.2f} MB)")

    # Also update desktop/src/assets/geo/hyderabad-primary-roads.json with arterials
    asset_art_path = os.path.join("desktop", "src", "assets", "geo", "hyderabad-primary-roads.json")
    with open(asset_art_path, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": arterials}, f, separators=(",", ":"))
    print(f"[+] Synced {asset_art_path}")

    # 2. Save individual Zoom 13 tiles
    manifest = {}
    for key, feats in tile_features.items():
        tx, ty = map(int, key.split("_"))
        n_lat, w_lon = num2deg(tx, ty, 13)
        s_lat, e_lon = num2deg(tx + 1, ty + 1, 13)
        manifest[key] = {
            "count": len(feats),
            "bounds": [round(w_lon, 5), round(s_lat, 5), round(e_lon, 5), round(n_lat, 5)]
        }
        tpath = os.path.join(TILES_DIR, f"{key}.json")
        with open(tpath, "w", encoding="utf-8") as f:
            json.dump({"type": "FeatureCollection", "features": feats}, f, separators=(",", ":"))

    # 3. Save manifest
    manifest_path = os.path.join("desktop", "public", "geo", "tiles", "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({"zoom": 13, "tiles": manifest}, f, separators=(",", ":"))

    print(f"[+] Successfully generated {len(tile_features)} tiles in {TILES_DIR}")
    print(f"[+] Manifest written to {manifest_path}")

if __name__ == "__main__":
    main()
