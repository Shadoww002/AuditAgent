import os
from langchain_qdrant import QdrantVectorStore
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from qdrant_client import QdrantClient

class RetrievalLayer:
    """
    RAG utility to fetch context on vulnerabilities.
    """
    def __init__(self):
        try:
            self.embeddings = FastEmbedEmbeddings()
            qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
            self.client = QdrantClient(url=qdrant_url)
            self.vectorstore = QdrantVectorStore(
                client=self.client,
                collection_name="auditagent",
                embedding=self.embeddings
            )
            self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})
            self.has_db = True
        except Exception as e:
            print(f"Failed to initialize Qdrant: {e}")
            self.has_db = False

    def query(self, query: str) -> str:
        """
        Query the Chroma vector database for security guidelines.
        """
        if not self.has_db:
            return "Retrieval DB unavailable."
            
        try:
            docs = self.retriever.invoke(query)
            if not docs:
                return "No relevant security context found."
                
            context = []
            for i, doc in enumerate(docs):
                context.append(f"[Source {i+1}]: {doc.page_content}")
                
            return "\n\n".join(context)
        except Exception as e:
            return f"Error during retrieval: {e}"

retriever = RetrievalLayer()
