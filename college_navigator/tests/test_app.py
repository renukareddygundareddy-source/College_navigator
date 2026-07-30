"""
tests/test_app.py
------------------
Basic unit + integration tests.

Run with:
    python -m pytest tests/ -v
(or, without pytest installed:)
    python tests/test_app.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.route_engine import dijkstra


class TestRouteEngine(unittest.TestCase):
    """Unit tests for the Dijkstra shortest-path logic in isolation
    (no database involved) — pure algorithm correctness checks."""

    def setUp(self):
        # a small square graph:  1 -- 2
        #                        |    |
        #                        4 -- 3
        self.nodes = {1: {}, 2: {}, 3: {}, 4: {}}
        self.adjacency = {
            1: [(2, 10), (4, 5)],
            2: [(1, 10), (3, 5)],
            3: [(2, 5), (4, 5)],
            4: [(1, 5), (3, 5)],
        }

    def test_shortest_path_found(self):
        path, dist = dijkstra(self.nodes, self.adjacency, 1, 3)
        # shortest route 1 -> 4 -> 3 = 5 + 5 = 10, vs 1 -> 2 -> 3 = 10 + 5 = 15
        self.assertEqual(path, [1, 4, 3])
        self.assertEqual(dist, 10)

    def test_same_start_and_end(self):
        path, dist = dijkstra(self.nodes, self.adjacency, 1, 1)
        self.assertEqual(path, [1])
        self.assertEqual(dist, 0)

    def test_unreachable_node_returns_none(self):
        nodes = {1: {}, 2: {}, 99: {}}
        adjacency = {1: [(2, 5)], 2: [(1, 5)], 99: []}
        path, dist = dijkstra(nodes, adjacency, 1, 99)
        self.assertIsNone(path)
        self.assertIsNone(dist)


class TestFlaskRoutes(unittest.TestCase):
    """Integration tests using Flask's test client against a freshly
    seeded database."""

    @classmethod
    def setUpClass(cls):
        # Ensure a seeded DB exists before running route tests
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "database", "college.db",
        )
        if not os.path.exists(db_path):
            import subprocess
            subprocess.run([sys.executable, "database/seed.py"], check=True,
                            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        from app import app
        cls.app = app
        cls.client = app.test_client()

    def test_homepage_loads(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)

    def test_navigate_page_loads(self):
        r = self.client.get("/navigate/1")
        self.assertEqual(r.status_code, 200)

    def test_navigate_unknown_location_redirects(self):
        r = self.client.get("/navigate/9999", follow_redirects=True)
        self.assertEqual(r.status_code, 200)  # redirected back to home

    def test_location_search_api(self):
        r = self.client.get("/api/locations?q=library")
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertTrue(any("Library" in loc["name"] for loc in data))

    def test_route_api_returns_valid_route(self):
        r = self.client.get("/api/route?lat=16.3067&lng=80.4365&destination_id=1")
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertIn("coordinates", data)
        self.assertIn("distance_m", data)
        self.assertGreater(data["distance_m"], 0)

    def test_route_api_missing_params(self):
        r = self.client.get("/api/route")
        self.assertEqual(r.status_code, 400)

    def test_chatbot_api_known_question(self):
        r = self.client.post("/api/chatbot", json={"message": "library timings"})
        self.assertEqual(r.status_code, 200)
        self.assertIn("Library", r.get_json()["reply"])

    def test_admin_routes_require_login(self):
        # Use a fresh client so an earlier test's logged-in session
        # doesn't leak into this check.
        fresh_client = self.app.test_client()
        r = fresh_client.get("/admin", follow_redirects=False)
        self.assertEqual(r.status_code, 302)  # redirected to login

    def test_admin_login_success(self):
        r = self.client.post(
            "/admin/login",
            data={"username": "admin", "password": "admin123"},
            follow_redirects=True,
        )
        self.assertEqual(r.status_code, 200)

    def test_admin_login_failure(self):
        r = self.client.post(
            "/admin/login",
            data={"username": "admin", "password": "wrongpass"},
        )
        self.assertEqual(r.status_code, 200)  # re-renders login with flash error


if __name__ == "__main__":
    unittest.main()
