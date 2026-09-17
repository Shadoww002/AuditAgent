import os
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_db")

class RetrievalLayer:
    """
    RAG utility to fetch context on vulnerabilities.
    """
    def __init__(self):
        try:
            self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            self.vectorstore = Chroma(
                persist_directory=CHROMA_PATH, 
                embedding_function=self.embeddings
            )
            self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})
            self.has_db = True
        except Exception as e:
            print(f"Failed to initialize ChromaDB: {e}")
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
