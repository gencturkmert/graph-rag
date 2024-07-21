import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

import logging
from src.utils.neo_utils import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

driver = get_driver()

def count_nodes(tx):
    query = """
    MATCH (p:Publication)
    RETURN count(p) AS node_count
    """
    result = tx.run(query)
    return result.single()[0]

def main():
    with driver.session() as session:
        data = session.execute_read(count_nodes)
    
    print("Number of nodes:",data)

    driver.close()

if __name__ == "__main__":
    main()
