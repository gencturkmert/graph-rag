import sys
import os
import torch
import argparse
import networkx as nx
import pandas as pd
from torch_geometric.data import Data
from torch.cuda.amp import GradScaler, autocast
from neo4j import GraphDatabase

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.neo_utils import get_driver
from src.cora.convert_data import neo4j_to_networkx
from src.models.informax.dgi import *

def train_model(data, dgi_model, epochs, optimizer, scaler, device):
    dgi_model.train()
    for epoch in range(epochs):
        optimizer.zero_grad()
        with autocast():
            pos_z, neg_z, summary = dgi_model(data.x.to(device), data.edge_index.to(device))
            loss = dgi_model.loss(pos_z, neg_z, summary)
        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()
        print(f'Epoch {epoch+1}, Loss: {loss.item()}')

def generate_embeddings(dgi_model, data, device, name="dgi_embeddings"):
    dgi_model.eval()
    with torch.no_grad():
        z, _, _ = dgi_model(data.x.to(device), data.edge_index.to(device))

    os.makedirs("../embeddings", exist_ok=True)
    torch.save(z.cpu(), f"../embeddings/{name}.pt")
    return z.cpu()

if __name__ == "__main__":
    #device = torch.device(f'cuda:{args.device}' if torch.cuda.is_available() else 'cpu')
    device = "cpu"
    print("Device:",device)

    driver = get_driver()
    nx_graph = neo4j_to_networkx(driver)
    print("nx graph created")
    
    #data = nx_to_pyg(nx_graph)
    #print("torch geometric data assembled")
    
    #dgi_model = get_dgi_model(data.num_features).to(device)
    #optimizer = torch.optim.Adam(dgi_model.parameters(), lr=args.lr)
    #scaler = GradScaler()

    dgi_wrapper = DGIWrapper(nx_graph,"cpu")
    dgi_wrapper.train_model()
    embed = dgi_wrapper.get_embeddings()
    print(embed.shape)

    #train_model(data, dgi_model, args.epochs, optimizer, scaler, device)
    #generate_embeddings(dgi_model, data, device, name=f"dgi_embeddings_epoch_{args.epochs}_lr_{args.lr}")
