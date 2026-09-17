import os
import sys
from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from qdrant_client import QdrantClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def seed_database():
    print("Loading HuggingFace Embeddings...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    print(f"Connecting to Qdrant at {qdrant_url}...")
    
    documents = [
        Document(
            page_content="OWASP Top 10 - A01:2021-Broken Access Control. Access control enforces policy such that users cannot act outside of their intended permissions. Failures typically lead to unauthorized information disclosure, modification, or destruction of all data.",
            metadata={"source": "OWASP_Top_10_2021"}
        ),
        Document(
            page_content="OWASP Top 10 - A02:2021-Cryptographic Failures. Previously known as Sensitive Data Exposure. Focuses on failures related to cryptography, which often leads to sensitive data exposure or system compromise. Hardcoded secrets like API keys or AWS keys fall under severe cryptographic or architecture failures.",
            metadata={"source": "OWASP_Top_10_2021"}
        ),
        Document(
            page_content="OWASP Top 10 - A03:2021-Injection. Injection flaws, such as SQL, NoSQL, OS command, and LDAP injection, occur when untrusted data is sent to an interpreter as part of a command or query.",
            metadata={"source": "OWASP_Top_10_2021"}
        ),
        Document(
            page_content="CWE-798: Use of Hard-coded Credentials. The software contains hard-coded credentials, such as a password or cryptographic key, which it uses for its own inbound authentication, outbound communication to external components, or encryption of internal data.",
            metadata={"source": "CWE"}
        ),
        Document(
            page_content="CWE-89: Improper Neutralization of Special Elements used in an SQL Command ('SQL Injection'). The software constructs all or part of an SQL command using externally-influenced input from an upstream component, but it does not neutralize or incorrectly neutralizes special elements that could modify the intended SQL command.",
            metadata={"source": "CWE"}
        )
    ]
    
    print("Adding documents to Qdrant vector database...")
    QdrantVectorStore.from_documents(
        documents,
        embeddings,
        url=qdrant_url,
        collection_name="auditagent",
    )
    print(f"Successfully added {len(documents)} documents to Qdrant.")

if __name__ == "__main__":
    seed_database()
