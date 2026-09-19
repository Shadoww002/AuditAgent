import os
from typing import List, Dict, Any
from langchain_qdrant import QdrantVectorStore
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from qdrant_client import QdrantClient

class RetrievalLayer:
    """
    RAG utility to fetch context on vulnerabilities.
    """
    def __init__(self):
        self._embeddings = None
        self._client = None
        self._vectorstore = None
        self._retriever = None
        self._initialized = False
        self.has_db = False

    def _initialize(self):
        if self._initialized:
            return
            
        try:
            qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
            self._client = QdrantClient(url=qdrant_url)
            
            # Make a real round trip to ensure the DB is reachable
            self._client.get_collections()
            
            self._embeddings = FastEmbedEmbeddings()
            self._vectorstore = QdrantVectorStore(
                client=self._client,
                collection_name="auditagent",
                embedding=self._embeddings
            )
            self._retriever = self._vectorstore.as_retriever(search_kwargs={"k": 3})
            self.has_db = True
        except Exception as e:
            print(f"Failed to initialize Qdrant: {e}")
            self.has_db = False
        finally:
            self._initialized = True

    def query(self, query: str) -> str:
        """
        Query the Qdrant vector database for security guidelines.
        (Legacy text output)
        """
        self._initialize()
        if not self.has_db:
            return "Retrieval DB unavailable."
            
        try:
            docs = self._retriever.invoke(query)
            if not docs:
                return "No relevant security context found."
                
            context = []
            for i, doc in enumerate(docs):
                context.append(f"[Source {i+1}]: {doc.page_content}")
                
            return "\n\n".join(context)
        except Exception as e:
            return f"Error during retrieval: {e}"

    def retrieve_context(self, query: str) -> List[Dict[str, Any]]:
        """
        Query the Qdrant vector database and return structured results
        including metadata (e.g. source).
        """
        self._initialize()
        if not self.has_db:
            return []
            
        try:
            docs = self._retriever.invoke(query)
            results = []
            for doc in docs:
                source = doc.metadata.get("source", "Unknown")
                results.append({
                    "content": doc.page_content,
                    "source": source
                })
            return results
        except Exception as e:
            print(f"Error during retrieval: {e}")
            return []

retriever = RetrievalLayer()
