import sys
import os
import networkx as nx
import pandas as pd
from neo4j import GraphDatabase
from tqdm import tqdm
import json
from llama_index.vector_stores.neo4jvector import Neo4jVectorStore
from llama_index.core.schema import TextNode
from llama_index.core import VectorStoreIndex


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.neo_utils import *
from src.utils.json import *
from src.models.informax.dgi import *
from src.models.embedding.embedding_model import *
from src.models.llama import *
from src.cora.convert_data import *


class RAG:
    def __init__():
        self.driver = None
        self.vector_store = None
        self.dgi = None
        self.embeddings = None
        self.llm = None
        self.tokenizer = None
        self.index = None
        self.query_engine = None
        self.data_nx = None
        self.embedding_dim = 64
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {self.device}")
        
        self._init_driver()
        self._init_data()
        self._init_dgi()
        self._init_vector_store()
        self._init_llm()
        
    def _init_driver():
        self.driver = get_driver()
        
    def _init_vector_store(self):
        url, user, password = get_creds()
        self.vector_store = Neo4jVectorStore(
            url=url,
            username=user,
            password=password,
            embedding_dimension=self.embedding_dim,
            index_name="graph_vector_index",
            node_label="GraphNode",
        )
        
    def _init_llm():
        self.llm, self.tokenizer = get_llama_model(device = self.device)
    
    def _init_data():
        self.data_nx = neo4j_to_networkx(self.driver)
        
    def _init_dgi():
        self.dgi = DGIWrapper(self.data_nx,self.device)
        
        
    def train_dgi():
        self.dgi.train_model()
        
    def fetch_embeddings(save=False):
        self.embeddings = self.dgi.get_embeddings(save)
    
    def add_to_vector_store(self):
        if self.data_nx is None or self.embeddings is None:
            raise ValueError(
                "Graph data or embeddings not created."
            )

        batch_size = 1000
        nodes = list(self.data_nx.nodes(data=True))
        for i in tqdm(range(0, len(nodes), batch_size), desc="Adding to vector store"):
            batch = nodes[i : i + batch_size]
            nodes_to_add = []
            for node in batch:
                node_id, node_data = node
                embedding = self.embeddings[node_id].tolist()

                json_safe_props = json.loads(json.dumps(node_data, cls=CustomJSONEncoder))

                text = f"Node ID: {node_id}, Label: {json_safe_props['label']}, "
                text += ", ".join([f"{k}: {v}" for k, v in json_safe_props.items() if k != "label"])

                metadata = {
                    "node_id": node_id,
                    "label": json_safe_props["label"],
                }
                metadata.update({k: v for k, v in json_safe_props.items() if k != "label"})

                text_node = TextNode(text=text, embedding=embedding, metadata=metadata)
                nodes_to_add.append(text_node)

            self.vector_store.add(nodes_to_add)
            
    def init_index_and_query_engine(self):
        embed_model = PrecomputedEmbedding(self.embeddings)

        self.index = VectorStoreIndex.from_vector_store(self.vector_store, embed_model=embed_model)
        self.query_engine = self.index.as_query_engine(llm=self.llm)

    def run_prompt(self, prompt):
        response = self.query_engine.query(prompt)
        print("Response:", response)

        
        
        