RAG with FAISS
This project uses FAISS as a vector database to store and retrieve text embeddings. It takes user queries, finds the most relevant text from a dataset, and returns the results.

Technologies Used
FAISS – Vector database for similarity search

Ollama – Embedding model

NumPy – For numerical operations

How It Works
Loads a text dataset and converts it into embeddings.

Stores the embeddings in FAISS.

Takes a user query and converts it into an embedding.

Searches FAISS for similar results and returns the top matches.
