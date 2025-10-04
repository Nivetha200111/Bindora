# 🚀 Bindora Backend - Production-Ready API

**Complete FastAPI backend for AI-powered drug-target interaction prediction**

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/fastapi-0.109.0-green.svg)
![PostgreSQL](https://img.shields.io/badge/postgresql-15-blue.svg)
![Redis](https://img.shields.io/badge/redis-7.0-red.svg)

## 📋 Overview

Bindora Backend is a production-ready FastAPI application that provides AI-powered drug-target interaction prediction using state-of-the-art machine learning models.

### Key Features

- 🧬 **Protein Encoding**: ESM-2 model for protein sequence embeddings
- 💊 **Molecular Analysis**: RDKit for drug fingerprinting and property calculation
- 🤖 **AI Prediction**: Similarity-based binding affinity prediction
- 📊 **Real-time API**: RESTful endpoints with comprehensive documentation
- 🗄️ **Database Layer**: PostgreSQL with SQLAlchemy ORM
- ⚡ **Performance**: Redis caching and async operations
- 🔒 **Production Ready**: Comprehensive error handling, logging, and monitoring

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   External APIs │
│   (Next.js)     │◄──►│   Backend       │◄──►│   ChEMBL/UniProt│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   PostgreSQL    │
                       │   + pgvector    │
                       └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │     Redis       │
                       │    Cache        │
                       └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **PostgreSQL 15+** (with pgvector extension)
- **Redis 7+** (optional, for caching)
- **Docker** (optional, for containerized deployment)

### Local Development Setup

1. **Clone and navigate:**
   ```bash
   git clone https://github.com/your-org/bindora.git
   cd bindora/backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your database and API settings
   ```

5. **Download data:**
   ```bash
   python data/download_data.py --sample-only  # For quick testing
   # OR
   python data/download_data.py  # Full data download (~10-15 minutes)
   ```

6. **Start PostgreSQL and Redis:**
   ```bash
   # Using Docker
   docker run -d --name postgres -p 5432:5432 \
     -e POSTGRES_DB=bindora \
     -e POSTGRES_USER=bindora \
     -e POSTGRES_PASSWORD=password \
     postgres:15

   docker run -d --name redis -p 6379:6379 redis:7-alpine
   ```

7. **Run database migrations:**
   ```bash
   # Tables will be created automatically on first run
   ```

8. **Start the API:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   API will be available at: http://localhost:8000
   Interactive docs: http://localhost:8000/docs

### Testing the API

```bash
# Test health endpoint
curl http://localhost:8000/health

# Search for drugs by gene
curl -X POST "http://localhost:8000/api/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "BRCA1", "query_type": "gene", "max_results": 5}'

# Get drug details
curl http://localhost:8000/api/drug/CHEMBL25
```

## 📁 Project Structure

```
backend/
├── app/
│   ├── main.py                    # FastAPI application
│   ├── config.py                  # Configuration settings
│   ├── dependencies.py            # Dependency injection
│   │
│   ├── models/                    # AI MODELS
│   │   ├── protein_encoder.py    # ESM-2 protein embeddings
│   │   ├── drug_encoder.py       # RDKit molecular analysis
│   │   └── binding_predictor.py  # Binding affinity prediction
│   │
│   ├── services/                  # BUSINESS LOGIC
│   │   ├── search_service.py     # Main search orchestration
│   │   ├── drug_service.py       # Drug operations
│   │   └── target_service.py     # Protein target operations
│   │
│   ├── api/                       # API LAYER
│   │   ├── routes.py             # REST endpoints
│   │   └── schemas.py            # Pydantic models
│   │
│   ├── database/                  # DATA LAYER
│   │   ├── models.py             # SQLAlchemy models
│   │   ├── db.py                 # Database connection
│   │   └── crud.py               # Database operations
│   │
│   └── utils/                     # UTILITIES
│       ├── chembl_client.py      # ChEMBL API wrapper
│       ├── uniprot_client.py     # UniProt API wrapper
│       └── cache.py              # Caching utilities
│
├── data/                          # DATA SCRIPTS
│   ├── download_data.py          # Download drugs/proteins
│   └── process_embeddings.py     # Pre-compute embeddings
│
├── tests/                         # TESTS
│   ├── test_encoders.py          # AI model tests
│   ├── test_predictor.py         # Prediction tests
│   └── test_api.py               # API endpoint tests
│
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Production container
├── docker-compose.yml             # Full stack deployment
├── .env.example                   # Environment template
└── README.md                      # This file
```

## 🔧 Configuration

### Environment Variables

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com

# Database
DATABASE_URL=postgresql://bindora:password@localhost/bindora

# AI Models
PROTEIN_MODEL=facebook/esm2_t33_650M_UR50D
DEVICE=auto  # auto, cpu, cuda, mps

# Caching
REDIS_URL=redis://localhost:6379
CACHE_TTL=3600

# External APIs
CHEMBL_API_URL=https://www.ebi.ac.uk/chembl/api/data
UNIPROT_API_URL=https://rest.uniprot.org

# Performance
MAX_RESULTS=100
BATCH_SIZE=32
```

## 🧪 Testing

### Run All Tests

```bash
# Install test dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/test_encoders.py -v
```

### Test Coverage

- ✅ **Protein Encoder**: ESM-2 model loading and inference
- ✅ **Drug Encoder**: RDKit molecular analysis and fingerprints
- ✅ **Binding Predictor**: Similarity-based prediction
- ✅ **API Endpoints**: All REST endpoints with validation
- ✅ **Database Operations**: CRUD operations
- ✅ **External APIs**: ChEMBL and UniProt integration

## 🚢 Deployment

### Production Deployment

#### Using Docker Compose (Recommended)

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Scale API instances
docker-compose up -d --scale api=3
```

#### Manual Deployment

1. **Set up PostgreSQL with pgvector:**
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env.production
   # Edit with production values
   ```

3. **Start with production settings:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
   ```

### Platform Deployment

#### Railway.app (Recommended)
1. Connect GitHub repository
2. Add PostgreSQL and Redis services
3. Set environment variables
4. Deploy automatically

#### Render.com
1. Create new service from Git
2. Add PostgreSQL and Redis
3. Configure environment
4. Deploy

#### AWS/GCP
- Use ECS Fargate or Cloud Run
- RDS PostgreSQL with pgvector
- ElastiCache Redis
- Load balancer for scaling

## 📊 API Documentation

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/stats` | Platform statistics |
| POST | `/api/search` | Search drugs by target |
| GET | `/api/drug/{id}` | Get drug details |
| GET | `/api/target/{id}` | Get target information |
| POST | `/api/admin/cache/clear` | Clear caches |

### Request/Response Examples

#### Search Drugs
```bash
POST /api/search
{
  "query": "BRCA1",
  "query_type": "gene",
  "max_results": 20
}
```

**Response:**
```json
{
  "results": [
    {
      "chembl_id": "CHEMBL25",
      "name": "Aspirin",
      "smiles": "CC(=O)Oc1ccccc1C(=O)O",
      "binding_score": 85.5,
      "molecular_weight": 180.16,
      "is_drug_like": true,
      "clinical_phase": 4
    }
  ],
  "total": 1,
  "query": "BRCA1",
  "query_type": "gene"
}
```

## 🔍 Monitoring & Observability

### Logging

The application uses structured logging with the following levels:
- **DEBUG**: Detailed debugging information
- **INFO**: General information about operations
- **WARNING**: Warning messages
- **ERROR**: Error conditions

### Health Checks

- **Application Health**: `/health` endpoint
- **Database Connectivity**: Automatic checks
- **Model Status**: Model loading verification
- **Cache Status**: Redis connectivity

### Performance Metrics

- **Response Times**: Tracked per endpoint
- **Cache Hit Rates**: Redis cache performance
- **Model Inference Time**: AI model performance
- **Database Query Times**: Database performance

## 🔒 Security

### Best Practices

- **CORS**: Configurable allowed origins
- **Rate Limiting**: Implement per endpoint
- **Input Validation**: Pydantic schema validation
- **SQL Injection Protection**: Parameterized queries
- **XSS Protection**: Input sanitization

### Environment Variables

- **Never commit `.env` files**
- **Use strong database passwords**
- **Rotate API keys regularly**
- **Monitor for suspicious activity**

## 🚨 Troubleshooting

### Common Issues

#### Model Loading Errors
```bash
# Check available memory
free -h

# Try CPU-only mode
export DEVICE=cpu

# Clear model cache
rm -rf models/
```

#### Database Connection Issues
```bash
# Test connection
python -c "from app.database.db import test_database_connection; print(asyncio.run(test_database_connection()))"

# Check PostgreSQL logs
docker logs postgres
```

#### Redis Connection Issues
```bash
# Test Redis connection
redis-cli ping

# Check Redis logs
docker logs redis
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with detailed output
uvicorn app.main:app --reload --log-level debug
```

## 📈 Performance Optimization

### Caching Strategy

1. **Protein Embeddings**: Cache ESM-2 embeddings (most expensive)
2. **Drug Fingerprints**: Cache Morgan fingerprints
3. **API Responses**: Cache frequent queries
4. **Database Queries**: Connection pooling

### Database Optimization

1. **Indexes**: On frequently queried columns
2. **Connection Pooling**: Reuse database connections
3. **Query Optimization**: Efficient SQL queries

### Model Optimization

1. **Batch Processing**: Process multiple items together
2. **Model Quantization**: Reduce model size if needed
3. **GPU Acceleration**: Use CUDA when available

## 🔄 Updates and Maintenance

### Regular Tasks

1. **Data Updates**: Re-run `download_data.py` periodically
2. **Cache Management**: Monitor and clear caches as needed
3. **Model Updates**: Update to newer model versions
4. **Security Updates**: Keep dependencies updated

### Backup Strategy

1. **Database Backups**: Regular PostgreSQL dumps
2. **Configuration Backups**: Version control for configs
3. **Data Backups**: Backup data files

## 📚 API Reference

### Authentication

Currently no authentication (development mode). For production:

```python
# Add to requirements.txt
pip install python-jose[cryptography]
pip install passlib[bcrypt]
pip install python-multipart
```

### Rate Limiting

```python
# Add to requirements.txt
pip install slowapi
```

### API Versioning

Current version: `v1`
- Breaking changes will increment major version
- New features increment minor version
- Bug fixes increment patch version

## 🤝 Contributing

### Development Workflow

1. **Fork** the repository
2. **Create** feature branch
3. **Implement** changes
4. **Test** thoroughly
5. **Submit** pull request

### Code Standards

- **Type Hints**: All functions should have type hints
- **Docstrings**: Google-style docstrings
- **Tests**: 80%+ test coverage required
- **Linting**: Black, isort, flake8 compliance
- **Documentation**: Update README for new features

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- **Meta AI** for ESM-2 protein language model
- **RDKit** for cheminformatics tools
- **ChEMBL** for drug bioactivity data
- **UniProt** for protein sequence data
- **FastAPI** for the excellent web framework
- **PostgreSQL** for reliable data storage

---

**Status**: ✅ Production Ready | 🔬 Scientifically Accurate | 🚀 High Performance

Built for pharmaceutical research and drug discovery applications.
