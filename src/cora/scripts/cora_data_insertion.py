from dotenv import load_dotenv, find_dotenv
import pandas as pd
from neo4j import GraphDatabase
import os

load_dotenv(find_dotenv())

uri = os.getenv('NEO4J_URI')
user = os.getenv('NEO4J_USER')
password = os.getenv('NEO4J_PASSWORD')


driver = GraphDatabase.driver(uri, auth=(user, password))

def insert_publication(tx, publication_id, title, authors):
    query = """
    MERGE (p:Publication {id: $publication_id})
    SET p.title = $title, p.authors = $authors
    """
    tx.run(query, publication_id=publication_id, title=title, authors=authors)

def insert_citation(tx, from_publication, to_publication):
    query = """
    MATCH (a:Publication {id: $from_publication})
    MATCH (b:Publication {id: $to_publication})
    MERGE (a)-[:CITES]->(b)
    """
    tx.run(query, from_publication=from_publication, to_publication=to_publication)

def main():
    content_file = './data/cora/cora.content'
    citation_file = './data/cora/cora.cites'
    
    content_data = pd.read_csv(content_file, sep='\t', header=None)
    content_data.columns = ['id'] + ['word_' + str(i) for i in range(content_data.shape[1] - 2)] + ['class_label']
    
    citation_data = pd.read_csv(citation_file, sep='\t', header=None)
    citation_data.columns = ['from', 'to']
    
    with driver.session() as session:
        for index, row in content_data.iterrows():
            publication_id = row['id']
            title = "Title_" + str(publication_id)  # Placeholder title
            authors = "Author_" + str(publication_id)  # Placeholder authors
            session.write_transaction(insert_publication, publication_id, title, authors)
            
    print("Content is added (nodes)")
    
    with driver.session() as session:
        for index, row in citation_data.iterrows():
            from_publication = row['from']
            to_publication = row['to']
            session.write_transaction(insert_citation, from_publication, to_publication)
            
    print("Citations is added (relations)")
    
    driver.close()
    
    print("connection closed")

if __name__ == "__main__":
    main()
