import os
from neo_utils import *

def check_connection():
    try:
        driver = get_driver()
        with driver.session() as session:
            result = session.run("RETURN 1")
            if result.single()[0] == 1:
                print("Connection to Neo4j database is successful.")
            else:
                print("Failed to execute test query.")
        driver.close()
    except Exception as e:
        print(f"Failed to connect to Neo4j database: {e}")

if __name__ == "__main__":
    check_connection()
