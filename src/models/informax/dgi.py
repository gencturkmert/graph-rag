import torch
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, DeepGraphInfomax

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

def get_dgi_model(in_channels, hidden_channels=64, out_channels=64, dropout=0.5, lr=0.001):
    encoder = Encoder(in_channels, hidden_channels, out_channels, dropout)
    dgi_model = DeepGraphInfomax(hidden_channels=out_channels, encoder=encoder, summary=summary, corruption=corruption)
    optimizer = torch.optim.Adam(dgi_model.parameters(), lr=lr)
    
def nx_to_pyg(nx_graph):
    pyg_data = from_networkx(nx_graph)
    pyg_data.x = torch.eye(pyg_data.num_nodes)
    return pyg_data
