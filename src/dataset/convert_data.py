import sys
import os
import networkx as nx
import pandas as pd
from neo4j import GraphDatabase

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.neo_utils import get_driver

def neo4j_to_networkx(driver):
    graph = nx.DiGraph()  # Directed graph since citations are directional

    def add_nodes(tx):
        query = """
        MATCH (a:Article) 
        RETURN id(a) as id, 
               a.title as title, 
               a.year as year, 
               a.journal as journal, 
               a.volume as volume, 
               a.pages as pages, 
               a.url as url
        """
        result = tx.run(query)
        for record in result:
            node_key = record["id"]
            node_data = {
                "title": record.get("title", None),
                "year": record.get("year", None),
                "journal": record.get("journal", None),
                "volume": record.get("volume", None),
                "pages": record.get("pages", None),
                "url": record.get("url", None)
            }
            # Remove None values from node_data
            node_data = {k: v for k, v in node_data.items() if v is not None}
            graph.add_node(node_key, **node_data)

    def add_edges(tx):
        query = """
        MATCH (a:Article)-[r:CITES]->(b:Article) 
        RETURN id(a) as source, id(b) as target
        UNION
        MATCH (author:Person)-[r:AUTHORED]->(a:Article)
        RETURN id(author) as source, id(a) as target
        """
        result = tx.run(query)
        for record in result:
            source = record["source"]
            target = record["target"]
            graph.add_edge(source, target)
            
    def add_authors(tx):
        query = """
        MATCH (a:Article)<-[:AUTHORED]-(author:Person)
        RETURN id(a) as article_id, collect(author.name) as authors
        """
        result = tx.run(query)
        for record in result:
            article_key = record["article_id"]
            authors = record["authors"]
            if graph.has_node(article_key):
                graph.nodes[article_key]["authors"] = authors

    with driver.session() as session:
        session.read_transaction(add_nodes)
        session.read_transaction(add_edges)
        session.read_transaction(add_authors)

    return graph

def main():
    driver = get_driver()
    networkx_graph = neo4j_to_networkx(driver)
    driver.close()

    # You can now work with the `networkx_graph` as needed, for example, print the number of nodes and edges
    print(f"Number of nodes: {len(networkx_graph.nodes)}")
    print(f"Number of edges: {len(networkx_graph.edges)}")

if __name__ == "__main__":
    main()

