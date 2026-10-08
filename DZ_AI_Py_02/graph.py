import re

LOCATIONS = {
    "A": "Центр",
    "B": "Університет",
    "C": "Лікарня",
    "D": "Парк",
    "E": "Вокзал",
    "F": "Торговий центр",
    "G": "Аеропорт"
}

ROADS = [
    ("A", "B", 4,  6,  2, 1),
    ("B", "E", 7, 11,  3, 2),
    ("E", "G", 7, 10,  2, 2),
    ("A", "D", 5,  8,  1, 1),
    ("D", "F", 6,  9,  2, 2),
    ("F", "G", 9, 14,  3, 2),
    ("B", "C", 3,  5,  1, 1),
    ("C", "G", 12, 17, 2, 3),
    ("D", "B", 3,  5,  2, 1),
    ("E", "F", 4,  6,  2, 2),
]


TRAFFIC_RANGE = (1, 5)
DIFFICULTY_RANGE = (1, 5)
CODE_PATTERN = re.compile(r"^[A-Z]$")


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _in_range(value, bounds):
    low, high = bounds
    return _is_number(value) and low <= value <= high


def validate_graph(locations=LOCATIONS, roads=ROADS):
    errors = [
        f"Код локації {code!r} має бути однією великою латинською літерою (A–Z)"
        for code in locations if not CODE_PATTERN.match(code)
    ]

    seen_pairs = {}
    connected = set()

    for i, road in enumerate(roads, start=1):
        if len(road) != 6:
            errors.append(f"Дорога #{i}: очікується 6 полів, отримано {len(road)}")
            continue

        start, end, distance, time, traffic, difficulty = road
        label = f"Дорога #{i} ({start}-{end})"

        errors += [f"{label}: локація {c!r} не існує в LOCATIONS"
                   for c in (start, end) if c not in locations]

        if start == end:
            errors.append(f"{label}: дорога веде з вершини в саму себе")

        pair = tuple(sorted((start, end)))
        if pair in seen_pairs:
            errors.append(f"{label}: дублікат, така пара вже описана в дорозі #{seen_pairs[pair]}")
        else:
            seen_pairs[pair] = i

        checks = [
            ("distance", distance, _is_number(distance) and distance > 0, "числом більше 0"),
            ("time", time, _is_number(time) and time > 0, "числом більше 0"),
            ("traffic", traffic, _in_range(traffic, TRAFFIC_RANGE),
             f"в діапазоні {TRAFFIC_RANGE[0]}–{TRAFFIC_RANGE[1]}"),
            ("difficulty", difficulty, _in_range(difficulty, DIFFICULTY_RANGE),
             f"в діапазоні {DIFFICULTY_RANGE[0]}–{DIFFICULTY_RANGE[1]}"),
        ]
        errors += [f"{label}: {name} має бути {expected}, отримано {value!r}"
                   for name, value, ok, expected in checks if not ok]

        connected.update((start, end))

    errors += [f"Локація {c!r} ізольована: до неї не веде жодна дорога"
               for c in locations if c not in connected]

    return errors


def build_graph(locations=LOCATIONS, roads=ROADS):

    errors = validate_graph(locations, roads)
    if errors:
        raise ValueError("Некоректна карта:\n  - " + "\n  - ".join(errors))

    graph = {node: {} for node in locations}

    for start, end, distance, time, traffic, difficulty in roads:
        params = {
            "distance": distance,
            "time": time,
            "traffic": traffic,
            "difficulty": difficulty,
        }
        graph[start][end] = params
        graph[end][start] = params

    return graph

GRAPH = build_graph()

def print_map(graph=GRAPH):
    print("===== КАРТА МІСТА =====\n")

    print("Локації:")
    for code, name in LOCATIONS.items():
        print(f"  {code} — {name}")

    print("\nДороги:")
    printed = set()
    for node in sorted(graph):
        for neighbor, p in sorted(graph[node].items()):
            key = tuple(sorted((node, neighbor)))
            if key in printed:
                continue
            printed.add(key)
            print(
                f"  {key[0]} — {key[1]}: "
                f"{p['distance']} км, {p['time']} хв, "
                f"затори={p['traffic']}, складність={p['difficulty']}"
            )


if __name__ == "__main__":
    errors = validate_graph()
    if errors:
        print("Знайдено помилки:")
        for e in errors:
            print(f"  - {e}")
    else:
        print("Карта коректна: помилок не знайдено.\n")
        print_map()