import urllib.request
import urllib.parse
import json
import time

query = """
[out:json][timeout:30];
(
  way["natural"="water"](17.20,78.20,17.65,78.70);
  relation["natural"="water"](17.20,78.20,17.65,78.70);
);
out geom;
"""

req = urllib.request.Request(
    'https://overpass-api.de/api/interpreter',
    data=urllib.parse.urlencode({'data': query}).encode('utf-8'),
    headers={'User-Agent': 'ResQMesh-GIS-Compiler/1.0'}
)

print("Fetching Hyderabad water bodies...")
t0 = time.time()
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        elems = data.get('elements', [])
        print(f"Water bodies completed in {time.time() - t0:.2f}s! Found {len(elems)} water features.")
except Exception as e:
    print("Error:", e)
