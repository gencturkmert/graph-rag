from rag import RAG

rag = RAG()
print("rag model created")
rag.train_dgi()
print("dgi trained")
rag.fetch_embeddings()
print("embeddings fetched")
rag.add_to_vector_store()
print("vector store initialized")
rag.init_index_and_query_engine()
print("index and query engine initialized")
rag.run_prompt("In which publications 'Neural Network-Based Representations of Knowledge' titled publication is cited")
