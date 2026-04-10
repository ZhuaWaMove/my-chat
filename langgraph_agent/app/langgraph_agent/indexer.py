import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

# 加载环境变量（如 OPENAI_API_KEY）
load_dotenv()

# 定义支持的文件类型及其对应的加载器
LOADER_MAPPING = {
    ".pdf": (PyPDFLoader, {}),
    ".txt": (TextLoader, {"encoding": "utf8"}),
    ".md": (UnstructuredMarkdownLoader, {}),
}

def load_documents(directory):
    """加载指定目录下的所有支持文档"""
    docs = []
    for root, _, files in os.walk(directory):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in LOADER_MAPPING:
                file_path = os.path.join(root, file)
                print(f"Loading: {file_path}")
                loader_class, kwargs = LOADER_MAPPING[ext]
                try:
                    loader = loader_class(file_path, **kwargs)
                    docs.extend(loader.load())
                except Exception as e:
                    print(f"Error loading {file_path}: {e}")
    return docs

def create_vector_store(documents, persist_directory="./chroma_db"):
    """将文档分块并创建向量存储"""
    # 文本分割器，将长文档分割成块
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,      # 每个块的大小[reference:11]
        chunk_overlap=200,    # 块之间的重叠部分[reference:12]
        length_function=len,
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks.")
    
    # 创建嵌入模型和向量数据库
    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_directory,
    )
    vectorstore.persist()
    print(f"Vector store created at {persist_directory}")
    return vectorstore

if __name__ == "__main__":
    # 1. 从 workspace 目录加载文档
    docs = load_documents("./workspace")
    if not docs:
        print("No documents found in ./workspace")
    else:
        # 2. 创建向量数据库
        vectorstore = create_vector_store(docs)