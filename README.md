RAG System with FAISS for Vector Search
This project implements a Retrieval-Augmented Generation (RAG) system using FAISS as a vector database for efficient similarity search. The system retrieves relevant text chunks based on user queries and integrates them into a language model response.

📌 Features
Vector Database: Uses FAISS (Facebook AI Similarity Search) for efficient nearest neighbor search.

Embeddings: Utilizes Ollama to generate embeddings from text.

Text Retrieval: Retrieves the top-N most relevant text chunks based on user input.

Query Input: Allows users to enter custom queries for retrieval.

🛠️ Technologies Used
FAISS (Facebook AI Similarity Search) – Vector database

Ollama – Embedding and language model

NumPy – Numerical operations

Python – Programming language

🚀 How It Works
Initialize FAISS Index

Uses IndexFlatIP for cosine similarity-based retrieval.

Load and Store Data

Reads text data and converts it into vector embeddings.

Stores embeddings in the FAISS database.

User Query Processing

Takes a user query and converts it into an embedding.

Searches for the most similar stored embeddings.

Retrieve & Display Results

Displays the top matching text chunks from the dataset.
