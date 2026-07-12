"""Provides core functionalities for the vector_db module."""
import logging
import math
from typing import List, Optional, Any
import chromadb
from chromadb.utils import embedding_functions
from app.core.vector_db_base import BaseVectorDB
from app.core.contracts import ToolSchema

logger = logging.getLogger(__name__)

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Executes the Cosine similarity operation."""
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm_a = math.sqrt(sum(a * a for a in vec1))
    norm_b = math.sqrt(sum(b * b for b in vec2))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)

class VectorDatabaseManager(BaseVectorDB):
    """
    [PHASE 3] Persistent Vector Database Manager (ChromaDB).
    1. Intent Routing (Supervisor determination)
    2. Semantic Key Mapping (Python LLM outputs to Java Specs)
    3. Domain-Scoped Tool Retrieval
    """
    def __init__(self, persist_dir: str = "./.chroma_data"):
        """Executes the   init   operation."""
        # Transition from in-memory to PersistentClient
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.ef = embedding_functions.DefaultEmbeddingFunction()
        
        # 1. Routing Collection
        self.routing_col = self.client.get_or_create_collection(
            name="domain_routing", 
            embedding_function=self.ef,
            metadata={"hnsw:space": "cosine"}
        )
        
        # 2. Tool Collection
        self.tools_col = self.client.get_or_create_collection(
            name="tools_registry", 
            embedding_function=self.ef,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"Vector DB: Persistent DB initialized at {persist_dir}.")

    # --- ROUTING METHODS ---
    def seed_supervisor_intents(self, supervisor_id: str, intent_descriptions: List[str]):
        """Executes the Seed supervisor intents operation."""
        ids = [f"{supervisor_id}_{i}" for i in range(len(intent_descriptions))]
        metadatas = [{"supervisor_id": supervisor_id} for _ in intent_descriptions]
        
        self.routing_col.upsert(
            documents=intent_descriptions,
            metadatas=metadatas,
            ids=ids
        )
        logger.info(f"Vector DB: Seeded {len(intent_descriptions)} intents for {supervisor_id}.")

    def find_best_supervisor(self, query: str) -> Optional[str]:
        """Executes the Find best supervisor operation."""
        top_k = self.find_top_k_supervisors(query, k=1, threshold=0.0)
        return top_k[0] if top_k else None

    def find_top_k_supervisors(self, query: str, k: int = 2, threshold: float = 0.5) -> List[str]:
        """Executes the Find top k supervisors operation."""
        if self.routing_col.count() == 0:
            return []
            
        results = self.routing_col.query(
            query_texts=[query],
            n_results=k
        )
        
        valid_supervisors = []
        if results and results.get("distances") and results.get("metadatas"):
            for dist, meta in zip(results["distances"][0], results["metadatas"][0]):
                # ChromaDB cosine distance: smaller is closer (distance = 1 - cosine_similarity)
                # So cosine_similarity = 1 - distance
                sim = 1.0 - dist
                if sim >= threshold:
                    valid_supervisors.append(meta["supervisor_id"])
                    
        # Remove duplicates while preserving order
        unique_supervisors = list(dict.fromkeys(valid_supervisors))
        return unique_supervisors

    # --- MAPPING METHODS ---
    def find_best_semantic_key(self, target_java_key: str, target_description: str, extracted_python_keys: List[str]) -> Optional[str]:
        """
        [PHASE 3] Avoids creating/dropping ephemeral ChromaDB collections.
        Calculates cosine similarity directly in memory for ultra-fast mapping.
        """
        if not extracted_python_keys:
            return None
            
        query_text = f"{target_java_key} {target_description}"
        
        # Generate embeddings in one batch
        embeddings = self.ef([query_text] + extracted_python_keys)
        query_emb = embeddings[0]
        keys_embs = embeddings[1:]
        
        best_match = None
        best_sim = -1.0
        
        # Currently hardcoded threshold for phase 3, should be configurable
        threshold = 0.6 
        
        for key, emb in zip(extracted_python_keys, keys_embs):
            sim = cosine_similarity(query_emb, emb)
            if sim > best_sim and sim >= threshold:
                best_sim = sim
                best_match = key
                
        return best_match

    # --- TOOL RETRIEVAL METHODS ---
    def index_tools(self, tools: List[ToolSchema]):
        """Executes the Index tools operation."""
        if not tools:
            return
            
        documents = []
        metadatas = []
        ids = []
        
        for tool in tools:
            # We embed the tool name, description, and example utterances
            content = f"{tool.tool_id}\nExamples: " + ", ".join(tool.example_utterances)
            documents.append(content)
            metadatas.append({"domain": tool.domain, "tool_id": tool.tool_id})
            ids.append(tool.tool_id)
            
        self.tools_col.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        logger.info(f"Vector DB: Indexed {len(tools)} tools.")

    def find_tools_for_domain(self, domain: str, query: str, top_k: int = 5, threshold: float = 0.6) -> List[str]:
        """Executes the Find tools for domain operation."""
        if self.tools_col.count() == 0:
            return []
            
        results = self.tools_col.query(
            query_texts=[query],
            n_results=top_k,
            where={"domain": domain}  # Domain-scoped filtering
        )
        
        valid_tools = []
        if results and results.get("distances") and results.get("metadatas"):
            for dist, meta in zip(results["distances"][0], results["metadatas"][0]):
                sim = 1.0 - dist
                if sim >= threshold:
                    valid_tools.append(meta["tool_id"])
                    
        return valid_tools

# Singleton instance
vdb = VectorDatabaseManager()
