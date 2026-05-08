"""
Console-based UI for the social network app.

Two menus:
  - Pre-login menu: register, login, search, popular users, exit
  - Post-login menu: all logged-in user actions

Every menu option maps to a single use case from the spec.
"""
from getpass import getpass

from backend.user_service import UserService
from backend.graph_service import GraphService

_user_service = UserService()
_graph_service = GraphService()


def _input(prompt: str) -> str:
    return input(prompt).strip()


def _pause() -> None:
    input("\n(press Enter to continue) ")


def _print_users(rows: list, empty_msg: str = "No users found.") -> None:
    if not rows:
        print(f"  {empty_msg}")
        return
    for r in rows:
        name     = r.get("name")     or "(no name)"
        username = r.get("username") or "(no username)"
        uid      = r.get("userId")
        extra    = ""
        if "followerCount" in r:
            extra = f"  followers={r['followerCount']}"
        elif "mutualConnectionCount" in r:
            extra = f"  via {r['mutualConnectionCount']} mutual friend(s)"
        print(f"  [{uid}] @{username} — {name}{extra}")


# ---------------------------------------------------------------------------
# Pre-login actions
# ---------------------------------------------------------------------------

def menu_register() -> None:
    while True:
        print("\n--- Register ---")
        print("(Type 'back' in any field to return to the main menu.)")

        name = _input("Name: ")
        if name.lower() == "back":
            return

        email = _input("Email: ")
        if email.lower() == "back":
            return

        username = _input("Username: ")
        if username.lower() == "back":
            return

        password = getpass("Password: ")

        bio = _input("Bio (optional): ")
        if bio.lower() == "back":
            return

        result = _user_service.register_user(
            name=name, email=email, username=username, password=password, bio=bio
        )
        print(f"\n{result['message']}")

        if result["success"]:
            _pause()
            return

        _pause()


def menu_login() -> dict | None:
    while True:
        print("\n--- Login ---")
        print("(Type 'back' in any field to return to the main menu.)")

        username = _input("Username: ")
        if username.lower() == "back":
            return None

        while True:
            password = getpass("Password (or type 'back' to change username): ")
            if password.lower() == "back":
                break

            result = _user_service.login_user(username, password)
            print(f"\n{result['message']}")

            if result["success"]:
                return result["user"]

            print("Incorrect password. Please try again.")
            _pause()



# Post-login actions
def menu_view_profile(current_user: dict) -> None:
    print("\n--- My Profile ---")
    result = _user_service.view_profile(current_user["username"])
    if not result["success"]:
        print(f"  {result['message']}")
        _pause()
        return
    p = result["profile"]
    print(f"  userId:   {p.get('userId')}")
    print(f"  username: @{p.get('username')}")
    print(f"  name:     {p.get('name')     or '(not set)'}")
    print(f"  email:    {p.get('email')    or '(not set)'}")
    print(f"  bio:      {p.get('bio')      or '(not set)'}")
    _pause()


def menu_edit_profile(current_user: dict) -> None:
    while True:
        print("\n--- Edit Profile ---")
        print("Select a field to edit:")
        print(f" 1. Name: {current_user.get('name') or '(not set)'}")
        print(f" 2. Email: {current_user.get('email') or '(not set)'}")
        print(f" 3. Bio: {current_user.get('bio') or '(not set)'}")
        print(f" 0. Back")
        choice = _input("> ")

        if choice == "0":
            return

        if choice not in ("1", "2", "3"):
            print("  Invalid option.")
            continue

        if choice == "1":
            field = "name"
            print(f"  Current name: {current_user.get('name') or '(not set)'}")
        elif choice == "2":
            field = "email"
            print(f"  Current email: {current_user.get('email') or '(not set)'}")
        elif choice == "3":
            field = "bio"
            print(f"  Current bio: {current_user.get('bio') or '(not set)'}")

        new_value = _input(f"New {field}: ").strip() or None

        result = _user_service.edit_profile(
            username=current_user["username"],
            **{field: new_value}
        )
        if result["success"]:
            current_user.update(result["profile"])
            if choice == "1":
                print(f"\n New name has been changed to {new_value}")
            elif choice == "2":
                print(f"\n New email has been changed to {new_value}")
            elif choice == "3":
                print(f"\n New bio has been changed to {new_value}")
        else:
            print(f"\n{result['message']}")
        _pause()


def menu_follow(current_user: dict) -> None:
    print("\n--- Follow a User ---")
    target = _input("Enter username to follow: ")
    result = _graph_service.follow_user(current_user["username"], target)
    print(f"\n{result['message']}")
    _pause()


def menu_unfollow(current_user: dict) -> None:
    print("\n--- Unfollow a User ---")
    target = _input("Enter username to unfollow: ")
    result = _graph_service.unfollow_user(current_user["username"], target)
    print(f"\n{result['message']}")
    _pause()


def menu_view_connections(current_user: dict) -> None:
    print("\n--- My Connections ---")
    result = _graph_service.view_connections(current_user["username"])
    if not result["success"]:
        print(f"  {result['message']}")
        _pause()
        return
    connections = result["connections"]
    print("\nFollowing:")
    _print_users(connections["following"], empty_msg="You are not following anyone yet.")
    print("\nFollowers:")
    _print_users(connections["followers"], empty_msg="You have no followers yet.")
    _pause()


def menu_mutual(current_user: dict) -> None:
    print("\n--- Mutual Connections ---")
    other = _input("Enter the other user's username: ")
    result = _graph_service.mutual_connections(current_user["username"], other)
    print(f"\nMutual connections with @{other}:")
    _print_users(result["mutual_connections"], empty_msg="No mutual connections found.")
    _pause()


def menu_recommendations(current_user: dict) -> None:
    print("\n--- Friend Recommendations ---")
    result = _graph_service.recommend_users(current_user["username"])
    print("People you might want to follow:")
    _print_users(result["recommendations"], empty_msg="No recommendations available yet.")
    _pause()


def menu_search() -> None:
    print("\n--- Search Users ---")
    term = _input("Search by username or name: ")
    rows = _user_service.search_users(term)
    print(f"\nResults for '{term}':")
    _print_users(rows, empty_msg="No matching users.")
    _pause()


def menu_popular() -> None:
    print("\n--- Most-Followed Users ---")
    result = _graph_service.popular_users()
    _print_users(result["popular_users"], empty_msg="No users in the database.")
    _pause()


# 
# Menu loops
# 

def post_login_loop(current_user: dict) -> None:
    while True:
        print(f"\n========== Logged in as @{current_user['username']} ==========")
        print(" 1. View my profile           (UC-3)")
        print(" 2. Edit my profile           (UC-4)")
        print(" 3. Follow a user             (UC-5)")
        print(" 4. Unfollow a user           (UC-6)")
        print(" 5. View following/followers  (UC-7)")
        print(" 6. View mutual connections   (UC-8)")
        print(" 7. Friend recommendations    (UC-9)")
        print(" 8. Search users              (UC-10)")
        print(" 9. Popular users             (UC-11)")
        print(" 0. Logout")
        choice = _input("> ")

        if   choice == "1": menu_view_profile(current_user)
        elif choice == "2": menu_edit_profile(current_user)
        elif choice == "3": menu_follow(current_user)
        elif choice == "4": menu_unfollow(current_user)
        elif choice == "5": menu_view_connections(current_user)
        elif choice == "6": menu_mutual(current_user)
        elif choice == "7": menu_recommendations(current_user)
        elif choice == "8": menu_search()
        elif choice == "9": menu_popular()
        elif choice == "0":
            print(f"\n  Logged out. Goodbye, @{current_user['username']}!")
            return
        else:
            print("  Invalid option.")


def main_loop() -> None:
    while True:
        print("\n========== Social Network ==========")
        print(" 1. Register                 (UC-1)")
        print(" 2. Login                    (UC-2)")
        print(" 3. Search users             (UC-10)")
        print(" 4. Popular users            (UC-11)")
        print(" 0. Exit")
        choice = _input("> ")

        if choice == "1":
            menu_register()
        elif choice == "2":
            user = menu_login()
            if user:
                post_login_loop(user)
        elif choice == "3":
            menu_search()
        elif choice == "4":
            menu_popular()
        elif choice == "0":
            print("\nGoodbye.")
            _user_service.close()
            _graph_service.close()
            return
        else:
            print("  Invalid option.")
