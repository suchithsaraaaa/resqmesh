import urllib.request
import urllib.parse
import json
import time

# Quadrant NW: Miyapur, Hafeezpet, Kondapur, Kukatpally, Gachibowli North, Balanagar, Patancheru
query = """
[out:json][timeout:90];
(
  way["highway"~"motorway|trunk|primary|secondary|tertiary|residential|unclassified|living_street"](17.40,78.25,17.55,78.45);
);
out geom;
"""

req = urllib.request.Request(
    'https://overpass-api.de/api/interpreter',
    data=urllib.parse.urlencode({'data': query}).encode('utf-8'),
    headers={'User-Agent': 'ResQMesh-GIS-Compiler/1.0'}
)

print("Fetching Quadrant NW...")
t0 = time.time()
try:
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        elems = data.get('elements', [])
        print(f"Quadrant NW completed in {time.time() - t0:.2f}s! Found {len(elems)} road ways.")
except Exception as e:
    print("Error:", e)
