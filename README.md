# 🎯 Drug-Target Matcher

An AI-powered drug discovery platform that predicts which drugs can bind to specific protein targets. Built with Next.js (frontend) and FastAPI (backend) with custom AI models for molecular prediction.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Next.js](https://img.shields.io/badge/next.js-14-black.svg)

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Implementation Guide](#implementation-guide)
- [API Documentation](#api-documentation)
- [Deployment](#deployment)
- [Contributing](#contributing)

## 🌟 Overview

Drug-Target Matcher accelerates drug discovery by using machine learning to predict drug-target interactions. Simply input a disease name, gene symbol, or protein sequence, and the platform returns ranked drug candidates with detailed molecular properties and binding predictions.

### Key Capabilities

- 🧬 **Protein Encoding**: Uses ESM-2 protein language models
- 💊 **Molecular Analysis**: RDKit-based cheminformatics
- 🤖 **AI Prediction**: Custom binding affinity predictor
- 📊 **Rich Visualization**: Interactive drug cards and properties
- 🔬 **Real Data**: ChEMBL, UniProt, and BindingDB integration

## ✨ Features

### Frontend (100% Complete)
- ✅ Modern Next.js 14 dashboard with TypeScript
- ✅ Shadcn/ui component library
- ✅ Three search modes: Disease, Gene, Sequence
- ✅ Interactive drug cards with binding scores
- ✅ Detailed drug information modal
- ✅ Responsive design (mobile-friendly)
- ✅ Lipinski Rule of Five validation
- ✅ ChEMBL database integration

### Backend (Structure Complete, AI Models TODO)
- ✅ FastAPI REST API with auto-docs
- ✅ Pydantic schemas for validation
- ✅ Service layer architecture
- ✅ API client utilities
- ⚠️ **YOU IMPLEMENT**: Protein encoder (ESM-2)
- ⚠️ **YOU IMPLEMENT**: Drug encoder (RDKit)
- ⚠️ **YOU IMPLEMENT**: Binding predictor

## 🛠️ Tech Stack

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI**: Shadcn/ui
- **Icons**: Lucide React

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.10+
- **AI/ML**: PyTorch, Transformers, RDKit
- **Bio**: Biopython, ChEMBL API
- **Database**: PostgreSQL (optional)

## 🚀 Quick Start

### Prerequisites
- **Node.js** 18+ (for frontend)
- **Python** 3.10+ (for backend)
- **Git**

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd drug-target-matcher
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
copy .env.example .env  # Windows
cp .env.example .env    # macOS/Linux

# Download sample data
python data/download_data.py

# Start API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will run at: http://localhost:8000
API Docs: http://localhost:8000/docs

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set up environment
copy .env.example .env.local  # Windows
cp .env.example .env.local    # macOS/Linux

# Start development server
npm run dev
```

Frontend will run at: http://localhost:3000

### 4. Test the Application

1. Open http://localhost:3000
2. Enter "BRCA1" in the gene search
3. Click "Find Drugs"
4. View results and explore drug details

## 📁 Project Structure

```
drug-target-matcher/
├── frontend/                   # Next.js application (COMPLETE ✅)
│   ├── src/
│   │   ├── app/               # Pages
│   │   ├── components/        # React components
│   │   ├── lib/               # API client & utils
│   │   └── types/             # TypeScript types
│   └── package.json
│
└── backend/                    # FastAPI application
    ├── app/
    │   ├── main.py            # FastAPI entry (COMPLETE ✅)
    │   ├── config.py          # Configuration (COMPLETE ✅)
    │   ├── api/               # Routes & schemas (COMPLETE ✅)
    │   ├── models/            # AI models (YOU IMPLEMENT ⚠️)
    │   ├── services/          # Business logic (COMPLETE ✅)
    │   └── utils/             # Helpers (COMPLETE ✅)
    ├── data/                  # Data scripts
    └── requirements.txt
```

## 🧑‍💻 Implementation Guide

The frontend is **100% complete** and ready to use. The backend structure is complete, but you need to implement the AI models.

### What YOU Need to Implement

#### 1. Protein Encoder (`backend/app/models/protein_encoder.py`)

**Goal**: Encode protein sequences into vector embeddings

**Suggested Approach**:
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

**Resources**:
- ESM-2 Model: https://huggingface.co/facebook/esm2_t33_650M_UR50D
- Transformers Docs: https://huggingface.co/docs/transformers/

#### 2. Drug Encoder (`backend/app/models/drug_encoder.py`)

**Goal**: Create molecular fingerprints and calculate properties

**Suggested Approach**:
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
            'logp': Descriptors.MolLogP(mol),
            'hbd': Lipinski.NumHDonors(mol),
            'hba': Lipinski.NumHAcceptors(mol)
        }
```

**Resources**:
- RDKit Docs: https://www.rdkit.org/docs/
- RDKit Cookbook: https://www.rdkit.org/docs/Cookbook.html

#### 3. Binding Predictor (`backend/app/models/binding_predictor.py`)

**Goal**: Predict drug-target binding affinity

**MVP Approach (Simple)**:
```python
from sklearn.metrics.pairwise import cosine_similarity

class BindingPredictor:
    def predict_binding_simple(self, protein_emb, drug_fp):
        similarity = cosine_similarity([protein_emb], [drug_fp])[0][0]
        score = (similarity + 1) * 50  # Scale to 0-100
        return max(0, min(100, score))
```

**V2 Approach (Advanced)**:
- Train ML model on BindingDB dataset
- Use attention mechanisms
- Implement confidence intervals

### Implementation Steps

1. **Start with Drug Encoder** (easiest)
   - Install RDKit: `conda install -c conda-forge rdkit`
   - Implement `encode_morgan_fingerprint()`
   - Implement `encode_descriptors()`
   - Test with sample SMILES

2. **Implement Protein Encoder** (medium)
   - Install transformers: `pip install transformers`
   - Load ESM-2 model
   - Implement `encode()`
   - Test with sample sequence

3. **Build Binding Predictor** (simple MVP)
   - Use cosine similarity
   - Scale scores to 0-100
   - Test with sample data

4. **Integrate Everything**
   - Update `search_service.py`
   - Test end-to-end flow
   - Optimize performance

## 📡 API Documentation

### Endpoints

#### Search for Drugs
```http
POST /api/search
Content-Type: application/json

{
  "query": "BRCA1",
  "query_type": "gene",
  "max_results": 20
}
```

**Response**:
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
  "total": 1
}
```

#### Get Drug Details
```http
GET /api/drug/{chembl_id}
```

#### Platform Stats
```http
GET /api/stats
```

**Full API docs**: http://localhost:8000/docs

## 🚢 Deployment

### Frontend (Vercel)

```bash
cd frontend
vercel deploy
```

Set environment variable:
- `NEXT_PUBLIC_API_URL`: Your backend URL

### Backend (Railway)

```bash
cd backend
railway up
```

Or use Railway.app dashboard for GUI deployment.

### Docker (Optional)

```bash
docker-compose up
```

See `docker-compose.yml` in project root.

## 📚 Resources

### Learning Materials
- **FastAPI**: https://fastapi.tiangolo.com/
- **Next.js**: https://nextjs.org/docs
- **RDKit**: https://www.rdkit.org/docs/
- **ESM-2**: https://github.com/facebookresearch/esm
- **ChEMBL**: https://www.ebi.ac.uk/chembl/

### Data Sources
- **ChEMBL**: Drug and target data
- **UniProt**: Protein sequences
- **BindingDB**: Binding affinity data
- **PubChem**: Chemical structures

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 🤝 Contributing

1. Fork the repository
2. Implement AI models in `backend/app/models/`
3. Add tests
4. Submit pull request

## 📝 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- **ChEMBL** for drug data
- **UniProt** for protein sequences
- **Meta AI** for ESM-2 model
- **RDKit** for cheminformatics tools
- **Vercel** for Next.js and hosting

## 📞 Support

- 📖 **Documentation**: See `/backend/README.md` and `/frontend/README.md`
- 🐛 **Issues**: Open a GitHub issue
- 💬 **Discussions**: GitHub Discussions

---

**Status**: Frontend ✅ Complete | Backend Structure ✅ Complete | AI Models ⚠️ TODO

Built with ❤️ for drug discovery research

