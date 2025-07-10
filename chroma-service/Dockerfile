FROM chromadb/chroma:latest

# Set build arguments for authentication
ARG CHROMA_USERNAME=chroma
ARG CHROMA_PASSWORD=secure_default_password

# Set environment variables
ENV CHROMA_SERVER_HOST=0.0.0.0
ENV CHROMA_SERVER_AUTHN_CREDENTIALS_FILE=/chroma/server.htpasswd
ENV CHROMA_SERVER_AUTHN_PROVIDER=chromadb.auth.basic.BasicAuthenticationProvider
ENV CHROMA_USERNAME=${CHROMA_USERNAME}
ENV CHROMA_PASSWORD=${CHROMA_PASSWORD}

# Create directory for data persistence
RUN mkdir -p /chroma/data

# Set working directory
WORKDIR /chroma

# Install apache2-utils for htpasswd generation
RUN apt-get update && apt-get install -y apache2-utils && rm -rf /var/lib/apt/lists/*

# Create a startup script that generates htpasswd file and starts ChromaDB
RUN echo '#!/bin/bash\n\
# Generate htpasswd file with environment variables\n\
CHROMA_USERNAME=${CHROMA_USERNAME:-chroma}\n\
CHROMA_PASSWORD=${CHROMA_PASSWORD:-secure_default_password}\n\
echo "Generating authentication file for user: $CHROMA_USERNAME"\n\
echo "$CHROMA_USERNAME:$(openssl passwd -apr1 $CHROMA_PASSWORD)" > /chroma/server.htpasswd\n\
\n\
# Start ChromaDB\n\
PORT=${PORT:-8000}\n\
echo "Starting ChromaDB on port $PORT with authentication enabled"\n\
exec chroma run --host 0.0.0.0 --port "$PORT" --path /chroma/data' > /start-chroma.sh && \
    chmod +x /start-chroma.sh

# Expose port
EXPOSE 8000

# Override the entrypoint completely and use our script
ENTRYPOINT []
CMD ["/bin/bash", "/start-chroma.sh"]