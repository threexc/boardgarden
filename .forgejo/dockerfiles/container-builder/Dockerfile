FROM debian:bookworm-slim

COPY caddy-local.crt /usr/local/share/ca-certificates/caddy-local.crt
RUN apt-get update && apt-get install -y ca-certificates nodejs && update-ca-certificates
