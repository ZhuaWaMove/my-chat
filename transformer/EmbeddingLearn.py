# 词表大小 10，向量维度 4
import torch
from torch import nn

# 
emb_layer = nn.Embedding(num_embeddings=768, embedding_dim=4)

print("Embedding 权重矩阵形状：", emb_layer.weight.shape)  # (10, 4)

input_ids = torch.tensor([3, 0, 7])
outputs = emb_layer(input_ids)

print(f"输出形状: {outputs.shape}")  # (3, 4)

# 验证：Embedding 本质就是查表
print(torch.equal(emb_layer.weight.data[3], outputs.data[0]))  # True