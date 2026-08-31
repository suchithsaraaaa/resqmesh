import urllib.request
import urllib.parse
import json
import time
import os

OVERPASS_URL = 'https://overpass-api.de/api/interpreter'
HEADERS = {'User-Agent': 'ResQMesh-Hyderabad-GIS-Compiler/1.0'}
GEO_DIR = os.path.join(os.path.dirname(__file__), '..', 'desktop', 'src', 'assets', 'geo')

def query_overpass(query, max_retries=3, timeout=90):
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(
                OVERPASS_URL,
                data=urllib.parse.urlencode({'data': query}).encode('utf-8'),
                headers=HEADERS
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode('utf-8')
                return json.loads(raw)
        except Exception as e:
            print(f"  Attempt {attempt + 1} failed: {e}. Retrying in 4s...")
            time.sleep(4)
    return None

def way_to_feature(el):
    geom = el.get('geometry', [])
    if len(geom) < 2:
        return None
    coords = [[round(p['lon'], 5), round(p['lat'], 5)] for p in geom]
    tags = el.get('tags', {})
    props = {
        'id': el.get('id'),
        'highway': tags.get('highway', 'road'),
    }
    if 'name' in tags:
        props['name'] = tags['name']
    if 'ref' in tags:
        props['ref'] = tags['ref']
    if 'lanes' in tags:
        props['lanes'] = tags['lanes']
    return {
        'type': 'Feature',
        'geometry': {
            'type': 'LineString',
            'coordinates': coords
        },
        'properties': props
    }

def main():
    print("=== RESQMESH AI: COMPILING 100% CONTINUOUS HYDERABAD GIS ===")
    os.makedirs(GEO_DIR, exist_ok=True)
    all_ways = {}

    # 1. Fetch Major Arterials & Highways across Full Hyderabad Metropolitan Area
    print("\n[Step 1/5] Fetching Major Arterials across Full Hyderabad Metropolitan Area [17.15, 78.15 to 17.65, 78.75]...")
    q_major = """
    [out:json][timeout:90];
    (
      way["highway"~"motorway|trunk|primary|secondary|tertiary"](17.15,78.15,17.65,78.75);
    );
    out geom;
    """
    res_major = query_overpass(q_major)
    if res_major:
        elems = res_major.get('elements', [])
        print(f"  Received {len(elems)} major arterial ways.")
        for el in elems:
            wid = el.get('id')
            if wid and wid not in all_ways:
                all_ways[wid] = el

    time.sleep(2)

    # 2. Quadrants for Local & Residential Streets
    quadrants = [
        ("Quadrant 1 (North-West: Miyapur, Kukatpally, Hafeezpet, Kondapur, Patancheru, Medchal, Balanagar)", 17.40, 78.20, 17.62, 78.47),
        ("Quadrant 2 (North-East: Secunderabad, Begumpet North, Alwal, Sainikpuri, Malkajgiri, ECIL, Uppal)", 17.40, 78.47, 17.62, 78.75),
        ("Quadrant 3 (South-West: Gachibowli, Hitec City, Madhapur, Jubilee Hills, Banjara Hills, Mehdipatnam, Attapur, Manikonda, Narsingi, Gandipet)", 17.18, 78.20, 17.40, 78.47),
        ("Quadrant 4 (South-East: Charminar, Koti, Abids, Malakpet, Dilsukhnagar, LB Nagar, Vanasthalipuram, Badangpet, Chandrayangutta)", 17.18, 78.47, 17.40, 78.75),
    ]

    for idx, (name, s, w, n, e) in enumerate(quadrants, start=2):
        print(f"\n[Step {idx}/5] Fetching {name}...")
        q_quad = f"""
        [out:json][timeout:90];
        (
          way["highway"~"residential|living_street|unclassified"]({s},{w},{n},{e});
        );
        out geom;
        """
        res_quad = query_overpass(q_quad)
        if res_quad:
            elems = res_quad.get('elements', [])
            print(f"  Received {len(elems)} residential ways.")
            for el in elems:
                wid = el.get('id')
                if wid and wid not in all_ways:
                    all_ways[wid] = el
        time.sleep(2)

    print(f"\nTotal unique Hyderabad road ways compiled: {len(all_ways)}")
    features = []
    for wid, el in all_ways.items():
        feat = way_to_feature(el)
        if feat:
            features.append(feat)

    roads_geojson = {
        "type": "FeatureCollection",
        "name": "hyderabad-roads",
        "features": features
    }

    out_roads_path = os.path.join(GEO_DIR, 'hyderabad-roads.json')
    with open(out_roads_path, 'w', encoding='utf-8') as f:
        json.dump(roads_geojson, f)
    print(f"Saved: {out_roads_path} ({len(features)} features, {os.path.getsize(out_roads_path) / (1024*1024):.2f} MB)")

    # Also sync root desktop/src/assets/hyderabad-roads.json
    root_roads_path = os.path.join(os.path.dirname(__file__), '..', 'desktop', 'src', 'assets', 'hyderabad-roads.json')
    with open(root_roads_path, 'w', encoding='utf-8') as f:
        json.dump(roads_geojson, f)
    print(f"Synced: {root_roads_path}")

    # 3. Fetch Iconic Hyderabad Water Bodies
    print("\n[Step 5/5] Fetching Hyderabad Water Bodies (Hussain Sagar, Osman Sagar, Himayat Sagar, etc.)...")
    q_water = """
    [out:json][timeout:60];
    (
      way["natural"="water"](17.20,78.20,17.65,78.70);
      relation["natural"="water"](17.20,78.20,17.65,78.70);
    );
    out geom;
    """
    res_water = query_overpass(q_water)
    water_features = []
    if res_water:
        for el in res_water.get('elements', []):
            geom = el.get('geometry', [])
            if len(geom) < 3:
                continue
            coords = [[round(p['lon'], 5), round(p['lat'], 5)] for p in geom]
            # Ensure closed polygon
            if coords[0] != coords[-1]:
                coords.append(coords[0])
            tags = el.get('tags', {})
            name = tags.get('name', '')
            water_features.append({
                'type': 'Feature',
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [coords]
                },
                'properties': {
                    'name': name,
                    'natural': 'water'
                }
            })
    water_geojson = {
        "type": "FeatureCollection",
        "name": "hyderabad-water",
        "features": water_features
    }
    out_water_path = os.path.join(GEO_DIR, 'hyderabad-water.json')
    with open(out_water_path, 'w', encoding='utf-8') as f:
        json.dump(water_geojson, f)
    print(f"Saved: {out_water_path} ({len(water_features)} water bodies, {os.path.getsize(out_water_path) / (1024*1024):.2f} MB)")

    # 4. Create Key Hyderabad Places / Neighborhoods
    places = [
        {"name": "Charminar", "type": "heritage", "lat": 17.3616, "lon": 78.4747},
        {"name": "Secunderabad", "type": "city", "lat": 17.4399, "lon": 78.4983},
        {"name": "Madhapur", "type": "suburb", "lat": 17.4483, "lon": 78.3915},
        {"name": "Hitec City", "type": "tech", "lat": 17.4435, "lon": 78.3772},
        {"name": "Gachibowli", "type": "suburb", "lat": 17.4401, "lon": 78.3489},
        {"name": "Kondapur", "type": "suburb", "lat": 17.4699, "lon": 78.3578},
        {"name": "Miyapur", "type": "suburb", "lat": 17.4968, "lon": 78.3614},
        {"name": "Hafeezpet", "type": "suburb", "lat": 17.4855, "lon": 78.3542},
        {"name": "Kukatpally", "type": "suburb", "lat": 17.4849, "lon": 78.4138},
        {"name": "Banjara Hills", "type": "suburb", "lat": 17.4156, "lon": 78.4350},
        {"name": "Jubilee Hills", "type": "suburb", "lat": 17.4319, "lon": 78.4073},
        {"name": "Begumpet", "type": "suburb", "lat": 17.4448, "lon": 78.4664},
        {"name": "Ameerpet", "type": "suburb", "lat": 17.4375, "lon": 78.4482},
        {"name": "Balanagar", "type": "suburb", "lat": 17.4697, "lon": 78.4478},
        {"name": "Jeedimetla", "type": "suburb", "lat": 17.5140, "lon": 78.4610},
        {"name": "Kompally", "type": "suburb", "lat": 17.5385, "lon": 78.4862},
        {"name": "Alwal", "type": "suburb", "lat": 17.5020, "lon": 78.5080},
        {"name": "Sainikpuri", "type": "suburb", "lat": 17.4910, "lon": 78.5520},
        {"name": "Malkajgiri", "type": "suburb", "lat": 17.4520, "lon": 78.5320},
        {"name": "Tarnaka", "type": "suburb", "lat": 17.4290, "lon": 78.5310},
        {"name": "Uppal", "type": "suburb", "lat": 17.4022, "lon": 78.5595},
        {"name": "Dilsukhnagar", "type": "suburb", "lat": 17.3685, "lon": 78.5247},
        {"name": "L.B. Nagar", "type": "suburb", "lat": 17.3457, "lon": 78.5522},
        {"name": "Vanasthalipuram", "type": "suburb", "lat": 17.3312, "lon": 78.5714},
        {"name": "Badangpet", "type": "suburb", "lat": 17.3180, "lon": 78.5280},
        {"name": "Chandrayangutta", "type": "suburb", "lat": 17.3190, "lon": 78.4720},
        {"name": "Falaknuma", "type": "heritage", "lat": 17.3310, "lon": 78.4680},
        {"name": "Bahadurpura", "type": "suburb", "lat": 17.3550, "lon": 78.4520},
        {"name": "Attapur", "type": "suburb", "lat": 17.3710, "lon": 78.4280},
        {"name": "Mehdipatnam", "type": "suburb", "lat": 17.3916, "lon": 78.4410},
        {"name": "Manikonda", "type": "suburb", "lat": 17.4020, "lon": 78.3840},
        {"name": "Narsingi", "type": "suburb", "lat": 17.3820, "lon": 78.3580},
        {"name": "Gandipet (Osman Sagar)", "type": "landmark", "lat": 17.3880, "lon": 78.3050},
        {"name": "Tellapur", "type": "suburb", "lat": 17.4580, "lon": 78.2850},
        {"name": "Patancheru", "type": "suburb", "lat": 17.5280, "lon": 78.2650},
        {"name": "Shamshabad (Airport Zone)", "type": "suburb", "lat": 17.2520, "lon": 78.4280},
        {"name": "Ghatkesar", "type": "suburb", "lat": 17.4520, "lon": 78.6850},
        {"name": "Cherlapalli", "type": "suburb", "lat": 17.4690, "lon": 78.6010},
    ]

    places_features = []
    for p in places:
        places_features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [p["lon"], p["lat"]]
            },
            "properties": {
                "name": p["name"],
                "type": p["type"]
            }
        })
    places_geojson = {
        "type": "FeatureCollection",
        "name": "hyderabad-places",
        "features": places_features
    }
    out_places_path = os.path.join(GEO_DIR, 'hyderabad-places.json')
    with open(out_places_path, 'w', encoding='utf-8') as f:
        json.dump(places_geojson, f)
    print(f"Saved: {out_places_path} ({len(places_features)} tactical places)")

    print("\n=== HYDERABAD GIS ASSETS GENERATION COMPLETE! ===")

if __name__ == '__main__':
    main()
