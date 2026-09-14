class RetrievalLayer:
    def __init__(self):
        # In a real scenario, initialize ChromaDB client here
        # self.client = chromadb.Client()
        pass
        
    def retrieve_context(self, query: str) -> str:
        """
        Mocks retrieving context from a vector DB for CVEs or OWASP issues.
        """
        query_lower = query.lower()
        if "secret" in query_lower or "password" in query_lower or "key" in query_lower:
            return (
                "CWE-798: Use of Hard-coded Credentials.\n"
                "Hardcoding secrets in source code is dangerous because it exposes sensitive "
                "authentication material to anyone with access to the repository, leading to "
                "potential unauthorized access to external services or databases."
            )
        elif "cve" in query_lower or "vuln" in query_lower or "dependency" in query_lower:
            return (
                "OWASP A06:2021 – Vulnerable and Outdated Components.\n"
                "Using known vulnerable dependencies allows attackers to exploit publicly "
                "known flaws. It is crucial to patch these libraries to secure versions."
            )
        return "No specific context found. Analyze the code carefully for general security best practices."

# Singleton instance for easy access
retriever = RetrievalLayer()
