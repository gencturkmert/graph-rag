import sys
import os
import torch
import argparse
import networkx as nx
import pandas as pd
import torch
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, DeepGraphInfomax
from torch_geometric.data import Data
from torch_geometric.utils import from_networkx
from torch.cuda.amp import GradScaler, autocast

class Encoder(torch.nn.Module):
    def __init__(self, in_channels, hidden_channels, out_channels, dropout=0.5):
        super(Encoder, self).__init__()
        self.conv1 = GCNConv(in_channels, hidden_channels)
        self.conv2 = GCNConv(hidden_channels, out_channels)
        self.dropout = dropout

    def forward(self, x, edge_index):
        x = F.relu(self.conv1(x, edge_index))
        x = F.dropout(x, self.dropout, training=self.training)
        x = self.conv2(x, edge_index)
        return x

def corruption(x, edge_index):
    return x[torch.randperm(x.size(0))], edge_index

def summary(z, *args, **kwargs):
    return torch.sigmoid(z.mean(dim=0))

def get_dgi_model(in_channels, hidden_channels=64, out_channels=64, dropout=0.5):
    encoder = Encoder(in_channels, hidden_channels, out_channels, dropout)
    dgi_model = DeepGraphInfomax(hidden_channels=out_channels, encoder=encoder, summary=summary, corruption=corruption)
    return dgi_model
    
def nx_to_pyg(nx_graph):
    pyg_data = from_networkx(nx_graph)
    pyg_data.x = torch.eye(pyg_data.num_nodes)
    return pyg_data

class DGIWrapper:
    def __init__(
        self,
        graph,
        device      
    ):
        self.device = device
        self.data_nx = graph
        self.data_pyg = nx_to_pyg(self.data_nx)
        self.dgi_model = get_dgi_model(self.data_pyg.num_features)
        
    def train_model(self):    
        optimizer = torch.optim.Adam(self.dgi_model.parameters(), lr=0.001)
        scaler = GradScaler()
        self.dgi_model.train()
        for epoch in range(100):
            optimizer.zero_grad()
            with autocast():
                pos_z, neg_z, summary = self.dgi_model(self.data_pyg.x.to(self.device), self.data_pyg.edge_index.to(self.device))
                loss = self.dgi_model.loss(pos_z, neg_z, summary)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            print(f'Epoch {epoch+1}, Loss: {loss.item()}')
            
    def get_embeddings(self,save=False):
        self.dgi_model.eval()
        with torch.no_grad():
            z, _, _ = self.dgi_model(self.data_pyg.x.to(self.device), self.data_pyg.edge_index.to(self.device))

        if save:
            os.makedirs("../embeddings", exist_ok=True)
            torch.save(z.cpu(), f"../embeddings/{name}.pt")
            
        embeddings = z.cpu()
        return embeddings
            
        
        
        
        
    
    
