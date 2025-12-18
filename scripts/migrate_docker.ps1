# PowerShell script to migrate scout reports to ChromaDB Cloud
# Using Python 3.12 in Docker

Write-Host "🔧 Migrating scout reports to ChromaDB Cloud using Docker" -ForegroundColor Cyan
Write-Host "=" -ForegroundColor Gray

# Build a temporary migration image
Write-Host "Building migration Docker image..." -ForegroundColor Yellow
docker build -t scout-migration -f- . <<'EOF'
FROM python:3.12-slim
WORKDIR /app
RUN pip install pymongo python-dotenv chromadb==0.4.24
COPY scripts/migrate_chromadb_http.py .
COPY .env.production .
CMD ["python", "migrate_chromadb_http.py"]
EOF

# Run migration
Write-Host "Running migration..." -ForegroundColor Yellow
docker run --rm scout-migration

Write-Host "✅ Migration complete!" -ForegroundColor Green
