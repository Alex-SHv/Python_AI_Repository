from database import get_connection, DB_PATH


def route_summary(db_path=DB_PATH):
    with get_connection(db_path) as conn:
        rows = conn.execute("""
            SELECT
                route,
                COUNT(*)                AS trips,
                AVG(time)               AS avg_time,
                AVG(distance)           AS avg_distance,
                AVG(actual_time)        AS avg_actual,
                AVG(actual_time - time) AS error
            FROM routes
            GROUP BY route
            ORDER BY trips DESC
        """).fetchall()
    return [dict(r) for r in rows]

def real_time(row):
    return row["avg_actual"] if row["avg_actual"] is not None else row["avg_time"]

def most_popular(summary):
    return max(summary, key=lambda r: r["trips"], default=None)


def fastest(summary):
    return min(summary, key=real_time, default=None)


def slowest(summary):
    return max(summary, key=real_time, default=None)


def print_statistics(db_path=DB_PATH):
    summary = route_summary(db_path)
    if not summary:
        print("Історія порожня.")
        return

    print("===== СТАТИСТИКА =====\n")
    for r in summary:
        actual = f"{r['avg_actual']:.1f} хв" if r["avg_actual"] is not None else "немає фактів"
        error = f"{r['error']:+.1f} хв" if r["error"] is not None else "—"
        print(r["route"])
        print(f"  проходжень:       {r['trips']}")
        print(f"  середня відстань: {r['avg_distance']:.1f} км")
        print(f"  прогноз:          {r['avg_time']:.1f} хв")
        print(f"  факт:             {actual}")
        print(f"  відхилення:       {error}\n")

    print(f"Найпопулярніший:  {most_popular(summary)['route']}")
    print(f"Найшвидший:       {fastest(summary)['route']}")
    print(f"Найповільніший:   {slowest(summary)['route']}")