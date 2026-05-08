import os
import csv
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE")

USERS_CSV = "data/users.csv"
FOLLOWS_CSV = "data/follows.csv"


def clear_database(tx):
    tx.run("MATCH (n) DETACH DELETE n")


def create_constraints(tx):
    tx.run("""
        CREATE CONSTRAINT user_id_unique IF NOT EXISTS
        FOR (u:User)
        REQUIRE u.userId IS UNIQUE
    """)

    tx.run("""
        CREATE CONSTRAINT username_unique IF NOT EXISTS
        FOR (u:User)
        REQUIRE u.username IS UNIQUE
    """)



# create User nodes
def load_users(driver): 
    with open(USERS_CSV, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        users = list(reader)

    query = """
    UNWIND $rows AS row
    MERGE (u:User {userId: toInteger(row.userId)})
    SET u.username = row.username,
        u.name = row.name,
        u.email = row.email,
        u.password = row.password,
        u.bio = row.bio
    """

    with driver.session(database=NEO4J_DATABASE) as session:
        for i in range(0, len(users), 1000):
            batch = users[i:i + 1000]
            session.run(query, rows=batch)

    print(f"Loaded {len(users)} users")


def load_follows(driver):
    with open(FOLLOWS_CSV, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        relationships = list(reader)

    query = """
    UNWIND $rows AS row
    MATCH (source:User {userId: toInteger(row.source)})
    MATCH (target:User {userId: toInteger(row.target)})
    MERGE (source)-[:FOLLOWS]->(target)
    """

    with driver.session(database=NEO4J_DATABASE) as session:
        for i in range(0, len(relationships), 5000):
            batch = relationships[i:i + 5000]
            session.run(query, rows=batch)

    print(f"Loaded {len(relationships)} follows relationships")


def verify_counts(driver):
    with driver.session(database=NEO4J_DATABASE) as session:
        user_count = session.run(
            "MATCH (u:User) RETURN count(u) AS count"
        ).single()["count"]

        follows_count = session.run(
            "MATCH ()-[r:FOLLOWS]->() RETURN count(r) AS count"
        ).single()["count"]

    print("Final database counts:")
    print(f"Users: {user_count}")
    print(f"FOLLOWS relationships: {follows_count}")


def main():
    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASSWORD)
    )

    try:
        with driver.session(database=NEO4J_DATABASE) as session:
            print("Clearing old database...")
            session.execute_write(clear_database)

            print("Creating constraints...")
            session.execute_write(create_constraints)

        print("Loading users...")
        load_users(driver)

        print("Loading follows relationships...")
        load_follows(driver)

        verify_counts(driver)

    finally:
        driver.close()


if __name__ == "__main__":
    main()