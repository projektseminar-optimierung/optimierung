import networkx as nx
import matplotlib.pyplot as plt
from math import radians, cos, sin, asin, sqrt

# 1. Distanz-Funktion (einfache Version)
def distanz(lat1, lon1, lat2, lon2):
    r = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 2 * r * asin(sqrt(a))

# 2. Daten einlesen und säubern
with open('cities_de_50k.txt', 'r', encoding='utf-8') as f:
    inhalt = f.read()

# Entfernt Quellenangaben wie  und repariert Umbrüche
import re
inhalt = re.sub(r'\'', '', inhalt)
inhalt = re.sub(r'\n\s*(?=[,\d])', ' ', inhalt)

staedte = []
for zeile in inhalt.strip().split('\n'):
    teile = [t.strip() for t in zeile.split(',')]
    if len(teile) >= 3:
        # Name, Breitengrad, Längengrad
        staedte.append((teile[0], float(teile[1]), float(teile[2])))

# 3. Graph erstellen
G = nx.Graph()
for name, lat, lon in staedte:
    G.add_node(name, pos=(lon, lat))

# Kanten nur hinzufügen, wenn Distanz < 100km
for i, (n1, lat1, lon1) in enumerate(staedte):
    for n2, lat2, lon2 in staedte[i+1:]:
        d = distanz(lat1, lon1, lat2, lon2)
        if d <= 100:
            G.add_edge(n1, n2)

# 4. Zeichnen
plt.figure(figsize=(10, 12))
pos = nx.get_node_attributes(G, 'pos')

nx.draw(G, pos, with_labels=True, node_size=20, font_size=6, edge_color='gray', alpha=0.5)
plt.title("Städte-Netzwerk (Kanten bis 100km)")
plt.show()