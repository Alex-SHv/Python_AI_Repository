from graph import LOCATIONS, GRAPH
from dijkstra import find_routes, format_path
from database import save_route, update_actual, get_all_routes
from analytics import print_statistics
from ai_module import get_recommendation

USER_TYPES = ("student", "worker", "driver")


def ask(prompt):
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return "0"


def ask_number(prompt):
    try:
        return float(ask(prompt).replace(",", "."))
    except ValueError:
        return None


def ask_route():
    start = ask("Початкова точка: ").upper()
    finish = ask("Кінцева точка: ").upper()
    if start not in LOCATIONS or finish not in LOCATIONS:
        print("Такої точки немає.\n")
        return None
    if start == finish:
        print("Початкова і кінцева точки однакові.\n")
        return None
    return start, finish


def average_traffic(path):
    values = [GRAPH[a][b]["traffic"] for a, b in zip(path, path[1:])]
    return round(sum(values) / len(values), 1)


def find_route(user_name, user_type):
    print("\nДоступні точки:", ", ".join(f"{k} — {v}" for k, v in LOCATIONS.items()))
    points = ask_route()
    if points is None:
        return

    best = find_routes(*points)["best"]
    if best is None:
        print("Маршрут не знайдено.\n")
        return

    route_id = save_route(points[0], points[1], best["path"], best["distance"],
                          best["time"], average_traffic(best["path"]),
                          user_name, user_type)

    print(f"\nНайкоротший маршрут: {format_path(best['path'])}")
    print(f"Відстань: {best['distance']} км")
    print(f"Час: {best['time']} хв")
    print(f"Записано в історію (id={route_id})\n")

def user_routes(user_name):
    return [r for r in get_all_routes() if r["user_name"] == user_name]

def add_actual(user_name):
    rows = user_routes(user_name)
    if not rows:
        print("Історія порожня. Спочатку знайдіть маршрут.\n")
        return

    print("\nОстанні маршрути:")
    for row in rows[:10]:
        print(f"  id={row['id']}  {row['route']}  прогноз {row['time']} хв")

    route_id = ask_number("Введіть id маршруту: ")
    actual_time = ask_number("Фактичний час, хв: ")
    actual_distance = ask_number("Фактична відстань, км: ")
    if None in (route_id, actual_time, actual_distance):
        print("Некоректні дані.\n")
        return

    if update_actual(int(route_id), actual_time, actual_distance):
        print("Результат збережено.\n")
    else:
        print("Запис з таким id не знайдено.\n")


def show_history(user_name):
    rows = user_routes(user_name)
    if not rows:
        print("Історія порожня. Спочатку знайдіть маршрут.\n")
        return

    print("\n===== ІСТОРІЯ МАРШРУТІВ =====")
    for row in rows:
        actual = f"{row['actual_time']} хв" if row["actual_time"] is not None else "немає"
        print(f"#{row['id']} {row['start_point']} → {row['finish_point']}  "
              f"{row['route']}  прогноз {row['time']} хв, факт {actual}")
    print()


def ai_recommendation(user_name):
    points = ask_route()
    if points is None:
        return

    result = find_routes(*points)
    best = result["best"]
    if best is None:
        print("Маршрут не знайдено.\n")
        return

    rec = get_recommendation(best, result["alternatives"], user_name)

    print(f"\nDijkstra: {format_path(best['path'])}, {best['distance']} км, {best['time']} хв")
    print(f"Аналіз: {rec['analysis']}")
    print(f"Рекомендований маршрут: {rec['route'].replace(',', ' → ')}")
    print(f"Причина: {rec['reason']}")
    print(f"Джерело: {rec['source']}, історія: {rec['history']}\n")


def choose_user():
    name = ask("Ваше ім'я: ") or "guest"
    print("Тип користувача: 1 — student, 2 — worker, 3 — driver")
    choice = ask("Оберіть (1-3): ")
    user_type = USER_TYPES[int(choice) - 1] if choice in ("1", "2", "3") else "student"
    return name, user_type


def main():
    print("Вітаємо в AI-навігаторі!\n")
    user_name, user_type = choose_user()

    while True:
        print("\n===== AI NAVIGATOR =====")
        print("1. Знайти маршрут")
        print("2. Додати результат проходження")
        print("3. Історія маршрутів")
        print("4. Статистика")
        print("5. AI-рекомендація")
        print("0. Вихід")

        choice = ask("Ваш вибір: ")

        if choice == "1":
            find_route(user_name, user_type)
        elif choice == "2":
            add_actual(user_name)
        elif choice == "3":
            show_history(user_name)
        elif choice == "4":
            print()
            print_statistics()
        elif choice == "5":
            ai_recommendation(user_name)
        elif choice == "0":
            print("До побачення!")
            break
        else:
            print("Невірний вибір, спробуйте ще раз.")


if __name__ == "__main__":
    main()