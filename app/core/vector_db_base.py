"""Provides core functionalities for the vector_db_base module."""
from abc import ABC, abstractmethod
from typing import List, Optional, Any


class BaseVectorDB(ABC):
    """
    Abstract Base Class for Vector Database interactions.
    Provides a modular interface so the underlying engine (Chroma, PgVector, Qdrant)
    can be swapped out for production scaling without affecting the application logic.
    """

    @abstractmethod
    def find_best_supervisor(self, query: str) -> Optional[str]:
        """
        Finds the best matching Domain Supervisor (Root Routing).
        Should return the supervisor_id or None.
        """
        pass

    @abstractmethod
    def find_top_k_supervisors(
        self, query: str, k: int = 2, threshold: float = 0.5
    ) -> List[str]:
        """
        [PHASE 3] Finds the Top-K matching Domain Supervisors based on a confidence threshold.
        Returns a list of supervisor_ids.
        """
        pass

    @abstractmethod
    def find_best_semantic_key(
        self, target_key: str, target_description: str, available_keys: List[str]
    ) -> Optional[str]:
        """
        Finds the semantically closest key for Contract Mapping.
        """
        pass

    @abstractmethod
    def index_tools(self, tools: List[Any]):
        """
        [PHASE 3] Indexes ToolSchemas into the Vector DB.
        """
        pass

    @abstractmethod
    def find_tools_for_domain(
        self, domain: str, query: str, top_k: int = 5, threshold: float = 0.6
    ) -> List[str]:
        """
        [PHASE 3] Domain-Scoped Tool Retrieval.
        Searches within a specific domain's namespace for the most relevant tools.
        Returns a list of tool_ids.
        """
        pass
