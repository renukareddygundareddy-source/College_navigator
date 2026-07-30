# System Design

## 1. Architecture Overview

```
┌─────────────────────┐        HTTPS         ┌──────────────────────────┐
│   Visitor's Phone    │◄────────────────────►│   Flask Application      │
│  (Browser, no app)   │                       │   (app.py)               │
│                       │                       │                          │
│  - Leaflet.js map     │   GET /               │  Routes:                 │
│  - Web Speech API     │   GET /navigate/<id>  │   / , /navigate, /about  │
│  - Geolocation API    │   GET /api/route      │   /api/*  (JSON)         │
│  - Fetch (AJAX)       │   POST /api/chatbot   │   /admin/* (session auth)│
└─────────────────────┘   POST /api/chatbot    └───────────┬──────────────┘
        ▲                                                    │
        │ scans                                              ▼
┌───────┴────────┐                              ┌──────────────────────────┐
│   QR Code at    │                              │  utils/route_engine.py   │
│   campus gate   │                              │  (Dijkstra over graph)   │
└─────────────────┘                              └───────────┬──────────────┘
                                                               ▼
                                                  ┌──────────────────────────┐
                                                  │   SQLite / PostgreSQL     │
                                                  │  locations, graph_nodes,  │
                                                  │  graph_edges, admins,     │
                                                  │  visitor_logs, faq        │
                                                  └──────────────────────────┘
```

## 2. Data Flow Diagram (Level 1)

```
Visitor ──(scan QR / open site)──► Homepage ──(select destination)──► Navigate Page
                                                                            │
                                                     (browser Geolocation)  │
                                                                            ▼
                                                 GET /api/route?lat&lng&destination_id
                                                                            │
                                                                            ▼
                                          route_engine.compute_route() ──► Dijkstra over graph_nodes/edges
                                                                            │
                                                                            ▼
                                          JSON {coordinates, distance_m, eta_minutes}
                                                                            │
                                                                            ▼
                                     Leaflet draws polyline  +  voice.js narrates steps
```

## 3. Use Case Diagram (textual)

- **Visitor**: Scan QR, Search destination, View route, Hear voice directions, Ask chatbot.
- **Administrator**: Login, Add/Edit/Deactivate location, Generate QR, View analytics, Logout.

## 4. Sequence Diagram — "Visitor navigates to Library" (textual)

```
Visitor -> Browser: scans QR code
Browser -> Flask: GET /navigate/1?source=qr
Flask -> DB: SELECT location WHERE id=1 ; INSERT visitor_log
Flask -> Browser: renders navigate.html (map placeholder)
Browser -> Browser: navigator.geolocation.getCurrentPosition()
Browser -> Flask: GET /api/route?lat=..&lng=..&destination_id=1
Flask -> route_engine: compute_route(start_node, dest_node)
route_engine -> DB: load graph_nodes, graph_edges
route_engine -> Flask: {coordinates, distance_m, eta_minutes}
Flask -> Browser: JSON response
Browser -> Leaflet: draw polyline + markers
Browser -> Web Speech API: speak turn-by-turn steps
```

## 5. Class Diagram (conceptual — Flask app is function-based, but conceptually)

```
Location            GraphNode            GraphEdge
---------            ---------            ---------
id                   id                   id
name                 label                node_a_id
category             latitude             node_b_id
building             longitude            distance_m
floor
latitude
longitude
node_id  ────────────► (FK)

RouteEngine
-----------
+ dijkstra(nodes, adjacency, start, end) -> (path, distance)
+ compute_route(db_path, start_node_id, end_node_id) -> dict

Chatbot (function-based in app.py)
-----------------------------------
+ api_chatbot(message) -> best-matching FAQ/location answer
```
