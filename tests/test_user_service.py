"""
Test cases for UserService Cypher queries.

UC-1 : User Registration
UC-2 : User Login
UC-3 : View Profile
UC-4 : Edit Profile
UC-10: Search Users
"""
import unittest
from unittest.mock import patch
from backend.user_service import UserService


class TestRegisterUser(unittest.TestCase):
    """UC-1: CREATE (u:User {...}) RETURN u"""

    @patch("backend.user_service.Neo4jConnection")
    def test_register_success(self, MockDB):
        MockDB.return_value.execute_query.side_effect = [
            [{"next_id": 1}],
            [{"u": {}}]
        ]

        result = UserService().register_user("Alice", "alice@example.com", "alice", "pass123")

        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "User registered successfully.")

    @patch("backend.user_service.Neo4jConnection")
    def test_register_bio_defaults_to_empty_string(self, MockDB):
        MockDB.return_value.execute_query.side_effect = [
            [{"next_id": 1}],
            [{"u": {}}]
        ]

        UserService().register_user("Alice", "alice@example.com", "alice", "pass123")

        params = MockDB.return_value.execute_query.call_args[0][1]
        self.assertEqual(params["bio"], "")

    @patch("backend.user_service.Neo4jConnection")
    def test_register_custom_bio_is_passed(self, MockDB):
        MockDB.return_value.execute_query.side_effect = [
            [{"next_id": 2}],
            [{"u": {}}]
        ]

        UserService().register_user("Bob", "bob@example.com", "bob", "pass", bio="Hi there")

        params = MockDB.return_value.execute_query.call_args[0][1]
        self.assertEqual(params["bio"], "Hi there")

    @patch("backend.user_service.Neo4jConnection")
    def test_register_user_id_is_auto_generated_int(self, MockDB):
        MockDB.return_value.execute_query.side_effect = [
            [{"next_id": 5}],
            [{"u": {}}]
        ]

        UserService().register_user("Alice", "a@a.com", "alice", "pass")

        params = MockDB.return_value.execute_query.call_args[0][1]
        self.assertIsInstance(params["user_id"], int)
        self.assertEqual(params["user_id"], 5)

    @patch("backend.user_service.Neo4jConnection")
    def test_register_exception_returns_failure(self, MockDB):
        MockDB.return_value.execute_query.side_effect = [
            [{"next_id": 1}],
            Exception("SomeOtherError")
        ]

        result = UserService().register_user("Alice", "alice@example.com", "alice", "pass")

        self.assertFalse(result["success"])
        self.assertIn("Registration failed", result["message"])

    @patch("backend.user_service.Neo4jConnection")
    def test_register_duplicate_username_returns_friendly_message(self, MockDB):
        MockDB.return_value.execute_query.side_effect = [
            [{"next_id": 1}],
            Exception("ConstraintValidationFailed")
        ]

        result = UserService().register_user("Alice", "alice@example.com", "alice", "pass")

        self.assertFalse(result["success"])
        self.assertIn("already taken", result["message"])

    @patch("backend.user_service.Neo4jConnection")
    def test_register_query_uses_create(self, MockDB):
        MockDB.return_value.execute_query.side_effect = [
            [{"next_id": 1}],
            [{"u": {}}]
        ]

        UserService().register_user("Alice", "a@a.com", "alice", "pass")

        query = MockDB.return_value.execute_query.call_args[0][0]
        self.assertIn("CREATE", query)
        self.assertIn("User", query)


class TestLoginUser(unittest.TestCase):
    """UC-2: MATCH (u:User {username, password}) RETURN u.*"""

    @patch("backend.user_service.Neo4jConnection")
    def test_login_valid_credentials(self, MockDB):
        MockDB.return_value.execute_query.return_value = [{
            "userId": 1, "username": "alice", "name": "Alice",
            "email": "alice@example.com", "bio": ""
        }]

        result = UserService().login_user("alice", "pass123")

        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "Login successful.")
        self.assertEqual(result["user"]["username"], "alice")

    @patch("backend.user_service.Neo4jConnection")
    def test_login_invalid_credentials(self, MockDB):
        MockDB.return_value.execute_query.return_value = []

        result = UserService().login_user("alice", "wrongpassword")

        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Invalid username or password.")

    @patch("backend.user_service.Neo4jConnection")
    def test_login_passes_username_and_password_params(self, MockDB):
        MockDB.return_value.execute_query.return_value = []

        UserService().login_user("alice", "pass123")

        params = MockDB.return_value.execute_query.call_args[0][1]
        self.assertEqual(params["username"], "alice")
        self.assertEqual(params["password"], "pass123")

    @patch("backend.user_service.Neo4jConnection")
    def test_login_query_matches_on_username_and_password(self, MockDB):
        MockDB.return_value.execute_query.return_value = []

        UserService().login_user("alice", "pass123")

        query = MockDB.return_value.execute_query.call_args[0][0]
        self.assertIn("MATCH", query)
        self.assertIn("username", query)
        self.assertIn("password", query)


class TestViewProfile(unittest.TestCase):
    """UC-3: MATCH (u:User {username}) RETURN u.*"""

    @patch("backend.user_service.Neo4jConnection")
    def test_view_existing_profile(self, MockDB):
        MockDB.return_value.execute_query.return_value = [{
            "userId": 1, "username": "alice", "name": "Alice",
            "email": "alice@example.com", "bio": "Hello!"
        }]

        result = UserService().view_profile("alice")

        self.assertTrue(result["success"])
        self.assertEqual(result["profile"]["username"], "alice")
        self.assertEqual(result["profile"]["name"], "Alice")

    @patch("backend.user_service.Neo4jConnection")
    def test_view_nonexistent_user(self, MockDB):
        MockDB.return_value.execute_query.return_value = []

        result = UserService().view_profile("nobody")

        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "User not found.")

    @patch("backend.user_service.Neo4jConnection")
    def test_view_profile_passes_username_param(self, MockDB):
        MockDB.return_value.execute_query.return_value = []

        UserService().view_profile("alice")

        params = MockDB.return_value.execute_query.call_args[0][1]
        self.assertEqual(params["username"], "alice")


class TestEditProfile(unittest.TestCase):
    """UC-4: MATCH (u:User) SET u.* = coalesce($val, u.*) RETURN u.*"""

    @patch("backend.user_service.Neo4jConnection")
    def test_edit_name_only(self, MockDB):
        MockDB.return_value.execute_query.return_value = [{
            "userId": 1, "username": "alice", "name": "Alice Updated",
            "email": "alice@example.com", "bio": "Hello!"
        }]

        result = UserService().edit_profile("alice", name="Alice Updated")

        self.assertTrue(result["success"])
        self.assertEqual(result["profile"]["name"], "Alice Updated")

    @patch("backend.user_service.Neo4jConnection")
    def test_edit_all_fields(self, MockDB):
        MockDB.return_value.execute_query.return_value = [{
            "userId": 1, "username": "alice", "name": "Alice New",
            "email": "new@example.com", "bio": "New bio"
        }]

        UserService().edit_profile("alice", name="Alice New", email="new@example.com", bio="New bio")

        params = MockDB.return_value.execute_query.call_args[0][1]
        self.assertEqual(params["name"], "Alice New")
        self.assertEqual(params["email"], "new@example.com")
        self.assertEqual(params["bio"], "New bio")

    @patch("backend.user_service.Neo4jConnection")
    def test_edit_nonexistent_user(self, MockDB):
        MockDB.return_value.execute_query.return_value = []

        result = UserService().edit_profile("nobody", name="Ghost")

        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "User not found.")

    @patch("backend.user_service.Neo4jConnection")
    def test_edit_none_params_passed_when_no_args(self, MockDB):
        MockDB.return_value.execute_query.return_value = []

        UserService().edit_profile("alice")

        params = MockDB.return_value.execute_query.call_args[0][1]
        self.assertIsNone(params["name"])
        self.assertIsNone(params["email"])
        self.assertIsNone(params["bio"])

    @patch("backend.user_service.Neo4jConnection")
    def test_edit_profile_query_uses_coalesce_and_set(self, MockDB):
        MockDB.return_value.execute_query.return_value = []

        UserService().edit_profile("alice")

        query = MockDB.return_value.execute_query.call_args[0][0]
        self.assertIn("SET", query)
        self.assertIn("coalesce", query.lower())


class TestSearchUsers(unittest.TestCase):
    """UC-10: MATCH (u:User) WHERE toLower(u.*) CONTAINS toLower($search_text) LIMIT $limit"""

    @patch("backend.user_service.Neo4jConnection")
    def test_search_returns_matches(self, MockDB):
        MockDB.return_value.execute_query.return_value = [
            {"userId": 1, "username": "alice", "name": "Alice", "email": "a@a.com", "bio": ""},
            {"userId": 2, "username": "alice2", "name": "Alice Two", "email": "b@b.com", "bio": ""},
        ]

        result = UserService().search_users("alice")

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["username"], "alice")

    @patch("backend.user_service.Neo4jConnection")
    def test_search_returns_empty_when_no_match(self, MockDB):
        MockDB.return_value.execute_query.return_value = []

        result = UserService().search_users("zzznomatch")

        self.assertEqual(result, [])

    @patch("backend.user_service.Neo4jConnection")
    def test_search_default_limit_is_10(self, MockDB):
        MockDB.return_value.execute_query.return_value = []

        UserService().search_users("alice")

        params = MockDB.return_value.execute_query.call_args[0][1]
        self.assertEqual(params["limit"], 10)

    @patch("backend.user_service.Neo4jConnection")
    def test_search_custom_limit_is_respected(self, MockDB):
        MockDB.return_value.execute_query.return_value = []

        UserService().search_users("alice", limit=5)

        params = MockDB.return_value.execute_query.call_args[0][1]
        self.assertEqual(params["limit"], 5)

    @patch("backend.user_service.Neo4jConnection")
    def test_search_passes_search_text_param(self, MockDB):
        MockDB.return_value.execute_query.return_value = []

        UserService().search_users("bob")

        params = MockDB.return_value.execute_query.call_args[0][1]
        self.assertEqual(params["search_text"], "bob")

    @patch("backend.user_service.Neo4jConnection")
    def test_search_query_uses_toLower_contains_for_case_insensitivity(self, MockDB):
        MockDB.return_value.execute_query.return_value = []

        UserService().search_users("Alice")

        query = MockDB.return_value.execute_query.call_args[0][0]
        self.assertIn("toLower", query)
        self.assertIn("CONTAINS", query)

    @patch("backend.user_service.Neo4jConnection")
    def test_search_query_checks_both_name_and_username(self, MockDB):
        MockDB.return_value.execute_query.return_value = []

        UserService().search_users("alice")

        query = MockDB.return_value.execute_query.call_args[0][0]
        self.assertIn("u.name", query)
        self.assertIn("u.username", query)


if __name__ == "__main__":
    unittest.main()
