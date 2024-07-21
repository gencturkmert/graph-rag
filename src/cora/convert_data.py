import sys
import os
import networkx as nx
import pandas as pd
from neo4j import GraphDatabase

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.neo_utils import get_driver

# We can directly convert neo4j data to pyg geometric data. for sake of simplcitiy I used networkx for now.

def neo4j_to_networkx(driver):
    graph = nx.DiGraph()  # Directed graph since citations are directional
    
    def add_nodes(tx):
        query = "MATCH (p:Publication) RETURN p.id as id"
        result = tx.run(query)
        for record in result:
            graph.add_node(record["id"])
    
    def add_edges(tx):
        query = "MATCH (a:Publication)-[:CITES]->(b:Publication) RETURN a.id as source, b.id as target"
        result = tx.run(query)
        for record in result:
            graph.add_edge(record["source"], record["target"])
    
    with driver.session() as session:
        session.execute_read(add_nodes)
        session.execute_read(add_edges)
    
    return graph

def test_neo4j_to_networkx(driver):
    content_file = 'data/cora/cora.content'
    citation_file = 'data/cora/cora.cites'
    
    content_data = pd.read_csv(content_file, sep='\t', header=None)
    content_data.columns = ['id'] + ['word_' + str(i) for i in range(content_data.shape[1] - 2)] + ['class_label']
    
    citation_data = pd.read_csv(citation_file, sep='\t', header=None)
    citation_data.columns = ['from', 'to']
    
    # Convert Neo4j to NetworkX
    cora_networkx = neo4j_to_networkx(driver)
    
    # Check if all nodes are present
    assert len(cora_networkx.nodes) == len(content_data), f"Node count mismatch: {len(cora_networkx.nodes)} != {len(content_data)}"
    for node_id in content_data['id']:
        assert node_id in cora_networkx.nodes, f"Node {node_id} not found in NetworkX graph"
    
    # Check if all edges are present
    assert len(cora_networkx.edges) == len(citation_data), f"Edge count mismatch: {len(cora_networkx.edges)} != {len(citation_data)}"
    for _, row in citation_data.iterrows():
        assert cora_networkx.has_edge(row['from'], row['to']), f"Edge from {row['from']} to {row['to']} not found in NetworkX graph"
    
    print("All tests passed!")


if __name__ == "__main__":
    driver = get_driver()

    cora_networkx = neo4j_to_networkx(driver)
    test_neo4j_to_networkx(driver)

    driver.close()
