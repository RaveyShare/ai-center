FROM python:3.11-slim
WORKDIR /app
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources
RUN apt-get update && apt-get install -y curl ca-certificates && rm -rf /var/lib/apt/lists/*
# Install uv
RUN curl -Ls https://astral.sh/uv/install.sh | sh && \
    echo 'export PATH="/root/.local/bin:$PATH"' >> /etc/profile
ENV PATH=/root/.local/bin:$PATH

# Copy project metadata and sync
COPY pyproject.toml ./
RUN uv sync --no-dev

# Copy application source
COPY app ./app
COPY README.md ./README.md

EXPOSE 8001
ENV PYTHONPATH=/app
ENV PORT=8001
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
