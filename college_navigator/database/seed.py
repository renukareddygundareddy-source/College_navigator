"""
database/seed.py
-----------------
Populates a fresh SQLite database with:
  1. The schema (from schema.sql)
  2. A sample campus path-network (graph_nodes + graph_edges)
  3. Sample locations, each linked to its nearest graph node
  4. A default admin account (username: admin / password: admin123)
  5. A starter chatbot FAQ knowledge base

Run this once before starting the Flask app:
    python database/seed.py

NOTE: Coordinates below are a fictional campus laid out on a simple
grid around a reference point so the demo works out of the box. In a
real deployment, replace them with your campus's actual GPS
coordinates (walk the campus with a phone GPS app, or use satellite
imagery in Google My Maps / OpenStreetMap's iD editor to plot nodes).
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "college.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")

# Reference point (fictional "College Main Gate") — change to your campus
ORIGIN_LAT = 16.3067
ORIGIN_LNG = 80.4365


def build_database():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    with open(SCHEMA_PATH, "r") as f:
        cur.executescript(f.read())

    # -----------------------------------------------------------------
    # 1. Graph nodes (path network / walkway junctions)
    # Small offsets simulate a real campus layout in degrees lat/lng.
    # -----------------------------------------------------------------
    nodes = [
        ("Main Gate",        ORIGIN_LAT,          ORIGIN_LNG),
        ("Central Junction",  ORIGIN_LAT + 0.0010, ORIGIN_LNG + 0.0005),
        ("Academic Block Path", ORIGIN_LAT + 0.0020, ORIGIN_LNG + 0.0005),
        ("Library Path",      ORIGIN_LAT + 0.0020, ORIGIN_LNG + 0.0015),
        ("Hostel Path",       ORIGIN_LAT + 0.0010, ORIGIN_LNG - 0.0010),
        ("Sports Path",       ORIGIN_LAT + 0.0005, ORIGIN_LNG + 0.0020),
        ("Admin Block Path",  ORIGIN_LAT + 0.0005, ORIGIN_LNG - 0.0005),
        ("Canteen Path",      ORIGIN_LAT + 0.0015, ORIGIN_LNG - 0.0002),
    ]
    cur.executemany(
        "INSERT INTO graph_nodes (label, latitude, longitude) VALUES (?, ?, ?)",
        nodes,
    )

    def haversine(lat1, lon1, lat2, lon2):
        import math
        R = 6371000
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = (math.sin(dphi / 2) ** 2 +
             math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
        return 2 * R * math.asin(min(1, a ** 0.5))

    node_coords = {i + 1: (n[1], n[2]) for i, n in enumerate(nodes)}

    # Edges describing which junctions are physically connected by a
    # walkway (id references are 1-indexed insert order above)
    edge_pairs = [
        (1, 2), (2, 3), (3, 4), (2, 6), (2, 5), (2, 7), (5, 7), (7, 8), (8, 3),
    ]
    edges = []
    for a, b in edge_pairs:
        lat1, lon1 = node_coords[a]
        lat2, lon2 = node_coords[b]
        dist = round(haversine(lat1, lon1, lat2, lon2), 1)
        edges.append((a, b, dist))

    cur.executemany(
        "INSERT INTO graph_edges (node_a_id, node_b_id, distance_m) VALUES (?, ?, ?)",
        edges,
    )

    # -----------------------------------------------------------------
    # 2. Locations — each tied to the nearest graph node (node_id)
    # -----------------------------------------------------------------
    locations = [
        ("Central Library", "Academic", "Block C", "Ground & 1st Floor",
         ORIGIN_LAT + 0.0021, ORIGIN_LNG + 0.0016,
         "Central library with reading halls, digital section and journals.",
         "bi-book-half", "8:00 AM - 8:00 PM", "library@college.edu", 4),

        ("Administrative Block", "Admin", "Block A", "Ground Floor",
         ORIGIN_LAT + 0.0006, ORIGIN_LNG - 0.0006,
         "Main administrative office for fees, records and certificates.",
         "bi-building", "9:30 AM - 5:00 PM", "admin@college.edu", 7),

        ("Principal Office", "Admin", "Block A", "1st Floor",
         ORIGIN_LAT + 0.0007, ORIGIN_LNG - 0.0007,
         "Office of the Principal.", "bi-person-badge",
         "10:00 AM - 1:00 PM", "principal@college.edu", 7),

        ("Admission Office", "Admin", "Block A", "Ground Floor",
         ORIGIN_LAT + 0.0005, ORIGIN_LNG - 0.0004,
         "New admissions and enquiries.", "bi-file-earmark-person",
         "9:30 AM - 4:30 PM", "admissions@college.edu", 7),

        ("Examination Cell", "Admin", "Block A", "2nd Floor",
         ORIGIN_LAT + 0.0006, ORIGIN_LNG - 0.0005,
         "Handles exam schedules, hall tickets and results.",
         "bi-file-earmark-check", "10:00 AM - 4:00 PM", "exams@college.edu", 7),

        ("Computer Labs", "Academic", "Block B", "2nd Floor",
         ORIGIN_LAT + 0.0019, ORIGIN_LNG + 0.0004,
         "CSE / IT department computer laboratories.",
         "bi-pc-display", "9:00 AM - 5:00 PM", "cse@college.edu", 3),

        ("Science Labs", "Academic", "Block B", "1st Floor",
         ORIGIN_LAT + 0.0018, ORIGIN_LNG + 0.0004,
         "Physics & Chemistry laboratories.", "bi-flask",
         "9:00 AM - 5:00 PM", "science@college.edu", 3),

        ("Academic Block", "Academic", "Block B", "All Floors",
         ORIGIN_LAT + 0.0020, ORIGIN_LNG + 0.0005,
         "Main classroom block for all departments.",
         "bi-mortarboard", "9:00 AM - 4:30 PM", "academics@college.edu", 3),

        ("Boys Hostel", "Hostel", "Hostel Block", "-",
         ORIGIN_LAT + 0.0011, ORIGIN_LNG - 0.0011,
         "On-campus residential hostel for boys.", "bi-house-door",
         "24 Hours", "hostel@college.edu", 5),

        ("Canteen", "Facility", "Central Court", "Ground Floor",
         ORIGIN_LAT + 0.0016, ORIGIN_LNG - 0.0003,
         "Food court and canteen.", "bi-cup-hot",
         "8:00 AM - 6:00 PM", "-", 8),

        ("Auditorium", "Facility", "Block D", "Ground Floor",
         ORIGIN_LAT + 0.0022, ORIGIN_LNG + 0.0017,
         "Main auditorium for events and seminars.", "bi-easel",
         "As per event schedule", "-", 4),

        ("Sports Complex", "Facility", "Open Grounds", "-",
         ORIGIN_LAT + 0.0006, ORIGIN_LNG + 0.0021,
         "Football, cricket and athletics grounds.", "bi-trophy",
         "6:00 AM - 6:00 PM", "sports@college.edu", 6),

        ("Placement Cell", "Admin", "Block A", "1st Floor",
         ORIGIN_LAT + 0.0008, ORIGIN_LNG - 0.0006,
         "Training & placement office.", "bi-briefcase",
         "9:30 AM - 5:00 PM", "placements@college.edu", 7),

        ("Medical Center", "Facility", "Block E", "Ground Floor",
         ORIGIN_LAT + 0.0009, ORIGIN_LNG - 0.0008,
         "First-aid and basic medical facility.", "bi-hospital",
         "9:00 AM - 5:00 PM", "medical@college.edu", 5),

        ("Parking Area", "Facility", "Near Main Gate", "-",
         ORIGIN_LAT + 0.0002, ORIGIN_LNG + 0.0002,
         "Two-wheeler and four-wheeler parking.", "bi-p-square",
         "24 Hours", "-", 1),

        ("Bus Stop", "Facility", "Near Main Gate", "-",
         ORIGIN_LAT + 0.0001, ORIGIN_LNG - 0.0001,
         "College bus pickup/drop point.", "bi-bus-front",
         "As per bus schedule", "-", 1),
    ]

    cur.executemany(
        """INSERT INTO locations
           (name, category, building, floor, latitude, longitude, description,
            icon, timings, contact, node_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        locations,
    )

    # -----------------------------------------------------------------
    # 3. Default admin account
    # -----------------------------------------------------------------
    cur.execute(
        "INSERT INTO admins (username, password_hash) VALUES (?, ?)",
        ("admin", generate_password_hash("admin123")),
    )

    # -----------------------------------------------------------------
    # 4. Chatbot starter FAQ
    # -----------------------------------------------------------------
    faqs = [
        ("What are the library timings?",
         "The Central Library is open from 8:00 AM to 8:00 PM on all working days.",
         "library,timing,hours,open"),
        ("How do I apply for admission?",
         "Visit the Admission Office in Block A (Ground Floor), open 9:30 AM - 4:30 PM, or email admissions@college.edu.",
         "admission,apply,enquiry"),
        ("Where is the placement cell?",
         "The Placement Cell is on the 1st Floor of the Administrative Block (Block A).",
         "placement,jobs,training,internship"),
        ("Is there a medical facility on campus?",
         "Yes, the Medical Center in Block E offers first-aid and basic medical care from 9:00 AM to 5:00 PM.",
         "medical,doctor,health,emergency,first aid"),
        ("Where can I park my vehicle?",
         "Parking is available near the Main Gate for both two-wheelers and four-wheelers.",
         "parking,park,vehicle,car,bike"),
    ]
    cur.executemany(
        "INSERT INTO chatbot_faq (question, answer, keywords) VALUES (?, ?, ?)",
        faqs,
    )

    conn.commit()
    conn.close()
    print(f"Database created at {DB_PATH}")
    print("Default admin login -> username: admin | password: admin123")


if __name__ == "__main__":
    build_database()
