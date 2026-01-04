FROM python:3.11-slim
WORKDIR /app
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources
RUN apt-get update && apt-get install -y curl ca-certificates && rm -rf /var/lib/apt/lists/*
# Install uv
RUN curl -Ls https://astral.sh/uv/install.sh | sh && \
    echo 'export PATH="/root/.local/bin:$PATH"' >> /etc/profile
ENV PATH=/root/.local/bin:$PATH

# Copy project metadata and lockfile first (better layer cache)
COPY pyproject.toml uv.lock ./

# Copy application source
COPY src ./src

RUN uv sync --frozen --no-dev

EXPOSE 8000
ENV PYTHONPATH=/app/src
ENV PORT=8000
CMD ["uv", "run", "uvicorn", "ai_center.main:app", "--host", "0.0.0.0", "--port", "8000"]
