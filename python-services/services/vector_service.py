import os
import logging
from typing import List, Dict, Any
import asyncio
import json

logger = logging.getLogger(__name__)

class VectorService:
    def __init__(self):
        self.db_path = os.getenv('VECTOR_DB_PATH', './data/lancedb')
        self.embedding_model = 'all-MiniLM-L6-v2'  # Lightweight embedding model
        self._db = None
        self._embedder = None
        
        # Initialize the vector database
        self._initialize_db()
    
    def _initialize_db(self):
        """Initialize LanceDB and embedding model"""
        try:
            import lancedb
            from sentence_transformers import SentenceTransformer
            
            # Initialize LanceDB (embedded)
            self._db = lancedb.connect(self.db_path)
            logger.info(f"Connected to LanceDB at {self.db_path}")
            
            # Initialize embedding model
            self._embedder = SentenceTransformer(self.embedding_model)
            logger.info(f"Loaded embedding model: {self.embedding_model}")
            
            # Create or connect to the documents table
            self._initialize_documents_table()
            
        except Exception as e:
            logger.error(f"Failed to initialize vector database: {e}")
            self._db = None
            self._embedder = None
    
    def _initialize_documents_table(self):
        """Initialize the documents table with mock technical data"""
        try:
            # Check if table exists
            table_name = "technical_documents"
            
            if table_name not in self._db.table_names():
                logger.info("Creating new documents table with mock data")
                
                # Mock technical documents for testing
                mock_documents = [
                    {
                        "id": "doc_1",
                        "title": "REST API Best Practices",
                        "content": "REST APIs should follow HTTP semantics, use proper status codes, implement consistent naming conventions, and support pagination for large datasets. Authentication should use tokens, and responses should be properly cached.",
                        "category": "web-development",
                        "tags": ["rest", "api", "http", "web-services"]
                    },
                    {
                        "id": "doc_2", 
                        "title": "Database Sharding Strategies",
                        "content": "Database sharding involves horizontal partitioning of data across multiple database instances. Common strategies include range-based sharding, hash-based sharding, and directory-based sharding. Consider data distribution, query patterns, and rebalancing needs.",
                        "category": "databases",
                        "tags": ["database", "sharding", "scaling", "partitioning"]
                    },
                    {
                        "id": "doc_3",
                        "title": "Microservices Architecture Patterns",
                        "content": "Microservices patterns include API Gateway, Circuit Breaker, Service Discovery, and Event Sourcing. Each service should have a single responsibility, own its data, and communicate via well-defined APIs. Consider deployment, monitoring, and distributed tracing.",
                        "category": "architecture",
                        "tags": ["microservices", "architecture", "patterns", "distributed-systems"]
                    },
                    {
                        "id": "doc_4",
                        "title": "System Design Interview Guide",
                        "content": "System design interviews focus on scalability, reliability, and performance. Start with requirements gathering, estimate scale, design high-level architecture, dive into components, address bottlenecks, and discuss monitoring and deployment strategies.",
                        "category": "interviews",
                        "tags": ["system-design", "interviews", "scalability", "architecture"]
                    },
                    {
                        "id": "doc_5",
                        "title": "Caching Strategies and Patterns",
                        "content": "Caching improves performance through strategies like Cache-Aside, Write-Through, Write-Behind, and Refresh-Ahead. Consider cache invalidation, TTL policies, and distributed caching solutions like Redis or Memcached for scalable applications.",
                        "category": "performance",
                        "tags": ["caching", "performance", "redis", "optimization"]
                    }
                ]
                
                # Generate embeddings for documents
                documents_with_embeddings = []
                for doc in mock_documents:
                    # Combine title and content for embedding
                    text_to_embed = f"{doc['title']} {doc['content']}"
                    embedding = self._embedder.encode(text_to_embed).tolist()
                    
                    doc_with_embedding = {
                        **doc,
                        "embedding": embedding,
                        "text": text_to_embed
                    }
                    documents_with_embeddings.append(doc_with_embedding)
                
                # Create table with documents
                self._table = self._db.create_table(table_name, documents_with_embeddings)
                logger.info(f"Created table '{table_name}' with {len(documents_with_embeddings)} documents")
            else:
                # Connect to existing table
                self._table = self._db.open_table(table_name)
                logger.info(f"Connected to existing table '{table_name}'")
                
        except Exception as e:
            logger.error(f"Failed to initialize documents table: {e}")
            self._table = None
    
    def is_ready(self) -> bool:
        """Check if the vector service is ready"""
        return self._db is not None and self._embedder is not None and self._table is not None
    
    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            
        Returns:
            List of matching documents with similarity scores
        """
        if not self.is_ready():
            logger.error("Vector service not ready")
            return []
        
        try:
            # Generate embedding for the query
            loop = asyncio.get_event_loop()
            query_embedding = await loop.run_in_executor(
                None, 
                lambda: self._embedder.encode(query).tolist()
            )
            
            # Perform vector search
            results = self._table.search(query_embedding).limit(limit).to_list()
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_result = {
                    "id": result.get("id"),
                    "title": result.get("title"),
                    "content": result.get("content"),
                    "category": result.get("category"),
                    "tags": result.get("tags", []),
                    "similarity_score": float(result.get("_distance", 0))  # LanceDB returns distance
                }
                formatted_results.append(formatted_result)
            
            logger.info(f"Vector search for '{query}' returned {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return []
    
    async def ingest_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Ingest new documents into the vector database
        
        Args:
            documents: List of documents to ingest
            
        Returns:
            Result dictionary with ingestion status
        """
        if not self.is_ready():
            raise Exception("Vector service not ready")
        
        try:
            documents_with_embeddings = []
            
            for doc in documents:
                # Generate text for embedding
                text_to_embed = f"{doc.get('title', '')} {doc.get('content', '')}"
                
                # Generate embedding
                loop = asyncio.get_event_loop()
                embedding = await loop.run_in_executor(
                    None,
                    lambda: self._embedder.encode(text_to_embed).tolist()
                )
                
                doc_with_embedding = {
                    **doc,
                    "embedding": embedding,
                    "text": text_to_embed
                }
                documents_with_embeddings.append(doc_with_embedding)
            
            # Add documents to table
            self._table.add(documents_with_embeddings)
            
            logger.info(f"Successfully ingested {len(documents)} documents")
            return {"count": len(documents), "status": "success"}
            
        except Exception as e:
            logger.error(f"Document ingestion error: {e}")
            raise