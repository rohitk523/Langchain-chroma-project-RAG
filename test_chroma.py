import chromadb

chroma_client = chromadb.HttpClient(host='https://chroma-db-production-2197.up.railway.app')
chroma_client.heartbeat()
