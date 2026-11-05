import math

import torch
from torch import nn
import matplotlib.pyplot as plt

d_model = 512
emb_large = nn.Embedding(100, d_model)
sample = emb_large(torch.tensor([1]))

print(f"未缩放的标准差：{sample.std().item():.4f}")          # ≈ 1.0
sample_scaled = sample * math.sqrt(d_model)
print(f"缩放后的标准差：{sample_scaled.std().item():.4f}")    # ≈ 22.6
print(f"缩放因子 sqrt({d_model}) = {math.sqrt(d_model):.2f}")
print(f'张量: {torch.tensor([[1,2,3],[4,5,6]])}')

attn=torch.tensor([[1,2,3],[4,5,6]])
plt.imshow(attn.detach().cpu().numpy(), cmap="viridis")
plt.colorbar()
plt.savefig("attention.png")