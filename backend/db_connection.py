'''
- Load environment variables from .env
- Create a Neo4j database driver connection
- Execute Cypher queries
- Return query results to backend services

'''

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")


class Neo4jConnection:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )

    def close(self):
        self.driver.close()

    def execute_query(self, query, parameters=None):
        with self.driver.session(database=NEO4J_DATABASE) as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]