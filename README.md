

## What's here

```
SocialNetwork/
├── main.py                    Console UI entry point
├── load_dateset.py            Loads SNAP dataset into Neo4j <- run this file to load dataset into
├── convert_csv.py             Converts raw data to CSV format
├── requirements.txt           Python dependencies
├── .env                       Neo4j credentials (not committed)
├── .gitignore
│
├── backend/
│   ├── __init__.py
│   ├── db_connection.py       Neo4j driver wrapper
│   ├── user_service.py        UC-1, UC-2, UC-3, UC-4 (auth & profile)
│   └── graph_service.py       UC-5..UC-11 (follow, search, recommendations)
│
├── frontend/
│   └── console_menu.py        Console menus and UI logic
│
├── data/
│   ├── facebook_combined.txt  Raw SNAP edge list (not committed)
│   ├── users.csv              Generated user nodes
│   └── follows.csv            Generated follow relationships
│
└── tests/ <- run `python -m unittest discover -s tests -v` to run all unittest
    ├── __init__.py
    ├── test_user_service.py   Tests for auth & profile use cases
    └── test_graph_service.py  Tests for social graph use cases
```

## Prerequisites

- Python 3.10 or newer (uses `dict | None` syntax)
- Neo4j running locally with the SNAP Facebook data. You need to set up your Neo4j instance, edit the .env and then run   ```python load_dataset.py``` to load the data into neo4j database
  (4,039 User nodes, 176,468 FOLLOWS relationships)

## Setup (do this once)

1. **Setup virtual environment**:

    Create virtual environment
       ```
       python -m venv .venv
       ```

    Activate the virtual environment

    - On **Windows**:

      ```powershell
      .\.venv\Scripts\Activate.ps1
      ```

    - On **Mac/Linux**:

      ```bash
      source .venv/bin/activate
      ```

2. **Install dependencies.** From inside the `social_network/` folder:

   ```
   pip install -r requirements.txt
   ```

3. **Create a `.env` file** in the project root with your Neo4j credentials:

   ```
   NEO4J_URI=neo4j://127.0.0.1:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your_password_here
   NEO4J_DATABASE=neo4j
   ```

   > `.env` is listed in `.gitignore` and will never be committed.

4. **Run the schema setup** (idempotent — safe to re-run):

   ```
   python load_dataset.py
   ```

   You should see `[OK]` lines for each constraint and index, plus a
   summary showing 4,039 users and 176,468 relationships.

## Run the app

```bash
python main.py
```

The console menu walks through all 11 use cases.

> **About the existing 4,039 SNAP users:** the SNAP dataset is anonymous,
> so those users have a `userId` (and the `username` your teammate
> generated) but no name, email, password, or bio. They're real nodes in
> the graph and you can follow them, search them, see them as
> recommendations, etc. — but you can't *log in* as one of them, because
> they have no password. Use the Register option to create an account
> with full credentials, then explore.

## Run the tests


```bash
python -m tests.test_use_cases
```

The test script:
- Creates two temporary users (with timestamped usernames so reruns
  don't collide)
- Exercises all 11 use cases end-to-end
- Cleans up after itself
- Prints a `PASS`/`FAIL` line per check and a summary at the end
- Exits with code 0 only if everything passes

## Use cases → file map

| UC   | Description                  | File                    | Key function                      |
|------|------------------------------|-------------------------|-----------------------------------|
| UC-1 | User Registration            | backend/user_service.py | `register_user`                   |
| UC-2 | User Login                   | backend/user_service.py | `login_user`                      |
| UC-3 | View Profile                 | backend/user_service.py | `view_profile`                    |
| UC-4 | Edit Profile                 | backend/user_service.py | `edit_profile`                    |
| UC-5 | Follow Another User          | backend/graph_service.py| `follow_user`                     |
| UC-6 | Unfollow a User              | backend/graph_service.py| `unfollow_user`                   |
| UC-7 | View Following / Followers   | backend/graph_service.py| `get_following` / `get_followers` |
| UC-8 | Mutual Connections           | backend/graph_service.py| `get_mutual_connections`          |
| UC-9 | Friend Recommendations       | backend/graph_service.py| `recommend_friends`               |
| UC-10| Search Users                 | backend/user_service.py | `search_users`                    |
| UC-11| Explore Popular Users        | backend/graph_service.py| `get_popular_users`               |

