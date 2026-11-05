import torch
from torch import nn

x = torch.tensor([[1.0], [2.0], [3.0]])
y = torch.tensor([[3.0], [5.0], [7.0]])
model = nn.Linear(1, 1)
pred = model(x)
print(pred)