# 构建原始数据集，source 是英文，target 是中文
raw_data = [
    ("I love deep learning", "我爱深度学习"),
    ("Transformer is all you need", "你需要的就是变形金刚"),
    ("Attention mechanism is great", "注意力机制很棒"),
    ("hello world", "你好世界"),
    ("PyTorch is easy to learn", "PyTorch很容易学")
]

# 构建词表
# pad: 填充, sos: 开始, eos: 结束
src_vocab = {'<pad>': 0, '<sos>': 1, '<eos>': 2}
tgt_vocab = {'<pad>': 0, '<sos>': 1, '<eos>': 2}

# 扫描数据集，构建词表
for src, tar in raw_data:
    for word in src.split():  # 英文用空格分词
        if word not in src_vocab:
            src_vocab[word] = len(src_vocab)
    for word in tar:  # 中文按单个字符遍历
        if word not in tgt_vocab:
            tgt_vocab[word] = len(tgt_vocab)

# 创建反向词表（索引 → 单词）
idx2src = {v: k for k, v in src_vocab.items()}
idx2tar = {v: k for k, v in tgt_vocab.items()}

print(f"源语言词表大小: {len(src_vocab)}")
print(f"目标语言词表大小: {len(tgt_vocab)}")

