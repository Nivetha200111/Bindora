# Drug-Target Matcher - Backend API

FastAPI-based backend service for AI-powered drug-target interaction prediction.

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- pip or conda package manager
- (Optional) CUDA-capable GPU for faster inference

### Installation

1. **Create virtual environment:**
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables:**
```bash
# Copy example env file
copy .env.example .env  # Windows
cp .env.example .env    # macOS/Linux

# Edit .env with your settings (optional for MVP)
```

4. **Download data (first time only):**
```bash
python data/download_data.py
```

5. **Start the server:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📁 Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── api/                 # API routes and schemas
│   │   ├── routes.py
│   │   └── schemas.py
│   ├── models/              # AI models (YOU IMPLEMENT)
│   │   ├── protein_encoder.py
│   │   ├── drug_encoder.py
│   │   └── binding_predictor.py
│   ├── services/            # Business logic (YOU IMPLEMENT)
│   │   ├── search_service.py
│   │   ├── drug_service.py
│   │   └── target_service.py
│   └── utils/               # Helper utilities
│       ├── chembl_client.py
│       └── uniprot_client.py
├── data/                    # Data scripts and files
├── tests/                   # Unit tests
└── requirements.txt         # Python dependencies
```

## 🔬 What YOU Need to Implement

The backend structure is complete, but the AI components need implementation:

### 1. Protein Encoder (`app/models/protein_encoder.py`)
**Goal:** Encode protein sequences into vector embeddings

**Suggested approach:**
- Use Hugging Face's `transformers` library
- Load pre-trained ESM-2 model: `facebook/esm2_t33_650M_UR50D`
- Implement `encode()` and `batch_encode()` methods

**Example:**
```python
from transformers import AutoTokenizer, AutoModel
import torch

class ProteinEncoder:
    def __init__(self, model_name="facebook/esm2_t33_650M_UR50D"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.eval()
    
    def encode(self, sequence: str):
        inputs = self.tokenizer(sequence, return_tensors="pt")
        with torch.no_grad():
            outputs = self.model(**inputs)
        return outputs.last_hidden_state.mean(dim=1).numpy()[0]
```

### 2. Drug Encoder (`app/models/drug_encoder.py`)
**Goal:** Create molecular fingerprints and calculate properties

**Suggested approach:**
- Use RDKit for cheminformatics
- Implement Morgan fingerprints
- Calculate Lipinski properties

**Example:**
```python
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors

class DrugEncoder:
    def encode_morgan_fingerprint(self, smiles: str):
        mol = Chem.MolFromSmiles(smiles)
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048)
        return np.array(fp)
    
    def encode_descriptors(self, smiles: str):
        mol = Chem.MolFromSmiles(smiles)
        return {
            'molecular_weight': Descriptors.MolWt(mol),
            'logp': Descriptors.MolLogP(mol)
        }
```

### 3. Binding Predictor (`app/models/binding_predictor.py`)
**Goal:** Predict drug-target binding affinity

**MVP approach (simple):**
- Calculate cosine similarity between protein embedding and drug fingerprint
- Scale to 0-100 score

**V2 approach (advanced):**
- Train neural network on BindingDB dataset
- Use attention mechanisms for interpretability

## 🧪 Testing

```bash
# Run tests
pytest tests/

# Test specific module
pytest tests/test_encoders.py

# With coverage
pytest --cov=app tests/
```

## 📡 API Endpoints

### Search for drugs
```bash
POST /api/search
{
  "query": "BRCA1",
  "query_type": "gene",
  "max_results": 20
}
```

### Get drug details
```bash
GET /api/drug/CHEMBL25
```

### Health check
```bash
GET /health
```

## 🔧 Configuration

Edit `.env` file for configuration:

```bash
# API settings
API_HOST=0.0.0.0
API_PORT=8000
ALLOWED_ORIGINS=http://localhost:3000

# Model settings
PROTEIN_MODEL=facebook/esm2_t33_650M_UR50D
DRUG_MODEL=seyonec/ChemBERTa-zinc-base-v1

# Paths
DATA_DIR=./data
MODEL_CACHE_DIR=./models
```

## 🚢 Deployment

### Local Development
```bash
uvicorn app.main:app --reload
```

### Production
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Docker
```bash
docker build -t drug-target-matcher-backend .
docker run -p 8000:8000 drug-target-matcher-backend
```

### Recommended Platforms
- **Railway.app** (easiest, GPU support)
- **Render.com** (free tier available)
- **AWS ECS / GCP Cloud Run** (production scale)

## 📚 Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Hugging Face Transformers**: https://huggingface.co/docs/transformers/
- **RDKit Documentation**: https://www.rdkit.org/docs/
- **ChEMBL API**: https://chembl.gitbook.io/chembl-interface-documentation/
- **UniProt API**: https://www.uniprot.org/help/api

## 🐛 Troubleshooting

### Import errors
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### RDKit installation issues
```bash
# Use conda instead
conda install -c conda-forge rdkit
```

### Out of memory errors
- Reduce batch size in encoders
- Use smaller model: `facebook/esm2_t12_35M_UR50D`
- Enable CPU-only mode

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

1. Implement AI models in `app/models/`
2. Add business logic in `app/services/`
3. Write tests for your implementations
4. Update this README with your learnings

---

**Next Steps:**
1. Implement the three AI model classes
2. Test with sample data
3. Connect to frontend
4. Deploy to Railway/Render

