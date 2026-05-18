import math


# --- 1. DATEN EINLESEN ---
def load_cities(filepath):
    cities_dict = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) == 3:
                    name = parts[0].strip()
                    lat = float(parts[1].strip())
                    lon = float(parts[2].strip())
                    cities_dict[name] = (lat, lon)
    except FileNotFoundError:
        print(f"Fehler: Datei {filepath} nicht gefunden.")
    return cities_dict


# --- 2. KOSTENFUNKTION c(r) ---
def get_cost(r):
    if 5 <= r < 20:
        return (
                    0.00003898883009994121 * r ** 3 - 0.0005848324514991181 * r ** 2 + 0.000818342151675485 * r + 0.9056554967666078)
    elif 20 <= r < 35:
        return (
                    -0.00004679600235155791 * r ** 3 + 0.004562257495590829 * r ** 2 - 0.10212345679012345 * r + 1.591934156378601)
    elif 35 <= r < 50:
        return (
                    0.00005930629041740153 * r ** 3 - 0.006578483245149912 * r ** 2 + 0.2878024691358025 * r - 2.957201646090535)
    elif 50 <= r <= 100:
        return (
                    -0.00001544973544973545 * r ** 3 + 0.004634920634920635 * r ** 2 - 0.27286772486772487 * r + 6.387301587301588)
    return float('inf')


# --- 3. HAVERSINE DISTANZ ---
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


# --- 4. HONEYCOMB GRID ---
def generate_honeycomb_grid(cities_list, target_points=800):
    lats, lons = [c[0] for c in cities_list.values()], [c[1] for c in cities_list.values()]
    min_lat, max_lat, min_lon, max_lon = min(lats) - 0.2, max(lats) + 0.2, min(lons) - 0.2, max(lons) + 0.2
    area_deg = (max_lat - min_lat) * (max_lon - min_lon)
    step_size = math.sqrt(area_deg / target_points)

    grid_points, row = [], 0
    curr_lat = min_lat
    while curr_lat <= max_lat:
        offset = 0.5 * step_size if row % 2 else 0
        curr_lon = min_lon + offset
        while curr_lon <= max_lon:
            if any(haversine(curr_lat, curr_lon, clat, clon) <= 100 for clat, clon in cities_list.values()):
                grid_points.append((curr_lat, curr_lon))
            curr_lon += step_size
        curr_lat += step_size * 0.866
        row += 1
    return grid_points


# --- 5. LAGRANGE-SUBGRADIENTEN-SOLVER ---
def solve_lagrangian_subgradient(cities_list, grid_to_city_dists, r1, r2, max_iters=15):
    cities = list(cities_list.keys())
    allowed_radii = sorted(list(set([r1, r2])))
    lambda_mu = {c: 0.1 for c in cities}

    best_cost = float('inf')
    best_towers = []

    for iteration in range(max_iters):
        uncovered = set(cities)
        current_towers = []
        current_cost = 0

        while uncovered:
            best_score = -1
            best_t = None

            for g_idx, dists in grid_to_city_dists.items():
                for r in allowed_radii:
                    if r not in dists: continue
                    newly_covered = [c for c in dists[r] if c in uncovered]
                    if not newly_covered: continue

                    urgency_sum = sum(lambda_mu[c] for c in newly_covered)
                    score = urgency_sum / get_cost(r)

                    if score > best_score:
                        best_score = score
                        best_t = {'g_idx': g_idx, 'r': r, 'cities': dists[r], 'newly': newly_covered,
                                  'cost': get_cost(r)}

            if not best_t: break

            current_towers.append(best_t)
            current_cost += best_t['cost']
            for c in best_t['newly']:
                uncovered.remove(c)

        if not uncovered and current_cost < best_cost:
            best_cost = current_cost
            best_towers = current_towers

        coverage_counts = {c: 0 for c in cities}
        for t in current_towers:
            for c in t['cities']:
                coverage_counts[c] += 1

        for c in cities:
            subgradient = 1 - coverage_counts[c]
            step_size = 0.5 / (iteration + 1)
            lambda_mu[c] = max(0.01, lambda_mu[c] + step_size * subgradient)

    return best_towers, best_cost


# --- NEU: FUNKTION ZUM EXPORTIEREN ALS TXT FILE ---
def save_towers_to_txt(towers, grid_points, output_filepath="tuerme_ausgabe.txt"):
    try:
        with open(output_filepath, 'w', encoding='utf-8') as f:
            # Header schreiben
            f.write("lat,lon,radius\n")
            for t in towers:
                # Koordinaten über den Gitterpunkt-Index (g_idx) auflösen
                pos = grid_points[t['g_idx']]
                lat = pos[0]
                lon = pos[1]
                radius = t['r']
                # Mit 6 Dezimalstellen präzise abspeichern
                f.write(f"{lat:.6f},{lon:.6f},{radius}\n")
        print(f"🎉 Daten erfolgreich in '{output_filepath}' exportiert!")
    except Exception as e:
        print(f"Fehler beim Schreiben der Exportdatei: {e}")


# --- 6. HAUPTPROGRAMM ---
if __name__ == "__main__":
    print("=" * 60)
    print("   ZWEI-RADIEN OPTIMIERER (SUBGRADIENTENVERFAHREN 2.0)")
    print("=" * 60)

    cities_data = load_cities('cities_de_50k.txt')

    if cities_data:
        grid = generate_honeycomb_grid(cities_data, target_points=500)
        print(f"Honeycomb-Grid mit {len(grid)} Punkten generiert.")

        print("Baue Distanz-Matrix auf (Pre-Caching)...")
        grid_to_city_dists = {g_idx: {} for g_idx in range(len(grid))}
        for g_idx, pt in enumerate(grid):
            raw_dists = [(c, haversine(pt[0], pt[1], coords[0], coords[1])) for c, coords in cities_data.items()]
            for r in range(5, 101):
                grid_to_city_dists[g_idx][r] = [c for c, d in raw_dists if d <= r]

        print("\nStarte globale Radien-Optimierung via Lagrange-Gewichtung...")
        best_overall_cost = float('inf')
        final_r1, final_r2 = 20, 50
        final_towers = []

        for test_r1 in range(5, 100, 2):
            for test_r2 in range(5, 100, 2):
                towers, cost = solve_lagrangian_subgradient(cities_data, grid_to_city_dists, test_r1, test_r2)

                if 0 < cost < best_overall_cost:
                    best_overall_cost = cost
                    final_r1 = test_r1
                    final_r2 = test_r2
                    final_towers = towers
                print(f" Prüfe Paar: {test_r1}km / {test_r2}km | Aktuelles Minimum: {best_overall_cost:.2f}  ",
                      end='\r')

        print(f"\n\n" + "=" * 55)
        print("🎉 SUBGRADIENTEN-OPTIMIERUNG ERFOLGREICH!")
        print(f"Optimales Paar: r1 = {final_r1} km, r2 = {final_r2} km")
        print(f"Mathematisch minimierte Gesamtkosten: {best_overall_cost:.4f}")
        print(f"Anzahl benötigter Türme: {len(final_towers)}")
        print("=" * 55)

        # --- NEUER GEÄNDERTER AUFRUF ---
        save_towers_to_txt(final_towers, grid, "solution.txt")