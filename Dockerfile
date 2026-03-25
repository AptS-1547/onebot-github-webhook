# Build stage
FROM rust:1.83-bookworm AS builder

WORKDIR /app

# Copy manifests
COPY Cargo.toml Cargo.lock ./

# Create dummy main to cache dependencies
RUN mkdir src && \
    echo 'fn main() {}' > src/main.rs && \
    echo 'pub mod config; pub mod error; pub mod github; pub mod matching; pub mod message; pub mod onebot; pub mod routes; pub struct AppState {}' > src/lib.rs && \
    mkdir -p src/github src/onebot src/routes && \
    echo 'pub mod formatter; pub mod payload; pub mod webhook;' > src/github/mod.rs && \
    echo 'pub mod client; pub mod http; pub mod websocket;' > src/onebot/mod.rs && \
    echo 'pub mod github;' > src/routes/mod.rs && \
    touch src/config.rs src/error.rs src/matching.rs src/message.rs \
          src/github/formatter.rs src/github/payload.rs src/github/webhook.rs \
          src/onebot/client.rs src/onebot/http.rs src/onebot/websocket.rs \
          src/routes/github.rs

# Build dependencies (this layer will be cached)
RUN cargo build --release && rm -rf src

# Copy actual source
COPY src ./src

# Build the actual binary
RUN touch src/main.rs src/lib.rs && cargo build --release

# Runtime stage
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
    ca-certificates \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy binary
COPY --from=builder /app/target/release/onebot-github-webhook /app/onebot-github-webhook

# Default config location
VOLUME /app/config

# Expose port
EXPOSE 8000

# Run
CMD ["/app/onebot-github-webhook"]
