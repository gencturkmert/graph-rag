from neo4j import GraphDatabase
from lxml import etree
import gzip

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.neo_utils import get_driver

# Function to clear the existing data in the Neo4j database
def clear_database(driver):
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")

# Function to insert data from dblp.xml.gz into Neo4j
def insert_dblp_data(driver, file_path):
    with gzip.open(file_path, 'rb') as f:
        context = etree.iterparse(f, events=('end',), tag='article')
        for event, elem in context:
            title = elem.find('title').text if elem.find('title') is not None else ''
            year = elem.find('year').text if elem.find('year') is not None else ''
            journal = elem.find('journal').text if elem.find('journal') is not None else ''
            volume = elem.find('volume').text if elem.find('volume') is not None else ''
            number = elem.find('number').text if elem.find('number') is not None else ''
            pages = elem.find('pages').text if elem.find('pages') is not None else ''
            url = elem.find('url').text if elem.find('url') is not None else ''
            authors = [author.text for author in elem.findall('author')]
            insert_article(driver, title, year, journal, volume, number, pages, url, authors)
            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]

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
    
    file_path = '../data/dblp.xml.gz'  # Path to your dblp.xml.gz file

    driver = get_driver()
    clear_database(driver)
    insert_dblp_data(driver, file_path)

    driver.close()

if __name__ == "__main__":
    main()
