from neo4j import GraphDatabase
from lxml import etree
import gzip
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

# Function to insert data from dblp.xml into Neo4j
def insert_dblp_data(driver, file_path):
    batch_size = 500  # Adjust the batch size as needed
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        context = etree.iterparse(file_path, events=('end',), tag='article')
        context_size = sum(1 for _ in context)
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
                executor.submit(insert_articles_batch, driver, batch)
                print(f"Inserted batch of {batch_size} articles")
                batch = []
        if batch:
            insert_articles_batch(driver, batch)
            print(f"Inserted final batch of {len(batch)} articles")

# Function to insert a batch of articles into Neo4j
def insert_articles_batch(driver, batch):
    with driver.session() as session:
        for article in batch:
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
            for author in article['authors']:
                session.run(
                    "MERGE (p:Person {name: $name})",
                    name=author
                )
                session.run(
                    """
                    MATCH (a:Article {title: $title}), (p:Person {name: $name})
                    CREATE (p)-[:AUTHORED]->(a)
                    """,
                    title=article['title'], name=author
                )
            for citation in article['citations']:
                session.run(
                    "MERGE (c:Article {title: $title})",
                    title=citation
                )
                session.run(
                    """
                    MATCH (a:Article {title: $title}), (c:Article {title: $citation})
                    CREATE (a)-[:CITES]->(c)
                    """,
                    title=article['title'], citation=citation
                )

# Function to insert a single article into Neo4j
def insert_article(driver, title, year, journal, volume, number, pages, url, authors):
    with driver.session() as session:
        session.run(
            """
            CREATE (a:Article {
                title: $title,
                year: $year,
                journal: $journal,
                volume: $volume,
                number: $number,
                pages: $pages,
                url: $url
            })
            """,
            title=title, year=year, journal=journal, volume=volume, number=number, pages=pages, url=url
        )
        for author in authors:
            session.run(
                "MERGE (p:Person {name: $name})",
                name=author
            )
            session.run(
                """
                MATCH (a:Article {title: $title}), (p:Person {name: $name})
                CREATE (p)-[:AUTHORED]->(a)
                """,
                title=title, name=author
            )

def main():
    file_path = '/home/mertgencturk/graph-rag/src/dataset/data/dblp.xml'
    driver = get_driver()
    clear_database(driver)
    insert_dblp_data(driver, file_path)
    print("DBLP data inserted")
    driver.close()
    print("Driver closed")

if __name__ == "__main__":
    main()
