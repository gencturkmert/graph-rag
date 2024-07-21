from dotenv import load_dotenv, find_dotenv
from neo4j import GraphDatabase
import os

def get_driver():
    load_dotenv(find_dotenv())

    uri = os.getenv('NEO4J_URI')
    user = os.getenv('NEO4J_USER')
    password = os.getenv('NEO4J_PASSWORD')

    if not uri or not user or not password:
        raise ValueError("Please set the NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD environment variables in the .env file.")

    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    if driver:
        print("Connection succesfull.")
        
    return driver

def get_creds():
    load_dotenv(find_dotenv())

    uri = os.getenv('NEO4J_URI')
    user = os.getenv('NEO4J_USER')
    password = os.getenv('NEO4J_PASSWORD')
    
    return url, user, password