FROM chromadb/chroma:latest

# Set environment variables
ENV CHROMA_SERVER_HOST=0.0.0.0
ENV CHROMA_SERVER_AUTHN_CREDENTIALS_FILE=/chroma/server.htpasswd
ENV CHROMA_SERVER_AUTHN_PROVIDER=chromadb.auth.basic.BasicAuthenticationProvider

# Create directory for data persistence
RUN mkdir -p /chroma/data

# Set working directory
WORKDIR /chroma

# Create a basic auth file (optional - for production security)
RUN apt-get update && apt-get install -y apache2-utils && \
    echo "chroma:$(openssl passwd -apr1 chromatest)" > server.htpasswd

# Create a startup script that handles the PORT variable
RUN echo '#!/bin/bash\n\
PORT=${PORT:-8000}\n\
echo "Starting ChromaDB on port $PORT"\n\
exec chroma run --host 0.0.0.0 --port "$PORT" --path /chroma/data' > /start-chroma.sh && \
    chmod +x /start-chroma.sh

# Expose port
EXPOSE 8000

# Override the entrypoint completely and use our script
ENTRYPOINT []
CMD ["/bin/bash", "/start-chroma.sh"]