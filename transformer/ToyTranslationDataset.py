import torch
from torch import nn
from torch.utils import data
from torch.utils.data import DataLoader


def build_vocab(raw_data):
    """构建源/目标词表及反向词表"""
    src_vocab = {'<pad>': 0, '<sos>': 1, '<eos>': 2}
    tgt_vocab = {'<pad>': 0, '<sos>': 1, '<eos>': 2}

    for src, tar in raw_data:
        for word in src.split():          # 英文按空格分词
            if word not in src_vocab:
                src_vocab[word] = len(src_vocab)
        for ch in tar:                    # 中文按单字
            if ch not in tgt_vocab:
                tgt_vocab[ch] = len(tgt_vocab)

    idx2src = {v: k for k, v in src_vocab.items()}
    idx2tgt = {v: k for k, v in tgt_vocab.items()}
    print(f'源语言词表：{src_vocab}')
    print(f'源语言反向词表：{idx2src}')
    return src_vocab, tgt_vocab, idx2src, idx2tgt


class ToyTranslationDataset(data.Dataset):
    def __init__(self, data_pairs, src_vocab, tgt_vocab):
        self.data_pairs = data_pairs
        self.src_vocab = src_vocab
        self.tgt_vocab = tgt_vocab

    def __len__(self):
        return len(self.data_pairs)

    def __getitem__(self, idx):
        src_text, tgt_text = self.data_pairs[idx]
        src_indices = [self.src_vocab[w] for w in src_text.split()]
        tgt_indices = [self.tgt_vocab[ch] for ch in tgt_text]
        return torch.tensor(src_indices, dtype=torch.long), \
               torch.tensor(tgt_indices, dtype=torch.long)


def make_collate_fn(tgt_vocab):
    """返回一个 collate_fn，闭包捕获 tgt_vocab，避免全局变量"""
    sos_idx = tgt_vocab['<sos>']
    eos_idx = tgt_vocab['<eos>']

    def collate_fn(batch):
        src_batch, tgt_batch = [], []
        for src_sample, tgt_sample in batch:
            src_batch.append(src_sample)
            tgt_processed = torch.cat([
                torch.tensor([sos_idx], dtype=torch.long),
                tgt_sample,
                torch.tensor([eos_idx], dtype=torch.long),
            ])
            tgt_batch.append(tgt_processed)

        src_batch = nn.utils.rnn.pad_sequence(
            src_batch, padding_value=0, batch_first=True)
        tgt_batch = nn.utils.rnn.pad_sequence(
            tgt_batch, padding_value=0, batch_first=True)
        print(f'规整源语言token：{src_batch}')
        print(f'规整目标语言token：{tgt_batch}')
        return src_batch, tgt_batch

    return collate_fn


def main():
    raw_data = [
        ("I love deep learning", "我爱深度学习"),
        ("Transformer is all you need", "你需要的就是变形金刚"),
        ("Attention mechanism is great", "注意力机制很棒"),
        ("hello world", "你好世界"),
        ("PyTorch is easy to learn", "PyTorch很容易学"),
    ]

    src_vocab, tgt_vocab, idx2src, idx2tgt = build_vocab(raw_data)
    print(f"源语言词表大小: {len(src_vocab)}")
    print(f"目标语言词表大小: {len(tgt_vocab)}")

    dataset = ToyTranslationDataset(raw_data, src_vocab, tgt_vocab)
    collate_fn = make_collate_fn(tgt_vocab)

    loader = DataLoader(dataset, batch_size=2, shuffle=False, collate_fn=collate_fn)

    src_batch, tgt_batch = next(iter(loader))
    print("\n处理后 Batch 数据的形状")
    print(f"Source Batch Shape: {src_batch.shape}  (Batch, Src_len)")
    print(f"Target Batch Shape: {tgt_batch.shape}  (Batch, tgt_len)")
    print("\nSource:\n", src_batch)
    print("Target:\n", tgt_batch)

    # Embedding 验证
    emb_layer = nn.Embedding(num_embeddings=10, embedding_dim=4)
    print("\nEmbedding 权重矩阵形状：", emb_layer.weight.shape)  # (10, 4)

    input_ids = torch.tensor([3, 0, 7], dtype=torch.long)
    outputs = emb_layer(input_ids)
    print(f"输出形状: {outputs.shape}")  # (3, 4)
    print("查表验证:", torch.equal(emb_layer.weight.data[3], outputs.data[0]))  # True


if __name__ == "__main__":
    main()