import urllib.request
import urllib.parse
import json
import time

query = """
[out:json][timeout:60];
(
  way["highway"~"residential|living_street|unclassified"](17.30,78.30,17.55,78.55);
);
out count;
"""

req = urllib.request.Request(
    'https://overpass-api.de/api/interpreter',
    data=urllib.parse.urlencode({'data': query}).encode('utf-8'),
    headers={'User-Agent': 'ResQMesh-GIS-Compiler/1.0'}
)

try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print("Count result:", data.get('elements', []))
except Exception as e:
    print("Error:", e)
