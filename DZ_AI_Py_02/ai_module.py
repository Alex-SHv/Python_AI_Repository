import json
import os
import urllib.request

from database import get_all_routes

MIN_TRIPS = 10
MODEL = "claude-haiku-5-5"
API_URL = "https://api.anthropic.com/v1/messages"


def get_stats(user_name=None):
    sums = {}
    for row in get_all_routes():
        if row["actual_time"] is None:
            continue
        if user_name and row["user_name"] != user_name:
            continue
        s = sums.setdefault(row["route"], {"trips": 0, "actual": 0.0, "forecast": 0.0})
        s["trips"] += 1
        s["actual"] += row["actual_time"]
        s["forecast"] += row["time"]

    return {
        route: {
            "trips": s["trips"],
            "avg_actual": s["actual"] / s["trips"],
            "avg_forecast": s["forecast"] / s["trips"],
        }
        for route, s in sums.items()
    }


def enough_data(stats, route):
    return route in stats and stats[route]["trips"] >= MIN_TRIPS


def analyze(route, stats):
    if not enough_data(stats, route):
        n = stats.get(route, {}).get("trips", 0)
        return f"Маршрут {route}: даних недостатньо ({n} з {MIN_TRIPS} поїздок)."

    s = stats[route]
    extra = (s["avg_actual"] - s["avg_forecast"]) / s["avg_forecast"] * 100
    if extra > 0:
        return (f"Маршрут {route} займає більше часу, ніж прогнозує алгоритм: "
                f"в середньому на {extra:.0f}% довше. Рекомендується закладати запас часу.")
    return f"Маршрут {route} зазвичай проходить за прогнозом або швидше."


def rule_decision(best, alternatives, stats):
    best_route = ",".join(best["path"])
    if not enough_data(stats, best_route):
        return {"choice": "keep", "route": best_route,
                "reason": "Даних для порівняння ще недостатньо, лишаємо найкоротший маршрут."}

    best_avg = stats[best_route]["avg_actual"]
    faster = [a for a in alternatives
              if enough_data(stats, ",".join(a["path"]))
              and stats[",".join(a["path"])]["avg_actual"] < best_avg]

    if not faster:
        return {"choice": "keep", "route": best_route,
                "reason": "Жодна альтернатива за історією не швидша."}

    alt = min(faster, key=lambda a: stats[",".join(a["path"])]["avg_actual"])
    alt_route = ",".join(alt["path"])
    diff = best_avg - stats[alt_route]["avg_actual"]
    return {"choice": "alternative", "route": alt_route,
            "reason": (f"Маршрут {alt_route} на {alt['distance'] - best['distance']:.0f} км довший, "
                       f"але за історією в середньому швидший на {diff:.0f} хв.")}


def ask_llm(prompt):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    body = json.dumps({
        "model": MODEL,
        "max_tokens": 300,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    request = urllib.request.Request(API_URL, data=body, method="POST", headers={
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    })
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read())["content"][0]["text"]
    except Exception:
        return None


def build_prompt(best, alternatives, stats):
    lines = ["Ти радник навігатора. Обери маршрут на основі історії фактичного часу.",
             "Відповідай ТІЛЬКИ JSON без markdown: "
             '{"choice": "keep" або "alternative", "route": "A,B,E,G", "reason": "коротко"}.',
             "Пояснення українською. Враховуй лише маршрути з поїздками з фактом.",
             "", f"Найкоротший (Dijkstra): {','.join(best['path'])}, "
                 f"{best['distance']} км, прогноз {best['time']} хв."]
    for alt in alternatives:
        key = ",".join(alt["path"])
        s = stats.get(key)
        history = (f"{s['trips']} поїздок, середній факт {s['avg_actual']:.0f} хв"
                   if s else "немає історії")
        lines.append(f"Альтернатива: {key}, {alt['distance']} км, прогноз {alt['time']} хв; {history}.")
    return "\n".join(lines)


def parse_llm_answer(text, allowed_routes):
    try:
        data = json.loads(text.strip().strip("`").removeprefix("json").strip())
        if data.get("choice") in ("keep", "alternative") and data.get("route") in allowed_routes:
            return {"choice": data["choice"], "route": data["route"],
                    "reason": str(data.get("reason", ""))}
    except (AttributeError, ValueError, TypeError):
        pass
    return None


def get_recommendation(best, alternatives, user_name=None):
    best_route = ",".join(best["path"])
    personal = get_stats(user_name) if user_name else {}
    stats = personal if enough_data(personal, best_route) else get_stats()
    source = "персональна історія" if stats is personal else "загальна історія"

    allowed = [best_route] + [",".join(a["path"]) for a in alternatives]
    answer = ask_llm(build_prompt(best, alternatives, stats))
    decision = parse_llm_answer(answer, allowed) if answer else None

    if decision is None:
        decision = rule_decision(best, alternatives, stats)
        decision["source"] = "правило (AI недоступний)"
    else:
        decision["source"] = "AI"

    decision["history"] = source
    decision["analysis"] = analyze(best_route, stats)
    return decision