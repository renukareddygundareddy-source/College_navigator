# Database Design

## ER Diagram (textual)

```
┌───────────────┐        ┌──────────────┐        ┌──────────────┐
│  graph_nodes  │◄──┐    │ graph_edges  │        │   locations  │
├───────────────┤   │    ├──────────────┤        ├──────────────┤
│ id PK         │   │    │ id PK        │        │ id PK        │
│ label         │   ├────│ node_a_id FK │        │ name         │
│ latitude      │   ├────│ node_b_id FK │        │ category     │
│ longitude     │   │    │ distance_m   │        │ building     │
└───────────────┘   │    └──────────────┘        │ floor        │
        ▲            │                            │ latitude     │
        │            └───────────────────────────►│ longitude    │
        │ (nearest node)                          │ description  │
        │                                          │ icon         │
        │                                          │ timings      │
        │                                          │ contact      │
        │                                          │ node_id FK   │──┘
        │                                          │ is_active    │
        │                                          └──────┬───────┘
        │                                                 │
        │                                                 │ 1:N
        │                                                 ▼
        │                                          ┌──────────────┐
        │                                          │ visitor_logs │
        │                                          ├──────────────┤
        │                                          │ id PK        │
        │                                          │ location_id FK│
        │                                          │ source        │
        │                                          │ user_agent    │
        │                                          │ timestamp     │
        │                                          └──────────────┘
        │
┌───────┴───────┐         ┌──────────────┐         ┌──────────────┐
│   qr_codes    │         │    admins    │         │ chatbot_faq  │
├───────────────┤         ├──────────────┤         ├──────────────┤
│ id PK         │         │ id PK        │         │ id PK        │
│ location_id FK│         │ username     │         │ question     │
│ file_path     │         │ password_hash│         │ answer       │
│ target_url    │         │ created_at   │         │ keywords     │
│ created_at    │         └──────────────┘         └──────────────┘
```

## Table Explanations

- **locations** — every destination visitors can navigate to. `node_id`
  links each location to the *nearest* walkway junction in the routing
  graph, so a route can be computed even though the location itself
  might be inside a building (off the walkable graph).
- **graph_nodes / graph_edges** — model the campus's actual walkable
  path network as a weighted undirected graph. This is what Dijkstra
  runs over, instead of drawing a straight line through walls.
- **admins** — administrator accounts; passwords are hashed with
  Werkzeug's PBKDF2-based `generate_password_hash`, never stored in plain text.
- **visitor_logs** — one row per navigation request; powers the "Top
  Destinations" analytics on the admin dashboard.
- **chatbot_faq** — curated Q&A pairs with keyword tags the chatbot
  matches against, in addition to live data from `locations`.
- **qr_codes** — tracks every generated QR image and the URL it encodes,
  so admins can regenerate or audit them later.

## Normalization Notes

The schema is in **3rd Normal Form (3NF)**:
- Every non-key column depends only on the table's primary key (1NF/2NF).
- No transitive dependencies — e.g. `visitor_logs` stores `location_id`
  rather than duplicating the location's name/building, avoiding update anomalies.
- Many-to-many-like path connectivity is modeled properly via the
  `graph_edges` junction table rather than repeating columns.
