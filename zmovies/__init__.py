"""zmovies: a personal, read-only web view of watched movies."""
# Copyright (c) 2026 Alexios Zavras
# SPDX-License-Identifier: GPL-3.0-or-later

import os
from pathlib import Path

from flask import Flask, abort, g, render_template, request

from . import db

PAGE_SIZE = 100

MOVIE_SORTS = {"title": "m.title COLLATE NOCASE", "year": "m.year", "viewings": "viewings", "last": "last_viewed"}

DIARY_SORTS = {"date": "v.date", "title": "m.title COLLATE NOCASE", "year": "m.year"}


def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    root = Path(__file__).resolve().parent.parent
    datadir = Path(os.environ.get("ZMOVIES_DATADIR", root / "Datadir"))
    db_path = Path(app.instance_path) / "zmovies.db"

    db.build_database(db.resolve_datadir(datadir), db_path)

    def get_db():
        if "db" not in g:
            g.db = db.connect(db_path)
        return g.db

    @app.teardown_appcontext
    def close_db(_exc):
        conn = g.pop("db", None)
        if conn is not None:
            conn.close()

    def list_params(sorts: dict[str, str], default_sort: str, default_order: str):
        sort = request.args.get("sort", default_sort)
        if sort not in sorts:
            sort = default_sort
        order = request.args.get("order", default_order)
        if order not in ("asc", "desc"):
            order = default_order
        q = request.args.get("q", "").strip()
        page = max(request.args.get("page", 1, type=int), 1)
        return sort, order, q, page

    def render_list(template: str, partial: str, **context):
        if request.headers.get("HX-Request") and not request.headers.get("HX-Boosted"):
            return render_template(partial, **context)
        return render_template(template, **context)

    @app.route("/")
    def movies():
        sort, order, q, page = list_params(MOVIE_SORTS, "title", "asc")
        where, args = "", []
        if q:
            where, args = "WHERE m.title LIKE ?", [f"%{q}%"]
        conn = get_db()
        total = conn.execute(f"SELECT COUNT(*) FROM movie m {where}", args).fetchone()[0]
        rows = conn.execute(
            f"""
            SELECT m.id, m.title, m.year, m.url,
                   COUNT(v.id) AS viewings, MAX(v.date) AS last_viewed
            FROM movie m LEFT JOIN viewing v ON v.movie_id = m.id
            {where}
            GROUP BY m.id
            ORDER BY {MOVIE_SORTS[sort]} {order} NULLS LAST, m.title COLLATE NOCASE
            LIMIT ? OFFSET ?
            """,
            [*args, PAGE_SIZE, (page - 1) * PAGE_SIZE],
        ).fetchall()
        return render_list(
            "movies.html",
            "_movies_table.html",
            rows=rows,
            total=total,
            sort=sort,
            order=order,
            q=q,
            page=page,
            pages=max((total + PAGE_SIZE - 1) // PAGE_SIZE, 1),
        )

    @app.route("/diary")
    def diary():
        sort, order, q, page = list_params(DIARY_SORTS, "date", "desc")
        where, args = "", []
        if q:
            where, args = "WHERE m.title LIKE ?", [f"%{q}%"]
        conn = get_db()
        total = conn.execute(
            f"SELECT COUNT(*) FROM viewing v JOIN movie m ON m.id = v.movie_id {where}", args
        ).fetchone()[0]
        rows = conn.execute(
            f"""
            SELECT v.date, v.rewatch, v.tags, m.id AS movie_id, m.title, m.year
            FROM viewing v JOIN movie m ON m.id = v.movie_id
            {where}
            ORDER BY {DIARY_SORTS[sort]} {order} NULLS LAST, v.date DESC
            LIMIT ? OFFSET ?
            """,
            [*args, PAGE_SIZE, (page - 1) * PAGE_SIZE],
        ).fetchall()
        return render_list(
            "diary.html",
            "_diary_table.html",
            rows=rows,
            total=total,
            sort=sort,
            order=order,
            q=q,
            page=page,
            pages=max((total + PAGE_SIZE - 1) // PAGE_SIZE, 1),
        )

    @app.route("/movie/<int:movie_id>")
    def movie(movie_id: int):
        conn = get_db()
        m = conn.execute("SELECT * FROM movie WHERE id = ?", (movie_id,)).fetchone()
        if m is None:
            abort(404)
        viewings = conn.execute(
            "SELECT date, rewatch, tags FROM viewing WHERE movie_id = ? ORDER BY date", (movie_id,)
        ).fetchall()
        return render_template("movie.html", movie=m, viewings=viewings)

    return app
