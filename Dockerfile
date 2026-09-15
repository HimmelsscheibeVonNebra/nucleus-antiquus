FROM --platform=linux/amd64 debian:bookworm
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc-multilib binutils gdb \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /work
