import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from opensearchpy import OpenSearch, RequestsHttpConnection
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings

from app.config import settings

class OpenSearchService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(api_key=settings.openai_api_key)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Set up OpenSearch client
        self.client = OpenSearch(
            hosts=[{"host": settings.opensearch_host, "port": settings.opensearch_port}],
            http_auth=(settings.opensearch_username, settings.opensearch_password),
            use_ssl=settings.opensearch_use_ssl,
            verify_certs=settings.opensearch_verify_certs,
            connection_class=RequestsHttpConnection,
            timeout=30,
            max_retries=3
        )
        
        # Index names
        self.documents_index = settings.opensearch_documents_index
        self.chat_index = settings.opensearch_chat_index
        
    async def initialize(self):
        """Initialize OpenSearch indices"""
        try:
            # Create documents index
            documents_mapping = {
                "settings": {
                    "index": {
                        "knn": True,
                        "knn.algo_param.ef_search": 100
                    }
                },
                "mappings": {
                    "properties": {
                        "content": {"type": "text"},
                        "embedding": {
                            "type": "knn_vector",
                            "dimension": 1536,
                            "method": {
                                "name": "hnsw",
                                "space_type": "cosinesimil",
                                "engine": "lucene"
                            }
                        },
                        "user_id": {"type": "keyword"},
                        "metadata": {"type": "object"},
                        "timestamp": {"type": "date"}
                    }
                }
            }
            
            if not self.client.indices.exists(index=self.documents_index):
                self.client.indices.create(
                    index=self.documents_index,
                    body=documents_mapping
                )
                
            # Create chat history index
            chat_mapping = {
                "settings": {
                    "index": {
                        "knn": True,
                        "knn.algo_param.ef_search": 100
                    }
                },
                "mappings": {
                    "properties": {
                        "chat_id": {"type": "keyword"},
                        "user_id": {"type": "keyword"},
                        "message": {"type": "text"},
                        "response": {"type": "text"},
                        "message_type": {"type": "keyword"},
                        "sources": {"type": "object"},
                        "timestamp": {"type": "date"},
                        "embedding": {
                            "type": "knn_vector",
                            "dimension": 1536,
                            "method": {
                                "name": "hnsw",
                                "space_type": "cosinesimil",
                                "engine": "lucene"
                            }
                        }
                    }
                }
            }
            
            if not self.client.indices.exists(index=self.chat_index):
                self.client.indices.create(
                    index=self.chat_index,
                    body=chat_mapping
                )
                
            print("✅ OpenSearch indices initialized")
        except Exception as e:
            print(f"⚠️ OpenSearch initialization error: {e}")
    
    async def add_documents(self, documents: List[str], metadatas: List[Dict], user_id: str) -> str:
        """Add documents to OpenSearch with embeddings"""
        try:
            # Generate embeddings
            embeddings = await self.embeddings.aembed_documents(documents)
            
            # Prepare bulk operations
            bulk_body = []
            for i, (doc, embedding, metadata) in enumerate(zip(documents, embeddings, metadatas)):
                doc_id = f"{user_id}_{uuid.uuid4()}"
                
                # Enhanced metadata with user_id
                enhanced_metadata = metadata.copy()
                enhanced_metadata["user_id"] = user_id
                
                bulk_body.append({
                    "index": {
                        "_index": self.documents_index,
                        "_id": doc_id
                    }
                })
                bulk_body.append({
                    "content": doc,
                    "embedding": embedding,
                    "user_id": user_id,
                    "metadata": enhanced_metadata,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # Bulk index documents
            response = self.client.bulk(body=bulk_body)
            
            if response.get("errors"):
                raise Exception(f"Bulk indexing errors: {response}")
            
            return f"Added {len(documents)} documents"
                    
        except Exception as e:
            raise Exception(f"Error adding documents: {str(e)}")
    
    async def similarity_search(self, query: str, user_id: str, k: int = 3) -> List[Dict[str, Any]]:
        """Perform similarity search using OpenSearch k-NN"""
        try:
            # Generate query embedding
            query_embedding = await self.embeddings.aembed_query(query)
            
            # OpenSearch k-NN query
            search_body = {
                "size": k,
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"user_id": user_id}}
                        ],
                        "filter": [
                            {
                                "knn": {
                                    "embedding": {
                                        "vector": query_embedding,
                                        "k": k
                                    }
                                }
                            }
                        ]
                    }
                }
            }
            
            response = self.client.search(
                index=self.documents_index,
                body=search_body
            )
            
            # Format results
            documents = []
            for hit in response["hits"]["hits"]:
                documents.append({
                    "content": hit["_source"]["content"],
                    "metadata": hit["_source"]["metadata"],
                    "distance": 1 - hit["_score"]  # Convert score to distance
                })
            
            return documents
                    
        except Exception as e:
            raise Exception(f"Error in similarity search: {str(e)}")
    
    async def add_chat_message(self, chat_id: str, user_id: str, message: str, 
                              response: str, message_type: str, sources: List[Dict] = None):
        """Add chat message to history"""
        try:
            chat_data = {
                "chat_id": chat_id,
                "user_id": user_id,
                "message": message,
                "response": response,
                "message_type": message_type,
                "sources": sources or [],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Generate embedding for search
            text_for_embedding = f"{message} {response}"
            embedding = await self.embeddings.aembed_query(text_for_embedding)
            
            message_id = f"{chat_id}_{uuid.uuid4()}"
            
            # Add embedding to chat data
            chat_data["embedding"] = embedding
            
            # Index chat message
            self.client.index(
                index=self.chat_index,
                id=message_id,
                body=chat_data
            )
            
            return True
                
        except Exception as e:
            print(f"Error adding chat message: {e}")
            return False
    
    async def get_chat_history(self, chat_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Get chat history for a specific chat"""
        try:
            search_body = {
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"chat_id": chat_id}},
                            {"term": {"user_id": user_id}}
                        ]
                    }
                },
                "sort": [{"timestamp": {"order": "asc"}}],
                "size": 100
            }
            
            response = self.client.search(
                index=self.chat_index,
                body=search_body
            )
            
            history = []
            for hit in response["hits"]["hits"]:
                history.append(hit["_source"])
            
            return history
                    
        except Exception as e:
            print(f"Error getting chat history: {e}")
            return []
    
    async def get_user_chats(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all chat sessions for a user"""
        try:
            # Aggregation query to group by chat_id
            search_body = {
                "query": {"term": {"user_id": user_id}},
                "size": 0,
                "aggs": {
                    "chats": {
                        "terms": {
                            "field": "chat_id",
                            "size": 1000
                        },
                        "aggs": {
                            "first_message": {
                                "top_hits": {
                                    "sort": [{"timestamp": {"order": "asc"}}],
                                    "size": 1
                                }
                            },
                            "last_message": {
                                "top_hits": {
                                    "sort": [{"timestamp": {"order": "desc"}}],
                                    "size": 1
                                }
                            }
                        }
                    }
                }
            }
            
            response = self.client.search(
                index=self.chat_index,
                body=search_body
            )
            
            chats = []
            for bucket in response["aggregations"]["chats"]["buckets"]:
                chat_id = bucket["key"]
                first_hit = bucket["first_message"]["hits"]["hits"][0]["_source"]
                last_hit = bucket["last_message"]["hits"]["hits"][0]["_source"]
                
                chats.append({
                    "chat_id": chat_id,
                    "title": first_hit["message"][:50] + "..." if len(first_hit["message"]) > 50 else first_hit["message"],
                    "created_at": first_hit["timestamp"],
                    "last_message_at": last_hit["timestamp"],
                    "message_count": bucket["doc_count"]
                })
            
            return chats
                    
        except Exception as e:
            print(f"Error getting user chats: {e}")
            return []
    
    async def delete_chat(self, chat_id: str, user_id: str) -> bool:
        """Delete a chat session"""
        try:
            # Delete by query
            delete_body = {
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"chat_id": chat_id}},
                            {"term": {"user_id": user_id}}
                        ]
                    }
                }
            }
            
            response = self.client.delete_by_query(
                index=self.chat_index,
                body=delete_body
            )
            
            return response["deleted"] > 0
                    
        except Exception as e:
            print(f"Error deleting chat: {e}")
            return False
    
    async def process_pdf_file(self, file_path: str, user_id: str) -> str:
        """Process uploaded PDF file"""
        try:
            # Load and split PDF
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            docs = self.text_splitter.split_documents(documents)
            
            # Prepare documents and metadata
            texts = [doc.page_content for doc in docs]
            metadatas = []
            
            for doc in docs:
                metadata = doc.metadata.copy()
                metadata["user_id"] = user_id
                metadata["upload_timestamp"] = datetime.utcnow().isoformat()
                metadatas.append(metadata)
            
            # Add to OpenSearch
            result = await self.add_documents(texts, metadatas, user_id)
            return result
            
        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check OpenSearch cluster health"""
        try:
            # Check cluster health
            health_response = self.client.cluster.health()
            
            # Check if indices exist
            indices_exist = {
                "documents_index": self.client.indices.exists(index=self.documents_index),
                "chat_index": self.client.indices.exists(index=self.chat_index)
            }
            
            # Get index stats
            try:
                documents_stats = self.client.indices.stats(index=self.documents_index)
                chat_stats = self.client.indices.stats(index=self.chat_index)
                
                return {
                    "status": "healthy",
                    "cluster_status": health_response.get("status", "unknown"),
                    "indices": {
                        "documents": {
                            "exists": indices_exist["documents_index"],
                            "document_count": documents_stats["_all"]["primaries"]["docs"]["count"] if indices_exist["documents_index"] else 0
                        },
                        "chat": {
                            "exists": indices_exist["chat_index"],
                            "message_count": chat_stats["_all"]["primaries"]["docs"]["count"] if indices_exist["chat_index"] else 0
                        }
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
            except Exception as stats_error:
                return {
                    "status": "partial",
                    "cluster_status": health_response.get("status", "unknown"),
                    "indices": indices_exist,
                    "error": f"Could not get index stats: {str(stats_error)}",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_user_documents(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all documents for a specific user"""
        try:
            search_body = {
                "query": {
                    "term": {"user_id": user_id}
                },
                "sort": [{"timestamp": {"order": "desc"}}],
                "size": 1000,
                "_source": ["content", "metadata", "timestamp"]
            }
            
            response = self.client.search(
                index=self.documents_index,
                body=search_body
            )
            
            documents = []
            for hit in response["hits"]["hits"]:
                source = hit["_source"]
                documents.append({
                    "id": hit["_id"],
                    "content": source["content"][:500] + "..." if len(source["content"]) > 500 else source["content"],
                    "metadata": source["metadata"],
                    "timestamp": source["timestamp"],
                    "full_content_available": len(source["content"]) > 500
                })
            
            return documents
                    
        except Exception as e:
            print(f"Error getting user documents: {e}")
            return [] 