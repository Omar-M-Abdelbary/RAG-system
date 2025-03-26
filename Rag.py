
import faiss
import numpy as np
import ollama

# Define embedding and language model
EMBEDDING_MODEL = 'hf.co/CompendiumLabs/bge-base-en-v1.5-gguf'
LANGUAGE_MODEL = 'hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF'


embedding_dim = 768  
index = faiss.IndexFlatIP(embedding_dim)  
chunks = []  
def normalize(vec):
    return vec / np.linalg.norm(vec)  

def add_chunk_to_database(chunk):
    embedding = ollama.embed(model=EMBEDDING_MODEL, input=chunk)['embeddings'][0]
    embedding = np.array(embedding).astype('float32').reshape(1, -1)
    embedding = normalize(embedding)  
    
    index.add(embedding)  
    chunks.append(chunk)  
    

with open(r'C:\Users\Owner\Desktop\RAG system\cat-facts.txt', 'r', encoding='utf-8') as file:
    dataset = file.readlines()
    print(f'Loaded {len(dataset)} entries')


for i, chunk in enumerate(dataset):
    add_chunk_to_database(chunk)
    print(f'Added chunk {i+1}/{len(dataset)} to the database')
    
    
    
    
def retrieve(query, top_n=3):
    query_embedding = ollama.embed(model=EMBEDDING_MODEL, input=query)['embeddings'][0]
    query_embedding = np.array(query_embedding).astype('float32').reshape(1, -1)
    query_embedding = normalize(query_embedding)  
    
    distances, indices = index.search(query_embedding, top_n)  
    results = [chunks[i] for i in indices[0] if i < len(chunks)] 
    return results





# query = input("Enter your query: ")
# results = retrieve(query, top_n=3)

# print("\nTop retrieved results:")
# for res in results:
#     print(res)