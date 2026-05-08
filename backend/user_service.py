
'''
Use cases: handles all user-related opereations

UC-1 : User Registration
UC-2 : User Login
UC-3 : View Profile
UC-4 : Edit Profile
UC-10: Search Users

'''
from backend.db_connection import Neo4jConnection



class UserService:
    def __init__(self):
        self.db = Neo4jConnection()

    def close(self):
        self.db.close()

    # UC-1: User Registration
    def register_user(self, name, email, username, password, bio=""):
        query = """
        CREATE (u:User {
            userId: $user_id,
            name: $name,
            email: $email,
            username: $username,
            password: $password,
            bio: $bio
        })
        RETURN u
        """
        try:
            id_result = self.db.execute_query(
                "MATCH (u:User) RETURN coalesce(max(u.userId), 0) + 1 AS next_id", {}
            )
            user_id = id_result[0]["next_id"]

            result = self.db.execute_query(query, {
                "user_id": user_id,
                "name": name,
                "email": email,
                "username": username,
                "password": password,
                "bio": bio
            })

            return {
                "success": True,
                "message": "User registered successfully.",
                "data": result
            }

        except Exception as e:
            if "ConstraintValidationFailed" in str(e):
                return {
                    "success": False,
                    "message": "Username or email already taken. Please choose a different one."
                }
            return {
                "success": False,
                "message": f"Registration failed: {e}"
            }

    # UC-2: User Login
    def login_user(self, username, password):
        query = """
        MATCH (u:User {username: $username, password: $password})
        RETURN u.userId AS userId,
               u.username AS username,
               u.name AS name,
               u.email AS email,
               u.bio AS bio
        """

        result = self.db.execute_query(query, {
            "username": username,
            "password": password
        })

        if result:
            return {
                "success": True,
                "message": "Login successful.",
                "user": result[0]
            }

        return {
            "success": False,
            "message": "Invalid username or password."
        }

    # UC-3: View Profile
    def view_profile(self, username):
        query = """
        MATCH (u:User {username: $username})
        RETURN u.userId AS userId,
               u.username AS username,
               u.name AS name,
               u.email AS email,
               u.bio AS bio
        """

        result = self.db.execute_query(query, {
            "username": username
        })

        if result:
            return {
                "success": True,
                "profile": result[0]
            }

        return {
            "success": False,
            "message": "User not found."
        }

    # UC-4: Edit Profile
    def edit_profile(self, username, name=None, email=None, bio=None):
        query = """
        MATCH (u:User {username: $username})
        SET u.name = coalesce($name, u.name),
            u.email = coalesce($email, u.email),
            u.bio = coalesce($bio, u.bio)
        RETURN u.userId AS userId,
               u.username AS username,
               u.name AS name,
               u.email AS email,
               u.bio AS bio
        """

        result = self.db.execute_query(query, {
            "username": username,
            "name": name,
            "email": email,
            "bio": bio
        })

        if result:
            return {
                "success": True,
                "message": "Profile updated successfully.",
                "profile": result[0]
            }

        return {
            "success": False,
            "message": "User not found."
        }

    # UC-10: Search Users
    def search_users(self, search_text, limit=10):
        query = """
        MATCH (u:User)
        WHERE toLower(u.name) CONTAINS toLower($search_text)
           OR toLower(u.username) CONTAINS toLower($search_text)
        RETURN u.userId AS userId,
               u.username AS username,
               u.name AS name,
               u.email AS email,
               u.bio AS bio
        LIMIT $limit
        """

        return self.db.execute_query(query, {
            "search_text": search_text,
            "limit": limit
        })