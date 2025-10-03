# 🚀 Quick Setup Guide

This guide will get your Drug-Target Matcher platform running in **under 5 minutes**.

## ✅ Prerequisites Check

Before starting, ensure you have:

- [ ] **Node.js 18+** installed (`node --version`)
- [ ] **Python 3.10+** installed (`python --version`)
- [ ] **Git** installed (`git --version`)
- [ ] Terminal/Command Prompt access
- [ ] Internet connection (for downloading dependencies)

## 📦 Step 1: Backend Setup (3 minutes)

### 1.1 Navigate to Backend
```bash
cd backend
```

### 1.2 Create Virtual Environment
**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### 1.3 Install Dependencies
```bash
pip install -r requirements.txt
```

This will take 2-3 minutes. Go grab a coffee! ☕

### 1.4 Start Backend Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

✅ **Backend is ready!** Keep this terminal open.

**Test it:** Open http://localhost:8000 in your browser. You should see:
```json
{
  "message": "Drug-Target Matcher API",
  "status": "running",
  "version": "1.0.0"
}
```

## 🎨 Step 2: Frontend Setup (2 minutes)

### 2.1 Open New Terminal
Keep the backend terminal running and open a **new terminal window**.

### 2.2 Navigate to Frontend
```bash
cd frontend
```

### 2.3 Install Dependencies
```bash
npm install
```

This will take 1-2 minutes.

### 2.4 Create Environment File
**Windows:**
```bash
copy .env.example .env.local
```

**macOS/Linux:**
```bash
cp .env.example .env.local
```

The file should contain:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 2.5 Start Frontend Server
```bash
npm run dev
```

You should see:
```
  ▲ Next.js 14.0.4
  - Local:        http://localhost:3000
  - Ready in 2s
```

✅ **Frontend is ready!** Keep this terminal open too.

## 🎯 Step 3: Test the Application

### 3.1 Open in Browser
Navigate to: **http://localhost:3000**

You should see the beautiful Drug-Target Matcher homepage! 🎉

### 3.2 Try a Search

1. On the homepage, you'll see the search form
2. Make sure **"Gene"** tab is selected
3. Enter: `BRCA1`
4. Click **"Find Drugs"**

You'll be redirected to the results page showing drug candidates!

### 3.3 Explore Drug Details

1. Click **"View Details"** on any drug card
2. Explore the tabs:
   - **Overview**: Basic info and SMILES
   - **Properties**: Molecular properties
   - **Binding**: Binding score
   - **Clinical**: Clinical phase info

## 🔍 What's Working vs. What's Not

### ✅ Fully Functional (Works Now)
- Frontend UI (100% complete)
- API routing and endpoints
- Search form with validation
- Results display
- Drug detail modal
- Responsive design
- Type-safe API integration

### ⚠️ Returns Mock Data (YOU Need to Implement)
The following return placeholder/random data because the AI models need implementation:

1. **Binding Scores** - Currently random (60-90%)
2. **Molecular Properties** - Currently random values
3. **Drug Rankings** - Currently random order

**Location of TODO Code:**
- `backend/app/models/protein_encoder.py` - Implement ESM-2 encoding
- `backend/app/models/drug_encoder.py` - Implement RDKit fingerprints
- `backend/app/models/binding_predictor.py` - Implement prediction logic

## 🛠️ Troubleshooting

### Backend Won't Start

**Error: "uvicorn: command not found"**
```bash
# Make sure venv is activated
# You should see (venv) in your prompt
pip install uvicorn
```

**Error: "Port 8000 is already in use"**
```bash
# Find and kill the process
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux:
lsof -ti:8000 | xargs kill -9
```

### Frontend Won't Start

**Error: "EADDRINUSE: port 3000 already in use"**
```bash
# Use different port
npm run dev -- -p 3001
```

**Error: "Module not found"**
```bash
# Reinstall dependencies
rm -rf node_modules
npm install
```

### API Connection Failed

**Check Backend is Running:**
```bash
curl http://localhost:8000/health
```

Should return:
```json
{"status": "healthy", "service": "drug-target-matcher"}
```

**Check Environment Variable:**
Open `frontend/.env.local` and verify:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 📚 Next Steps

### For Users
1. ✅ Try different searches (genes, sequences)
2. ✅ Explore drug details
3. ✅ Check the API docs at http://localhost:8000/docs

### For Developers
1. **Implement AI Models** (Priority!)
   - Start with `drug_encoder.py` (easiest)
   - Then `protein_encoder.py` (medium)
   - Finally `binding_predictor.py` (core logic)

2. **Read Implementation Guides**
   - See `backend/README.md` for detailed instructions
   - Check code comments for specific TODOs
   - Review example code snippets

3. **Test Your Implementations**
   - Run `pytest tests/` in backend
   - Check results in frontend

## 🎓 Learning Resources

### Protein Encoding
- ESM-2 Model: https://huggingface.co/facebook/esm2_t33_650M_UR50D
- Protein Language Models: https://github.com/facebookresearch/esm

### Drug Encoding
- RDKit Tutorial: https://www.rdkit.org/docs/GettingStartedInPython.html
- Morgan Fingerprints: https://www.rdkit.org/docs/GettingStartedInPython.html#morgan-fingerprints-circular-fingerprints

### Binding Prediction
- BindingDB: https://www.bindingdb.org/
- Drug-Target Interaction Papers: Google Scholar

## 💡 Tips

1. **Keep Both Servers Running**: You need both backend (port 8000) and frontend (port 3000)
2. **Check Browser Console**: F12 for debugging API calls
3. **Use API Docs**: http://localhost:8000/docs for testing endpoints
4. **Hot Reload**: Both servers auto-reload on code changes
5. **Git Commits**: Commit often as you implement features!

## ✨ Success Checklist

After completing this guide, you should have:

- [x] Backend running on port 8000
- [x] Frontend running on port 3000
- [x] Homepage loads with search form
- [x] Can perform searches (returns mock data)
- [x] Can view drug details in modal
- [x] API docs accessible at /docs
- [ ] Implemented protein encoder (YOUR TODO)
- [ ] Implemented drug encoder (YOUR TODO)
- [ ] Implemented binding predictor (YOUR TODO)

## 🎉 Congratulations!

Your Drug-Target Matcher platform is up and running! 

**Frontend**: 100% Complete ✅  
**Backend Structure**: 100% Complete ✅  
**AI Models**: Ready for you to implement 🚀

Now it's time to build the AI magic! Start with `backend/app/models/drug_encoder.py` as it's the easiest entry point.

---

**Need Help?**
- Check the main README.md
- Review backend/README.md for AI model implementation
- Look at the code comments marked with TODO
- Open an issue on GitHub

**Happy Coding! 🎯**

