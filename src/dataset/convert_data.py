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
               a.volume as volume
        """
        result = tx.run(query)
        for record in result:
            node_key = record["id"]
            node_data = {
                "title": record.get("title", ""),
                "year": record.get("year", ""),
                "journal": record.get("journal", ""),
                "volume": record.get("volume", ""),
                "authors": None  
            }
            graph.add_node(node_key, **node_data)

    def add_edges(tx):
        query = """
        MATCH (a:Article)-[r:CITES]->(b:Article) 
        RETURN id(a) as source, id(b) as target
        """
        result = tx.run(query)
        edge_count = 0 
        for record in result:
            source = record["source"]
            target = record["target"]
            graph.add_edge(source, target)
            edge_count += 1
        
        print(f"Total CITES edges added: {edge_count}")
            
    def add_authors(tx):
        count = 0
        query = """
        MATCH (a:Article)<-[:AUTHORED]-(author:Person)
        RETURN id(a) as article_id, collect(author.name) as authors
        """
        result = tx.run(query)
        for record in result:
            article_key = record["article_id"]
            authors = ', '.join(record["authors"]) 
            if graph.has_node(article_key):
                graph.nodes[article_key]["authors"] = authors
                count+=1
        print("Added author number:",count)

    with driver.session() as session:
        session.read_transaction(add_nodes)
        session.read_transaction(add_authors)
        session.read_transaction(add_edges)

    return graph

def check_uniform_attributes(graph):
    nodes_iter = iter(graph.nodes(data=True))
    _, first_node_data = next(nodes_iter)
    standard_attributes = set(first_node_data.keys())
    count=0
    for node_id, node_data in graph.nodes(data=True):
        node_attributes = set(node_data.keys())
        if node_attributes != standard_attributes:
            count+=1
            """ print(f"Node {node_id} has different attributes.")
            print(f"Expected attributes: {standard_attributes}")
            print(f"Actual attributes: {node_attributes}")
            print() """
            
    print(f"There is {count} nodes with problamtic attributes")

def main():
    driver = get_driver()
    networkx_graph = neo4j_to_networkx(driver)
    driver.close()

    print(f"Number of nodes: {len(networkx_graph.nodes)}")
    print(f"Number of edges: {len(networkx_graph.edges)}")
    
    check_uniform_attributes(networkx_graph)
    
if __name__ == "__main__":
    main()

