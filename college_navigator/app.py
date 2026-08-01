"""
app.py
------
Main Flask application for the AI-Powered Smart QR-Based College
Navigation System.

Run with:
    python app.py

Before first run, seed the database:
    python database/seed.py
"""

import os
import sqlite3
import difflib
from functools import wraps

from flask import (
    Flask, render_template, jsonify, request, redirect,
    url_for, session, flash, g
)
from werkzeug.security import check_password_hash

from utils.route_engine import compute_route
from utils.qr_generator import generate_qr  # uses a lazy internal import of `qrcode`

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "college.db")
QR_DIR = os.path.join(BASE_DIR, "static", "qrcodes")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-this-in-production")


# ---------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------
def get_db():
    """Opens a new DB connection per-request, reused via Flask's `g`."""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def login_required(view_func):
    """Decorator that protects admin routes."""
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            return redirect(url_for("admin_login"))
        return view_func(*args, **kwargs)
    return wrapped


# ---------------------------------------------------------------------
# Public routes — visitor facing
# ---------------------------------------------------------------------
@app.route("/")
def index():
    db = get_db()
    locations = db.execute(
        "SELECT * FROM locations WHERE is_active = 1 ORDER BY category, name"
    ).fetchall()

    # group by category for the homepage cards
    categories = {}
    for loc in locations:
        categories.setdefault(loc["category"], []).append(loc)

    return render_template("index.html", categories=categories)


@app.route("/navigate/<int:location_id>")
def navigate(location_id):
    db = get_db()
    location = db.execute(
        "SELECT * FROM locations WHERE id = ?", (location_id,)
    ).fetchone()

    if location is None:
        flash("Location not found.")
        return redirect(url_for("index"))

    # log the visit for analytics
    source = request.args.get("source", "search")
    db.execute(
        "INSERT INTO visitor_logs (location_id, source, user_agent) VALUES (?, ?, ?)",
        (location_id, source, request.headers.get("User-Agent", "")[:255]),
    )
    db.commit()

    all_locations = db.execute(
        "SELECT id, name FROM locations WHERE is_active = 1 ORDER BY name"
    ).fetchall()

    return render_template("navigate.html", location=location, all_locations=all_locations)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    db = get_db()
    # simple directory pulled from locations that have a contact email
    contacts = db.execute(
        "SELECT name, contact, timings FROM locations WHERE contact != '-' AND contact IS NOT NULL"
    ).fetchall()
    return render_template("contact.html", contacts=contacts)


# ---------------------------------------------------------------------
# JSON APIs consumed by the frontend JavaScript
# ---------------------------------------------------------------------
@app.route("/api/locations")
def api_locations():
    db = get_db()
    q = request.args.get("q", "").strip()
    if q:
        rows = db.execute(
            "SELECT * FROM locations WHERE is_active = 1 AND name LIKE ? ORDER BY name",
            (f"%{q}%",),
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM locations WHERE is_active = 1 ORDER BY name"
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/route")
def api_route():
    """
    Computes the shortest walking route from the visitor's live GPS
    position to a destination location.

    Query params:
        lat, lng          -> visitor's current GPS coordinates
        destination_id    -> target location id

    Strategy: snap the visitor's GPS position to the nearest graph
    node, then run Dijkstra from that node to the destination's node.
    """
    try:
        user_lat = float(request.args.get("lat"))
        user_lng = float(request.args.get("lng"))
        destination_id = int(request.args.get("destination_id"))
    except (TypeError, ValueError):
        return jsonify({"error": "lat, lng and destination_id are required"}), 400

    db = get_db()
    destination = db.execute(
        "SELECT * FROM locations WHERE id = ?", (destination_id,)
    ).fetchone()
    if destination is None:
        return jsonify({"error": "destination not found"}), 404

    # find nearest graph node to the visitor's live GPS position
    nodes = db.execute("SELECT id, latitude, longitude FROM graph_nodes").fetchall()

    def sq_dist(lat1, lng1, lat2, lng2):
        return (lat1 - lat2) ** 2 + (lng1 - lng2) ** 2

    nearest_node = min(nodes, key=lambda n: sq_dist(user_lat, user_lng, n["latitude"], n["longitude"]))

    route = compute_route(DB_PATH, nearest_node["id"], destination["node_id"])
    if route is None:
        return jsonify({"error": "no route found"}), 404

    # prepend the visitor's exact GPS point so the polyline starts at them
    route["coordinates"].insert(0, [user_lat, user_lng])

    route["destination"] = {
        "id": destination["id"],
        "name": destination["name"],
        "latitude": destination["latitude"],
        "longitude": destination["longitude"],
    }
    return jsonify(route)


@app.route("/api/chatbot", methods=["POST"])
def api_chatbot():
    """
    Lightweight rule-based / fuzzy-matching chatbot.

    How it works (explained for the report / viva):
    1. The visitor's free-text message is lower-cased and split into
       keywords.
    2. We compare it against two knowledge sources:
         a) chatbot_faq table (curated Q&A + keyword tags)
         b) locations table (name, category, timings, building)
    3. `difflib.SequenceMatcher` computes a similarity ratio between
       the message and each candidate (a lightweight, dependency-free
       stand-in for NLP intent matching / cosine similarity over
       TF-IDF vectors, which is the natural upgrade path — see
       README "Future Enhancements").
    4. The highest scoring match above a confidence threshold is
       returned; otherwise a fallback message is sent.
    """
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip().lower()
    if not message:
        return jsonify({"reply": "Please type a question."})

    db = get_db()

    best_score = 0.0
    best_reply = None

    # 1) Match against curated FAQ
    for row in db.execute("SELECT question, answer, keywords FROM chatbot_faq"):
        keywords = [k.strip() for k in (row["keywords"] or "").split(",")]
        keyword_hit = any(k and k in message for k in keywords)
        ratio = difflib.SequenceMatcher(None, message, row["question"].lower()).ratio()
        score = ratio + (0.3 if keyword_hit else 0)
        if score > best_score:
            best_score = score
            best_reply = row["answer"]

    # 2) Match against live location data ("where is the library")
    for row in db.execute("SELECT name, building, floor, timings, description FROM locations"):
        name = row["name"].lower()
        if name in message or difflib.SequenceMatcher(None, message, name).ratio() > 0.55:
            reply = (f"{row['name']} is located in {row['building']} "
                     f"({row['floor']}). Timings: {row['timings']}.")
            score = 0.9  # location name hits are treated as high confidence
            if score > best_score:
                best_score = score
                best_reply = reply

    if best_reply and best_score >= 0.4:
        return jsonify({"reply": best_reply, "confidence": round(best_score, 2)})

    return jsonify({
        "reply": ("I'm not sure about that yet. Try asking about a specific "
                   "office, department, timing, or facility — or use the "
                   "search bar on the home page to navigate directly."),
        "confidence": round(best_score, 2),
    })


# ---------------------------------------------------------------------
# Admin authentication
# ---------------------------------------------------------------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        db = get_db()
        admin = db.execute(
            "SELECT * FROM admins WHERE username = ?", (username,)
        ).fetchone()

        if admin and check_password_hash(admin["password_hash"], password):
            session["admin_id"] = admin["id"]
            session["admin_username"] = admin["username"]
            return redirect(url_for("admin_dashboard"))

        flash("Invalid username or password.")

    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


# ---------------------------------------------------------------------
# Admin panel
# ---------------------------------------------------------------------
@app.route("/admin")
@login_required
def admin_dashboard():
    db = get_db()
    locations = db.execute("SELECT * FROM locations ORDER BY category, name").fetchall()

    total_visits = db.execute("SELECT COUNT(*) c FROM visitor_logs").fetchone()["c"]

    top_destinations = db.execute("""
        SELECT l.name, COUNT(v.id) as visits
        FROM visitor_logs v
        JOIN locations l ON l.id = v.location_id
        GROUP BY l.id
        ORDER BY visits DESC
        LIMIT 5
    """).fetchall()

    return render_template(
        "admin_dashboard.html",
        locations=locations,
        total_visits=total_visits,
        top_destinations=top_destinations,
    )


@app.route("/admin/location/add", methods=["POST"])
@login_required
def admin_add_location():
    db = get_db()
    db.execute(
        """INSERT INTO locations
           (name, category, building, floor, latitude, longitude, description,
            icon, timings, contact, node_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            request.form["name"], request.form["category"], request.form["building"],
            request.form["floor"], float(request.form["latitude"]), float(request.form["longitude"]),
            request.form["description"], request.form.get("icon", "bi-geo-alt-fill"),
            request.form["timings"], request.form["contact"], int(request.form["node_id"]),
        ),
    )
    db.commit()
    flash("Location added successfully.")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/location/edit/<int:location_id>", methods=["POST"])
@login_required
def admin_edit_location(location_id):
    db = get_db()
    db.execute(
        """UPDATE locations SET name=?, category=?, building=?, floor=?,
           latitude=?, longitude=?, description=?, timings=?, contact=?
           WHERE id=?""",
        (
            request.form["name"], request.form["category"], request.form["building"],
            request.form["floor"], float(request.form["latitude"]), float(request.form["longitude"]),
            request.form["description"], request.form["timings"], request.form["contact"],
            location_id,
        ),
    )
    db.commit()
    flash("Location updated.")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/location/delete/<int:location_id>", methods=["POST"])
@login_required
def admin_delete_location(location_id):
    db = get_db()
    db.execute("UPDATE locations SET is_active = 0 WHERE id = ?", (location_id,))
    db.commit()
    flash("Location deactivated.")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/qr/generate/<int:location_id>", methods=["POST"])
@login_required
def admin_generate_qr(location_id):
    db = get_db()
    location = db.execute("SELECT * FROM locations WHERE id = ?", (location_id,)).fetchone()
    if location is None:
        flash("Location not found.")
        return redirect(url_for("admin_dashboard"))

    base_url = request.form.get("base_url") or request.host_url.rstrip("/")
    filepath, target_url = generate_qr(location_id, location["name"], base_url, QR_DIR)

    db.execute(
        "INSERT INTO qr_codes (location_id, file_path, target_url) VALUES (?, ?, ?)",
        (location_id, filepath, target_url),
    )
    db.commit()
    flash(f"QR code generated for {location['name']}.")
    return redirect(url_for("admin_dashboard"))


if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print("Database not found. Run `python database/seed.py` first.")
    app.run(debug=True, host="0.0.0.0", port=5000)