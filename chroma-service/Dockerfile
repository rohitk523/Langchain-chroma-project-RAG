FROM chromadb/chroma:latest

# Set environment variables
ENV CHROMA_SERVER_HOST=0.0.0.0
ENV CHROMA_SERVER_HTTP_PORT=8000
ENV CHROMA_SERVER_AUTHN_CREDENTIALS_FILE=/chroma/server.htpasswd
ENV CHROMA_SERVER_AUTHN_PROVIDER=chromadb.auth.basic.BasicAuthenticationProvider

# Create directory for data persistence
RUN mkdir -p /chroma/data

# Expose port
EXPOSE 8000

# Set working directory
WORKDIR /chroma

# Create a basic auth file (optional - for production security)
RUN apt-get update && apt-get install -y apache2-utils && \
    echo "chroma:$(openssl passwd -apr1 chromatest)" > server.htpasswd

# Start ChromaDB
CMD ["chroma", "run", "--host", "0.0.0.0", "--port", "8000", "--path", "/chroma/data"] 