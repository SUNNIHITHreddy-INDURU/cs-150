'''

Use cases: handles all graph-related operations

UC-5 : Follow Another User
UC-6 : Unfollow User
UC-7 : View Friends / Connections
UC-8 : Mutual Connections
UC-9 : Friend Recommendations
UC-11: Explore Popular Users

'''

from backend.db_connection import Neo4jConnection


class GraphService:
    def __init__(self):
        self.db = Neo4jConnection()

    def close(self):
        self.db.close()

        # UC-5: Follow Another User
    def follow_user(self, current_username, target_username):
        if current_username == target_username:
            return {
                "success": False,
                "message": "You cannot follow yourself."
            }

        query = """
        MATCH (current:User {username: $current_username})
        MATCH (target:User {username: $target_username})
        MERGE (current)-[:FOLLOWS]->(target)
        RETURN current.username AS currentUser,
               target.username AS followedUser
        """

        result = self.db.execute_query(query, {
            "current_username": current_username,
            "target_username": target_username
        })

        if result:
            return {
                "success": True,
                "message": f"{current_username} now follows {target_username}.",
                "data": result[0]
            }

        return {
            "success": False,
            "message": "One or both users were not found."
        }

    # UC-6: Unfollow User
    def unfollow_user(self, current_username, target_username):
        query = """
        MATCH (current:User {username: $current_username})
              -[r:FOLLOWS]->
              (target:User {username: $target_username})
        DELETE r
        RETURN current.username AS currentUser,
               target.username AS unfollowedUser
        """

        result = self.db.execute_query(query, {
            "current_username": current_username,
            "target_username": target_username
        })

        if result:
            return {
                "success": True,
                "message": f"{current_username} unfollowed {target_username}.",
                "data": result[0]
            }

        return {
            "success": False,
            "message": "Follow relationship not found."
        }

    # UC-7: View Friends/Connections
    def view_connections(self, username, limit=20):
        query = """
        MATCH (u:User {username: $username})

        OPTIONAL MATCH (u)-[:FOLLOWS]->(following:User)
        WITH u, collect(DISTINCT {
            userId: following.userId,
            username: following.username,
            name: following.name
        }) AS followingList

        OPTIONAL MATCH (follower:User)-[:FOLLOWS]->(u)
        RETURN followingList AS following,
               collect(DISTINCT {
                   userId: follower.userId,
                   username: follower.username,
                   name: follower.name
               }) AS followers
        """

        result = self.db.execute_query(query, {
            "username": username,
            "limit": limit
        })

        if result:
            return {
                "success": True,
                "connections": result[0]
            }

        return {
            "success": False,
            "message": "User not found."
        }

    # UC-8: Mutual Connections
    def mutual_connections(self, username1, username2, limit=20):
        query = """
        MATCH (u1:User {username: $username1})-[:FOLLOWS]->(mutual:User)
        MATCH (u2:User {username: $username2})-[:FOLLOWS]->(mutual)
        RETURN mutual.userId AS userId,
               mutual.username AS username,
               mutual.name AS name
        LIMIT $limit
        """

        result = self.db.execute_query(query, {
            "username1": username1,
            "username2": username2,
            "limit": limit
        })

        return {
            "success": True,
            "mutual_connections": result
        }

    # UC-9: Friend Recommendations
    def recommend_users(self, username, limit=10):
        query = """
        MATCH (u:User {username: $username})-[:FOLLOWS]->(:User)-[:FOLLOWS]->(rec:User)
        WHERE rec.username <> $username
          AND NOT (u)-[:FOLLOWS]->(rec)
        RETURN rec.userId AS userId,
               rec.username AS username,
               rec.name AS name,
               count(*) AS mutualConnectionCount
        ORDER BY mutualConnectionCount DESC
        LIMIT $limit
        """

        result = self.db.execute_query(query, {
            "username": username,
            "limit": limit
        })

        return {
            "success": True,
            "recommendations": result
        }

    # UC-11: Explore Popular Users
    def popular_users(self, limit=10):
        query = """
        MATCH (u:User)
        OPTIONAL MATCH (:User)-[:FOLLOWS]->(u)
        RETURN u.userId AS userId,
               u.username AS username,
               u.name AS name,
               count(*) AS followerCount
        ORDER BY followerCount DESC
        LIMIT $limit
        """

        result = self.db.execute_query(query, {
            "limit": limit
        })

        return {
            "success": True,
            "popular_users": result
        }