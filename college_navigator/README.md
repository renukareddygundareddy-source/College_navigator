# AI-Powered Smart QR-Based College Navigation System

A complete, working final-year engineering project: scan a QR code at the
campus gate, land on a mobile-friendly website (no app install), pick a
destination, and get a live shortest-path walking route with voice-guided
turn-by-turn directions — plus an AI chatbot for general campus questions.

---

## 1. Quick Start

```bash
# 1. Extract the zip, then move into the folder
cd college_navigator

# 2. Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Build the database (creates database/college.db with sample data)
python database/seed.py

# 5. Run the app
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

- **Visitor site:** the homepage — click any destination card.
- **Admin panel:** http://127.0.0.1:5000/admin/login
  - Username: `admin`
  - Password: `admin123`
  - **Change this password before any real deployment** (see §9).

> The sample data uses fictional GPS coordinates near a placeholder
> "Main Gate" point. To use this on your real campus, replace the
> coordinates in `database/seed.py` (see §5).

---

## 2. What's Included (Deliverables Checklist)

| Deliverable | Where |
|---|---|
| Complete source code | `app.py`, `utils/`, `static/`, `templates/` |
| Database schema + SQL | `database/schema.sql` |
| Seed / sample data script | `database/seed.py` |
| Frontend (HTML/CSS/JS) | `templates/`, `static/` |
| Backend (Flask/Python) | `app.py`, `utils/` |
| API documentation | §6 below |
| Setup instructions | §1 above |
| Testing guide | `tests/README.md` |
| Deployment guide | §9 below |
| User manual | §7 below |
| Administrator manual | §8 below |
| Viva questions & answers | §11 below |
| Future enhancements | §12 below |

---

## 3. Problem Statement, Objectives & Scope

**Problem:** Large campuses are hard to navigate for visitors, parents,
new students, guest lecturers, recruiters and alumni. People currently
rely on asking security guards or students, causing delays and confusion
— especially for elderly or visually-impaired visitors.

**Proposed solution:** QR codes placed at the entrance and key junctions.
Scanning one opens a responsive website (no app needed) that shows all
campus destinations as cards, computes the shortest walking route to the
chosen one over the campus's real path network, and narrates directions
aloud in the visitor's chosen language.

**Objectives**
- Eliminate dependency on physical signage/guards for wayfinding.
- Provide a zero-install, mobile-first navigation experience.
- Offer voice guidance for accessibility (elderly / visually impaired).
- Give administrators a way to manage locations and see analytics
  without touching code.

**Scope:** Outdoor/indoor walking navigation within a single campus,
QR-triggered access, admin-managed location data, rule-based AI
chatbot, and browser-native speech features. It does not include indoor
Bluetooth-beacon-level positioning or turn-by-turn car navigation.

**Existing System vs Proposed System**

| Existing | Proposed |
|---|---|
| Static campus map posters | Interactive live map with routing |
| Ask a guard/student | Self-service AI chatbot + search |
| No accessibility support | Voice narration in multiple languages |
| No usage insight for admins | Visitor analytics dashboard |

---

## 4. Software Requirements Specification (SRS)

### 4.1 Functional Requirements
- FR1: The system shall display all active campus locations grouped by category.
- FR2: The system shall let a visitor search locations by name.
- FR3: The system shall compute the shortest walking route from the visitor's live GPS position to a selected destination.
- FR4: The system shall display distance (meters) and ETA (minutes) for the computed route.
- FR5: The system shall narrate turn-by-turn directions using text-to-speech in a selectable language.
- FR6: The system shall accept voice search input via speech recognition.
- FR7: The system shall answer free-text campus questions via a chatbot widget available on every page.
- FR8: The system shall let an authenticated admin add, edit, and deactivate locations.
- FR9: The system shall let an admin generate a QR code image for any location.
- FR10: The system shall log each navigation request for analytics (most visited destinations, total visits).
- FR11: Unauthenticated users shall not access `/admin/*` routes.

### 4.2 Non-Functional Requirements
- NFR1 (Usability): No app installation required; works from any QR-scanning phone browser.
- NFR2 (Performance): Route computation shall return in under 300ms for a campus-scale graph (<500 nodes).
- NFR3 (Portability): Runs on SQLite for development; schema is compatible with PostgreSQL for production.
- NFR4 (Accessibility): Voice narration and large tap targets support elderly/visually-impaired visitors.
- NFR5 (Security): Admin passwords are stored as salted hashes (Werkzeug `generate_password_hash`), never plain text.
- NFR6 (Availability): Designed to run behind a standard WSGI server (Gunicorn) for production uptime.

### 4.3 Hardware Requirements
- Server: any machine/VM with 1 vCPU, 512MB RAM minimum (dev); 1–2GB RAM recommended for production with concurrent users.
- Client: any smartphone or laptop with a camera (to scan QR) and a modern browser.

### 4.4 Software Requirements
- Python 3.10+
- Flask 3.x, Werkzeug
- SQLite3 (bundled with Python) or PostgreSQL for production
- Modern browser supporting the Web Speech API (Chrome recommended for full voice support)
- `qrcode` + `Pillow` Python packages (QR generation)

---

## 5. Project Folder Structure

```
college_navigator/
├── app.py                     # Main Flask application (routes, APIs, admin)
├── requirements.txt           # Python dependencies
├── README.md                  # This file
│
├── database/
│   ├── schema.sql              # Full SQL schema (tables, keys, indexes)
│   ├── seed.py                 # Builds college.db with sample campus data
│   └── college.db              # Generated SQLite database (after running seed.py)
│
├── utils/
│   ├── route_engine.py         # Dijkstra shortest-path over the campus graph
│   └── qr_generator.py         # Generates QR code PNGs per location
│
├── templates/                  # Jinja2 HTML templates
│   ├── base.html                # Shared layout, navbar, footer, chatbot widget
│   ├── index.html               # Home page — destination directory + search
│   ├── navigate.html            # Map + route + voice controls
│   ├── about.html
│   ├── contact.html
│   ├── admin_login.html
│   └── admin_dashboard.html     # CRUD + analytics + QR generation
│
├── static/
│   ├── css/style.css            # Wayfinding-signage themed design system
│   ├── js/main.js               # Search, Leaflet map, route fetching
│   ├── js/voice.js               # Speech synthesis + recognition (voice nav)
│   ├── js/chatbot.js             # Floating AI assistant widget logic
│   └── qrcodes/                  # Generated QR PNGs land here
│
├── docs/                        # Extra report material (diagrams as text/mermaid)
│   ├── architecture.md
│   ├── database_design.md
│   └── viva_questions.md
│
└── tests/
    └── README.md                 # How to run the test suite described below
```

**Why this structure?** It separates *what the visitor sees*
(`templates/`, `static/`) from *how the server thinks*
(`app.py`, `utils/`) from *what the server remembers*
(`database/`). This is the standard Flask "application factory-lite"
layout — small enough for a final-year project, but organized the same
way a production app would be, which is exactly what examiners and
interviewers look for.

---

## 6. API Documentation

All endpoints return JSON unless noted.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/locations?q=<text>` | List/search active locations |
| GET | `/api/route?lat=&lng=&destination_id=` | Compute shortest route from a GPS point to a location |
| POST | `/api/chatbot` `{"message": "..."}` | AI chatbot reply |
| GET | `/navigate/<id>` | HTML page: map + route to location `<id>` |
| POST | `/admin/location/add` | (auth) Create a location |
| POST | `/admin/location/edit/<id>` | (auth) Update a location |
| POST | `/admin/location/delete/<id>` | (auth) Deactivate a location |
| POST | `/admin/qr/generate/<id>` | (auth) Generate a QR PNG for a location |

Example `/api/route` response:
```json
{
  "coordinates": [[16.3067, 80.4365], [16.3077, 80.4370], ...],
  "distance_m": 341.2,
  "eta_minutes": 4.1,
  "node_path": [1, 2, 3, 4],
  "destination": { "id": 1, "name": "Central Library", "latitude": ..., "longitude": ... }
}
```

---

## 7. User Manual (Visitors)

1. Scan the QR code at the entrance (or open the site URL directly).
2. On the homepage, browse destination cards by category, or type/speak
   a search query (tap the microphone icon).
3. Tap a destination to open the map. Allow the browser's location
   permission prompt — this is required to compute your live route.
4. The blue-green dot is you; the orange line is your route.
5. Tap **Start** under "Voice Guidance" to hear spoken directions.
   Change the language dropdown first if you prefer Hindi/Telugu/Tamil/Kannada.
6. Use the floating chat bubble (bottom-right) anytime to ask questions
   like *"What are the library timings?"* or *"Where is the placement cell?"*

## 8. Administrator Manual

1. Go to `/admin/login` and sign in.
2. **Dashboard** shows total logged visits and the top 5 most-searched
   destinations — use this to see which signage/QR placement matters most.
3. **Add New Location**: fill the form. `node_id` must be an existing
   `graph_nodes.id` (the nearest walkway junction) — see `database/seed.py`
   for the current node map, or query `SELECT * FROM graph_nodes` in
   the admin's DB browser of choice.
4. **Manage Locations** table: click the QR icon to generate/download a
   scannable QR code for that location (saved to `static/qrcodes/`),
   or the trash icon to deactivate (soft-delete) a location.
5. Always log out on shared computers.

---

## 9. Deployment Guide

### 9.1 Local development
Already covered in §1 — `python app.py` runs Flask's built-in dev server.

### 9.2 Production (Linux server, Gunicorn + Nginx)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```
Put Nginx in front as a reverse proxy for TLS termination and static
file caching. Set a strong `SECRET_KEY` environment variable instead of
the default dev value in `app.py`.

### 9.3 Docker
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn
COPY . .
RUN python database/seed.py
EXPOSE 8000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
```
```bash
docker build -t campus-navigator .
docker run -p 8000:8000 campus-navigator
```

### 9.4 Hosting options
- **Render / Railway / PythonAnywhere**: simplest for a student project, free tiers available.
- **A college server / campus VM**: preferred for a real deployment so GPS/QR URLs use the college's own domain.
- Switch `database/college.db` (SQLite) to PostgreSQL for multi-user production traffic — the schema in `schema.sql` is portable with minor type tweaks (`AUTOINCREMENT` → `SERIAL`).

### 9.5 Before going live
- Change the default admin password.
- Set `app.secret_key` from an environment variable, not a hardcoded string.
- Turn `debug=True` off in `app.run(...)`.
- Re-walk the campus with a GPS app (or use satellite imagery) to enter accurate `graph_nodes` and `locations` coordinates for your real campus.

---

## 10. Testing

See `tests/README.md` for the full guide. Summary:
- **Unit tests**: `utils/route_engine.py`'s Dijkstra logic (path correctness, unreachable nodes).
- **Integration tests**: Flask test client hitting `/api/route`, `/api/chatbot`, `/admin/*` (all verified working — see below).
- **Manual/UI tests**: checklist for map rendering, voice playback, chatbot widget, admin CRUD, on both desktop and a real phone (for GPS + QR scanning).

All backend routes in this build were smoke-tested with Flask's test
client: homepage, navigate page, search API, route API, chatbot API,
admin login, and admin CRUD (add/edit/delete) all return HTTP 200.

---

## 11. Viva Questions & Answers

**Q: Why is this considered an "AI" project and not just a web app?**
A: It combines several AI-adjacent components: (1) graph-based shortest-path
search (Dijkstra) for route optimization — a classic AI/algorithms
technique; (2) a chatbot using text-similarity/NLP-style matching
(`difflib` + keyword tagging) to answer free-text questions; (3) Speech
Recognition and Speech Synthesis, which are neural models for acoustic
and language processing, integrated via the browser's Web Speech API;
(4) turn-by-turn instruction generation, which converts raw coordinate
data into natural language — a language-generation task.

**Q: Why Dijkstra and not just straight-line distance?**
A: A straight line would cut through buildings and walls. Dijkstra finds
the shortest path along the actual walkway graph, which mirrors how
real navigation apps (Google Maps, OSRM) work, just scoped to campus paths.

**Q: How does the QR code work?**
A: Each QR encodes a URL like `/navigate/<id>?source=qr`. Scanning opens
that URL in the phone's default browser — no app needed. The `?source=qr`
tag also lets analytics distinguish QR-driven visits from search-driven ones.

**Q: How is voice navigation implemented without any paid API?**
A: The browser's built-in Web Speech API provides both `SpeechRecognition`
(speech-to-text) and `SpeechSynthesis` (text-to-speech) for free,
client-side, in Chrome and most modern browsers.

**Q: How would you scale this to multiple campuses?**
A: Add a `campuses` table and a `campus_id` foreign key to `locations`
and `graph_nodes`; scope all queries by the campus resolved from the
QR code or subdomain.

**Q: How do you secure the admin panel?**
A: Session-based auth (Flask `session`), passwords hashed with Werkzeug's
`generate_password_hash`/`check_password_hash` (PBKDF2), and a
`login_required` decorator guarding every `/admin/*` route.

**Q: What happens if GPS is denied?**
A: The app falls back to showing just the destination pin on the map
and displays a clear status message asking the visitor to enable
location — it degrades gracefully rather than crashing.

*(See `docs/viva_questions.md` for ~15 more Q&As including database
normalization, REST principles, and complexity analysis of Dijkstra.)*

---

## 12. Future Enhancements (Ideas to Extend the Project)

See the chat response for a full breakdown of "what to add to make this
more advanced" — summarized here for the report:
- Indoor navigation via Bluetooth beacons / Wi-Fi RTT for room-level accuracy.
- Real NLP chatbot (embeddings + vector search, or a small LLM) instead of keyword/fuzzy matching.
- AR (augmented reality) camera overlay for directions using WebXR.
- Predictive crowd-density suggestions (e.g. "canteen is busy, try 1pm instead").
- Push notifications for event-based navigation (e.g. auditorium seating during fests).
- Multi-campus / multi-tenant support.
- Progressive Web App (PWA) install prompt for offline map caching.
- Analytics dashboard charts (Chart.js) instead of a plain list.
#   C o l l e g e _ n a v i g a t o r  
 