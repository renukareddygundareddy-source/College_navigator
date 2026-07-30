# Extended Viva Questions & Answers

1. **Why Flask instead of Django?**
   Flask is a micro-framework — lighter weight, faster to learn, and
   gives full control over structure, which suits a scoped final-year
   project better than Django's heavier batteries-included approach.

2. **What is REST and does this API follow it?**
   REST (Representational State Transfer) structures APIs around
   resources and standard HTTP verbs. This project's `/api/locations`,
   `/api/route`, and `/api/chatbot` are resource-oriented, stateless
   JSON endpoints — consistent with REST principles.

3. **What's the time complexity of Dijkstra's algorithm here?**
   O((V + E) log V) using a binary heap, where V = graph nodes and
   E = graph edges — efficient for a campus-scale graph (tens to a few
   hundred nodes).

4. **Why SQLite for development and PostgreSQL for production?**
   SQLite needs no server setup, perfect for development and small
   deployments. PostgreSQL handles concurrent writes and larger scale
   better, which matters once many visitors hit the app simultaneously.

5. **How do you prevent SQL injection here?**
   All queries use parameterized statements (`?` placeholders via
   `sqlite3`), never raw string formatting of user input into SQL.

6. **How does the system stay usable if the visitor denies location permission?**
   `main.js` catches the geolocation error and falls back to showing
   only the destination marker with a clear status message, instead of
   breaking the page.

7. **What is the accuracy of GPS-based routing, and its limitation?**
   Consumer GPS accuracy is typically 3–10 meters outdoors, less
   reliable indoors/near tall buildings. This is why the system snaps
   the visitor to the *nearest graph node* rather than assuming exact
   pixel-perfect positioning.

8. **How would you test the chatbot's accuracy?**
   Build a labeled test set of sample questions with expected FAQ IDs,
   run them through `api_chatbot`, and measure match precision — flagged
   as a natural extension in "Future Enhancements."

9. **Why store passwords as hashes, and which algorithm?**
   Hashing (Werkzeug's `generate_password_hash`, PBKDF2-SHA256 by
   default) means even a database leak doesn't expose usable passwords,
   since hashes can't be reversed and are salted against rainbow-table attacks.

10. **How is session-based auth different from token-based (JWT) auth, and which did you use?**
    This project uses Flask's server-side `session` (a signed cookie),
    simplest for a single-server app. JWT/token auth would be the
    upgrade path for a mobile app or multi-server deployment.

11. **What's the purpose of the `is_active` flag on locations instead of hard deletes?**
    Soft-deletes preserve historical `visitor_logs` referential integrity
    and let admins "undo" accidental removals — hard deleting would
    orphan foreign key references.

12. **How does the turn-by-turn narration logic work?**
    It computes the compass bearing between consecutive route
    coordinates, and whenever the bearing changes by more than ~30°, it
    emits a "turn left/right" instruction with the distance walked since
    the last turn — a simple heuristic version of what real turn-by-turn
    nav systems do.

13. **Is this project offline-capable?**
    Partially — the routing algorithm and database are entirely local
    Python, but map *tiles* are fetched from OpenStreetMap and speech
    features run through the browser's engine, so those need internet
    access unless tiles are cached (a good enhancement: offline PWA tile caching).

14. **How would you add multi-campus support?**
    Add a `campuses` table; scope `locations` and `graph_nodes` with a
    `campus_id` foreign key; resolve which campus a QR code belongs to
    from a `campus` query parameter or subdomain.

15. **What's a realistic scalability bottleneck, and how would you fix it?**
    High concurrent read load on SQLite (`database is locked` errors).
    Fix: migrate to PostgreSQL, add connection pooling, and cache the
    graph in memory instead of re-querying it on every `/api/route` call.
