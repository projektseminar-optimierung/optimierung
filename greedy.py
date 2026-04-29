import math


def haversine(lat1, lon1, lat2, lon2):
    """Berechnet die Entfernung zwischen zwei Punkten in km."""
    R = 6371.0  # Erdradius
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def solve_6g_coverage(file_path):
    cities = []

    # 1. Daten einlesen [cite: 1, 2, 3, 4, 5, 6]
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('['): continue

            parts = line.split(',')
            if len(parts) >= 3:
                name = parts[0].strip()
                lat = float(parts[1].strip())
                lon = float(parts[2].strip())
                cities.append({'name': name, 'lat': lat, 'lon': lon})

    uncovered = set(range(len(cities)))
    selected_towers = []
    total_cost = 0.0

    # Turm-Konfigurationen
    tower_types = [
        {'radius': 50, 'cost': 2.4, 'label': '50km Turm'},
        {'radius': 20, 'cost': 1.0, 'label': '20km Turm'}
    ]

    # 2. Greedy-Algorithmus
    while uncovered:
        best_efficiency = float('inf')
        best_tower = None

        # Teste jede Stadt als potenziellen Turmstandort
        for i, city in enumerate(cities):
            for t_type in tower_types:
                # Zähle, wie viele NOCH NICHT abgedeckte Städte dieser Turm erreichen würde
                covered_by_this = []
                for j in uncovered:
                    dist = haversine(city['lat'], city['lon'], cities[j]['lat'], cities[j]['lon'])
                    if dist <= t_type['radius']:
                        covered_by_this.append(j)

                if not covered_by_this:
                    continue

                # Effizienz = Kosten / neu abgedeckte Städte
                efficiency = t_type['cost'] / len(covered_by_this)

                if efficiency < best_efficiency:
                    best_efficiency = efficiency
                    best_tower = {
                        'location': city['name'],
                        'type': t_type['label'],
                        'cost': t_type['cost'],
                        'covers': covered_by_this
                    }

        # Den besten Turm zur Lösung hinzufügen
        if best_tower:
            selected_towers.append(best_tower)
            total_cost += best_tower['cost']
            # Entferne die nun abgedeckten Städte aus der Liste
            for idx in best_tower['covers']:
                uncovered.remove(idx)
        else:
            break

    # 3. Ergebnis ausgeben
    print(f"--- Optimierung abgeschlossen ---")
    print(f"Gesamtkosten: {total_cost:.2f}")
    print(f"Anzahl benötigter Türme: {len(selected_towers)}\n")

    for i, t in enumerate(selected_towers, 1):
        print(f"Turm {i}: {t['type']} bei {t['location']} (Kosten: {t['cost']})")


# Starte das Skript
if __name__ == "__main__":
    solve_6g_coverage('cities_de_50k.txt')