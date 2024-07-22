from neo4j import GraphDatabase
from lxml import etree
import sys
import os
import concurrent.futures
from tqdm import tqdm

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from src.utils.neo_utils import get_driver

def clear_database(driver):
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    print("Database cleared")

def insert_articles_batch(driver, batch):
    with driver.session() as session:
        session.run(
            """
            UNWIND $batch as row
            CREATE (a:Article {
                title: row.title,
                year: row.year,
                journal: row.journal,
                volume: row.volume,
                number: row.number,
                pages: row.pages,
                url: row.url
            })
            """,
            batch=batch
        )
        for article in batch:
            for author in article['authors']:
                session.run(
                    """
                    MERGE (p:Person {name: $name})
                    WITH p
                    MATCH (a:Article {title: $title})
                    CREATE (p)-[:AUTHORED]->(a)
                    """,
                    name=author, title=article['title']
                )
            for citation in article['citations']:
                session.run(
                    """
                    MERGE (c:Article {title: $citation})
                    WITH c
                    MATCH (a:Article {title: $title})
                    CREATE (a)-[:CITES]->(c)
                    """,
                    citation=citation, title=article['title']
                )

def insert_dblp_data(driver, file_path):
    batch_size = 100  # Adjust the batch size as needed
    context = etree.iterparse(file_path, events=('end',), tag='article', load_dtd=True)
    context_size = sum(1 for _, _ in context)
    print("Context size:", context_size)
    context = etree.iterparse(file_path, events=('end',), tag='article')

    batch = []
    for event, elem in tqdm(context, total=context_size, desc="Processing articles"):
        article = {
            "title": elem.find('title').text if elem.find('title') is not None else '',
            "year": elem.find('year').text if elem.find('year') is not None else '',
            "journal": elem.find('journal').text if elem.find('journal') is not None else '',
            "volume": elem.find('volume').text if elem.find('volume') is not None else '',
            "number": elem.find('number').text if elem.find('number') is not None else '',
            "pages": elem.find('pages').text if elem.find('pages') is not None else '',
            "url": elem.find('url').text if elem.find('url') is not None else '',
            "authors": [author.text for author in elem.findall('author') if author.text is not None and author.text.strip() != ''],
            "citations": [cite.text for cite in elem.findall('cite') if cite.text is not None and cite.text.strip() != '']
        }
        batch.append(article)
        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]
        if len(batch) >= batch_size:
            insert_articles_batch(driver, batch)
            batch = []
    if batch:
        insert_articles_batch(driver, batch)

def main():
    file_path = '/home/mertgencturk/graph-rag/src/dataset/data/dblp50000.xml'
    driver = get_driver()
    clear_database(driver)
    insert_dblp_data(driver, file_path)
    print("DBLP data inserted")
    driver.close()
    print("Driver closed")

if __name__ == "__main__":
    main()
