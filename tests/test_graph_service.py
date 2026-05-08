"""
Test cases for GraphService Cypher queries.

UC-5 : Follow Another User
UC-6 : Unfollow User
UC-7 : View Friends / Connections
UC-8 : Mutual Connections
UC-9 : Friend Recommendations
UC-11: Explore Popular Users
"""
import unittest
from unittest.mock import patch
from backend.graph_service import GraphService


class TestFollowUser(unittest.TestCase):
    """UC-5: MERGE (current)-[:FOLLOWS]->(target)"""

    @patch("backend.graph_service.Neo4jConnection")
    def test_follow_success(self, MockDB):
        MockDB.return_value.execute_query.return_value = [
            {"currentUser": "alice", "followedUser": "bob"}
        ]

        result = GraphService().follow_user("alice", "bob")

        self.assertTrue(result["success"])
        self.assertIn("alice", result["message"])
        self.assertIn("bob", result["message"])

    @patch("backend.graph_service.Neo4jConnection")
    def test_follow_yourself_is_rejected_without_db_call(self, MockDB):
        result = GraphService().follow_user("alice", "alice")

        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "You cannot follow yourself.")
        MockDB.return_value.execute_query.assert_not_called()

    @patch("backend.graph_service.Neo4jConnection")
    def test_follow_user_not_found(self, MockDB):
        MockDB.return_value.execute_query.return_value = []

        result = GraphService().follow_user("alice", "nobody")

        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "One or both users were not found.")

    @patch("backend.graph_service.Neo4jConnection")
    def test_follow_query_uses_merge_and_follows(self, MockDB):
        MockDB.return_value.execute_query.return_value = [
            {"currentUser": "alice", "followedUser": "bob"}
        ]

        GraphService().follow_user("alice", "bob")

        query = MockDB.return_value.execute_query.call_args[0][0]
        self.assertIn("MERGE", query)
        self.assertIn("FOLLOWS", query)

    @patch("backend.graph_service.Neo4jConnection")
    def test_follow_passes_correct_username_params(self, MockDB):
        MockDB.return_value.execute_query.return_value = [
            {"currentUser": "alice", "followedUser": "bob"}
        ]

        GraphService().follow_user("alice", "bob")

        params = MockDB.return_value.execute_query.call_args[0][1]
        self.assertEqual(params["current_username"], "alice")
        self.assertEqual(params["target_username"], "bob")


class TestUnfollowUser(unittest.TestCase):
    """UC-6: MATCH (current)-[r:FOLLOWS]->(target) DELETE r"""

    @patch("backend.graph_service.Neo4jConnection")
    def test_unfollow_success(self, MockDB):
        MockDB.return_value.execute_query.return_value = [
            {"currentUser": "alice", "unfollowedUser": "bob"}
        ]

        result = GraphService().unfollow_user("alice", "bob")

        self.assertTrue(result["success"])
        self.assertIn("alice", result["message"])
        self.assertIn("bob", result["message"])

    @patch("backend.graph_service.Neo4jConnection")
    def test_unfollow_relationship_not_found(self, MockDB):
        MockDB.return_value.execute_query.return_value = []

        result = GraphService().unfollow_user("alice", "bob")

        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Follow relationship not found.")

    @patch("backend.graph_service.Neo4jConnection")
    def test_unfollow_query_deletes_follows_relationship(self, MockDB):
        MockDB.return_value.execute_query.return_value = []

        GraphService().unfollow_user("alice", "bob")

        query = MockDB.return_value.execute_query.call_args[0][0]
        self.assertIn("DELETE", query)
        self.assertIn("FOLLOWS", query)

    @patch("backend.graph_service.Neo4jConnection")
    def test_unfollow_passes_correct_username_params(self, MockDB):
        MockDB.return_value.execute_query.return_value = []

        GraphService().unfollow_user("alice", "bob")

        params = MockDB.return_value.execute_query.call_args[0][1]
        self.assertEqual(params["current_username"], "alice")
        self.assertEqual(params["target_username"], "bob")


class TestViewConnections(unittest.TestCase):
    """UC-7: OPTIONAL MATCH following/followers, collect(DISTINCT {...})"""

    @patch("backend.graph_service.Neo4jConnection")
    def test_view_connections_returns_following_and_followers(self, MockDB):
        MockDB.return_value.execute_query.return_value = [{
            "following": [{"userId": 2, "username": "bob", "name": "Bob"}],
            "followers": [{"userId": 3, "username": "carol", "name": "Carol"}]
        }]

        result = GraphService().view_connections("alice")

        self.assertTrue(result["success"])
        self.assertEqual(result["connections"]["following"][0]["username"], "bob")
        self.assertEqual(result["connections"]["followers"][0]["username"], "carol")

    @patch("backend.graph_service.Neo4jConnection")
    def test_view_connections_with_no_connections(self, MockDB):
        MockDB.return_value.execute_query.return_value = [{"following": [], "followers": []}]

        result = GraphService().view_connections("alice")

        self.assertTrue(result["success"])
        self.assertEqual(result["connections"]["following"], [])
        self.assertEqual(result["connections"]["followers"], [])

    @patch("backend.graph_service.Neo4jConnection")
    def test_view_connections_user_not_found(self, MockDB):
        MockDB.return_value.execute_query.return_value = []

        result = GraphService().view_connections("nobody")

        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "User not found.")

    @patch("backend.graph_service.Neo4jConnection")
    def test_view_connections_query_uses_optional_match(self, MockDB):
        MockDB.return_value.execute_query.return_value = []

        GraphService().view_connections("alice")

        query = MockDB.return_value.execute_query.call_args[0][0]
        self.assertIn("OPTIONAL MATCH", query)
        self.assertIn("FOLLOWS", query)

    @patch("backend.graph_service.Neo4jConnection")
    def test_view_connections_passes_username_param(self, MockDB):
        MockDB.return_value.execute_query.return_value = []

        GraphService().view_connections("alice")

        params = MockDB.return_value.execute_query.call_args[0][1]
        self.assertEqual(params["username"], "alice")


class TestMutualConnections(unittest.TestCase):
    """UC-8: MATCH u1-[:FOLLOWS]->mutual<-[:FOLLOWS]-u2 RETURN mutual.*"""

    @patch("backend.graph_service.Neo4jConnection")
    def test_mutual_connections_found(self, MockDB):
        MockDB.return_value.execute_query.return_value = [
            {"userId": 3, "username": "carol", "name": "Carol"}
        ]

        result = GraphService().mutual_connections("alice", "bob")

        self.assertTrue(result["success"])
        self.assertEqual(len(result["mutual_connections"]), 1)
        self.assertEqual(result["mutual_connections"][0]["username"], "carol")

    @patch("backend.graph_service.Neo4jConnection")
    def test_mutual_connections_none_found(self, MockDB):
        MockDB.return_value.execute_query.return_value = []

        result = GraphService().mutual_connections("alice", "bob")

        self.assertTrue(result["success"])
        self.assertEqual(result["mutual_connections"], [])

    @patch("backend.graph_service.Neo4jConnection")
    def test_mutual_connections_passes_both_usernames(self, MockDB):
        MockDB.return_value.execute_query.return_value = []

        GraphService().mutual_connections("alice", "bob")

        params = MockDB.return_value.execute_query.call_args[0][1]
        self.assertEqual(params["username1"], "alice")
        self.assertEqual(params["username2"], "bob")

    @patch("backend.graph_service.Neo4jConnection")
    def test_mutual_connections_passes_limit(self, MockDB):
        MockDB.return_value.execute_query.return_value = []

        GraphService().mutual_connections("alice", "bob", limit=5)

        params = MockDB.return_value.execute_query.call_args[0][1]
        self.assertEqual(params["limit"], 5)

    @patch("backend.graph_service.Neo4jConnection")
    def test_mutual_connections_default_limit_is_20(self, MockDB):
        MockDB.return_value.execute_query.return_value = []

        GraphService().mutual_connections("alice", "bob")

        params = MockDB.return_value.execute_query.call_args[0][1]
        self.assertEqual(params["limit"], 20)

    @patch("backend.graph_service.Neo4jConnection")
    def test_mutual_connections_query_uses_follows(self, MockDB):
        MockDB.return_value.execute_query.return_value = []

        GraphService().mutual_connections("alice", "bob")

        query = MockDB.return_value.execute_query.call_args[0][0]
        self.assertIn("FOLLOWS", query)
        self.assertIn("LIMIT", query)


class TestRecommendUsers(unittest.TestCase):
    """UC-9: MATCH u-[:FOLLOWS]->()-[:FOLLOWS]->rec WHERE NOT followed AND <> self ORDER BY count"""

    @patch("backend.graph_service.Neo4jConnection")
    def test_recommendations_returned_ordered_by_mutual_count(self, MockDB):
        MockDB.return_value.execute_query.return_value = [
            {"userId": 4, "username": "dave", "name": "Dave", "mutualConnectionCount": 3},
            {"userId": 5, "username": "eve", "name": "Eve", "mutualConnectionCount": 1},
        ]

        result = GraphService().recommend_users("alice")

        self.assertTrue(result["success"])
        self.assertEqual(len(result["recommendations"]), 2)
        self.assertEqual(result["recommendations"][0]["username"], "dave")

    @patch("backend.graph_service.Neo4jConnection")
    def test_no_recommendations(self, MockDB):
        MockDB.return_value.execute_query.return_value = []

        result = GraphService().recommend_users("alice")

        self.assertTrue(result["success"])
        self.assertEqual(result["recommendations"], [])

    @patch("backend.graph_service.Neo4jConnection")
    def test_recommendations_passes_username_param(self, MockDB):
        MockDB.return_value.execute_query.return_value = []

        GraphService().recommend_users("alice")

        params = MockDB.return_value.execute_query.call_args[0][1]
        self.assertEqual(params["username"], "alice")

    @patch("backend.graph_service.Neo4jConnection")
    def test_recommendations_passes_limit(self, MockDB):
        MockDB.return_value.execute_query.return_value = []

        GraphService().recommend_users("alice", limit=5)

        params = MockDB.return_value.execute_query.call_args[0][1]
        self.assertEqual(params["limit"], 5)

    @patch("backend.graph_service.Neo4jConnection")
    def test_recommendations_default_limit_is_10(self, MockDB):
        MockDB.return_value.execute_query.return_value = []

        GraphService().recommend_users("alice")

        params = MockDB.return_value.execute_query.call_args[0][1]
        self.assertEqual(params["limit"], 10)

    @patch("backend.graph_service.Neo4jConnection")
    def test_recommendations_query_excludes_self_and_already_followed(self, MockDB):
        MockDB.return_value.execute_query.return_value = []

        GraphService().recommend_users("alice")

        query = MockDB.return_value.execute_query.call_args[0][0]
        self.assertIn("NOT", query)
        self.assertIn("<>", query)

    @patch("backend.graph_service.Neo4jConnection")
    def test_recommendations_query_orders_by_mutual_count_descending(self, MockDB):
        MockDB.return_value.execute_query.return_value = []

        GraphService().recommend_users("alice")

        query = MockDB.return_value.execute_query.call_args[0][0]
        self.assertIn("ORDER BY", query)
        self.assertIn("DESC", query)


class TestPopularUsers(unittest.TestCase):
    """UC-11: OPTIONAL MATCH (:User)-[:FOLLOWS]->(u) count(*) ORDER BY followerCount DESC"""

    @patch("backend.graph_service.Neo4jConnection")
    def test_popular_users_returned(self, MockDB):
        MockDB.return_value.execute_query.return_value = [
            {"userId": 2, "username": "bob", "name": "Bob", "followerCount": 100},
            {"userId": 1, "username": "alice", "name": "Alice", "followerCount": 50},
        ]

        result = GraphService().popular_users()

        self.assertTrue(result["success"])
        self.assertEqual(len(result["popular_users"]), 2)
        self.assertEqual(result["popular_users"][0]["username"], "bob")
        self.assertEqual(result["popular_users"][0]["followerCount"], 100)

    @patch("backend.graph_service.Neo4jConnection")
    def test_popular_users_empty_db(self, MockDB):
        MockDB.return_value.execute_query.return_value = []

        result = GraphService().popular_users()

        self.assertTrue(result["success"])
        self.assertEqual(result["popular_users"], [])

    @patch("backend.graph_service.Neo4jConnection")
    def test_popular_users_default_limit_is_10(self, MockDB):
        MockDB.return_value.execute_query.return_value = []

        GraphService().popular_users()

        params = MockDB.return_value.execute_query.call_args[0][1]
        self.assertEqual(params["limit"], 10)

    @patch("backend.graph_service.Neo4jConnection")
    def test_popular_users_custom_limit(self, MockDB):
        MockDB.return_value.execute_query.return_value = []

        GraphService().popular_users(limit=5)

        params = MockDB.return_value.execute_query.call_args[0][1]
        self.assertEqual(params["limit"], 5)

    @patch("backend.graph_service.Neo4jConnection")
    def test_popular_users_query_uses_optional_match_for_users_with_no_followers(self, MockDB):
        MockDB.return_value.execute_query.return_value = []

        GraphService().popular_users()

        query = MockDB.return_value.execute_query.call_args[0][0]
        self.assertIn("OPTIONAL MATCH", query)
        self.assertIn("FOLLOWS", query)

    @patch("backend.graph_service.Neo4jConnection")
    def test_popular_users_query_orders_by_follower_count_descending(self, MockDB):
        MockDB.return_value.execute_query.return_value = []

        GraphService().popular_users()

        query = MockDB.return_value.execute_query.call_args[0][0]
        self.assertIn("ORDER BY", query)
        self.assertIn("DESC", query)
        self.assertIn("followerCount", query)


if __name__ == "__main__":
    unittest.main()
