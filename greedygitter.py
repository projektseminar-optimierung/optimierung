import math
import networkx as nx
import matplotlib.pyplot as plt


def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def generate_local_grid(lat, lon, radius_km, steps=5):
    """Erzeugt ein Gitter von Testpunkten um eine Koordinate."""
    grid = []
    # Annäherung: 1 Grad Breitengrad ~ 111km
    # Längengrad-Abstand variiert je nach Breitengrad
    lat_step = radius_km / (steps * 111)
    lon_step = radius_km / (steps * 111 * math.cos(math.radians(lat)))

    for i in range(-steps, steps + 1):
        for j in range(-steps, steps + 1):
            grid.append((lat + i * lat_step, lon + j * lon_step))
    return grid


def solve_with_grid_search(file_path):
    cities = []
    # 1. Daten einlesen [cite: 1, 2, 3, 4, 5, 6]
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('['): continue
            parts = line.split(',')
            if len(parts) >= 3:
                cities.append({
                    'name': parts[0].strip(),
                    'lat': float(parts[1].strip()),
                    'lon': float(parts[2].strip())
                })

    uncovered = set(range(len(cities)))
    selected_towers = []
    tower_configs = [
        {'radius': 50, 'cost': 2.4, 'color': 'red'},
        {'radius': 20, 'cost': 1.0, 'color': 'blue'}
    ]

    print("Berechne optimale Standorte per Gittersuche...")

    # 2. Erweiterter Greedy-Algorithmus
    while uncovered:
        best_efficiency = float('inf')
        best_tower_data = None

        for i, city in enumerate(cities):
            # Erzeuge Gitterpunkte um die Stadt (lokale Suche)
            # Wir nutzen 25km Suchradius, um die Umgebung zu scannen
            test_points = generate_local_grid(city['lat'], city['lon'], 25, steps=3)

            for p_lat, p_lon in test_points:
                for config in tower_configs:
                    covered_indices = [j for j in uncovered if haversine(
                        p_lat, p_lon, cities[j]['lat'], cities[j]['lon']
                    ) <= config['radius']]

                    if not covered_indices: continue

                    efficiency = config['cost'] / len(covered_indices)

                    if efficiency < best_efficiency:
                        best_efficiency = efficiency
                        best_tower_data = {
                            'lat': p_lat, 'lon': p_lon,
                            'type': config,
                            'covers': covered_indices,
                            'base_city': city['name']
                        }

        if best_tower_data:
            selected_towers.append(best_tower_data)
            for idx in best_tower_data['covers']:
                uncovered.remove(idx)
        else:
            break

    # 3. Visualisierung
    G = nx.Graph()
    pos = {}
    for i, c in enumerate(cities):
        G.add_node(i)
        pos[i] = (c['lon'], c['lat'])

    plt.figure(figsize=(12, 10))
    nx.draw_networkx_nodes(G, pos, node_size=15, node_color='grey', alpha=0.3)

    total_cost = 0
    for t in selected_towers:
        total_cost += t['type']['cost']
        # Zeichne den berechneten Gitterpunkt (nicht zwingend eine Stadt)
        plt.scatter(t['lon'], t['lat'], c=t['type']['color'], s=120, edgecolors='black', zorder=5)

        # Verbindungen zeichnen
        for c_idx in t['covers']:
            plt.plot([t['lon'], cities[c_idx]['lon']], [t['lat'], cities[c_idx]['lat']],
                     color=t['type']['color'], alpha=0.2, linewidth=1)

    plt.title(f"Optimiertes 6G Netz (Gitter-Greedy) - Kosten: {total_cost:.2f}")

    # Legende manuell hinzufügen
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label='50km Turm (2.4)', markerfacecolor='red', markersize=10),
        Line2D([0], [0], marker='o', color='w', label='20km Turm (1.0)', markerfacecolor='blue', markersize=10),
        Line2D([0], [0], color='grey', lw=1, label='Abdeckung', alpha=0.5)
    ]
    plt.legend(handles=legend_elements, loc='upper right')

    print(f"Gesamtkosten: {total_cost:.2f} mit {len(selected_towers)} Türmen.")
    plt.show()


if __name__ == "__main__":
    solve_with_grid_search('cities_de_50k.txt')