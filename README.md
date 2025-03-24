# **📌 RAG with FAISS**  

This project uses **FAISS** as a vector database to store and retrieve text embeddings. It takes user queries, finds the most relevant text from a dataset, and returns the results.  

## ** Technologies Used**  
- **FAISS** – Vector database for similarity search  
- **Ollama** – Embedding model  
- **NumPy** – For numerical operations  

## ** How It Works**  
1. **Loads** a text dataset and converts it into **embeddings**.  
2. **Stores** the embeddings in **FAISS**.  
3. **Takes a user query** and converts it into an embedding.  
4. **Searches FAISS** for similar results and returns the top matches.  

## ** How to Run**  
1. Install dependencies:  
   ```bash
   pip install faiss-cpu numpy ollama
