# Data Directory

This directory contains scripts and data files for the Drug-Target Matcher platform.

## Scripts

### `download_data.py`
Downloads drug and protein data from public databases.

**Usage:**
```bash
python data/download_data.py
```

**Data Sources:**
- **ChEMBL**: FDA-approved drugs with molecular structures
- **UniProt**: Protein sequences and annotations
- **BindingDB**: Known drug-target interactions (for ML training)

**Output Files:**
- `drugs.csv`: Drug information (ChEMBL ID, name, SMILES, etc.)
- `proteins.csv`: Protein targets (UniProt ID, gene name, sequence)
- `interactions.csv`: Known drug-target interactions (for V2)

### `process_embeddings.py`
Pre-computes and caches molecular embeddings (V2 feature).

**Usage:**
```bash
python data/process_embeddings.py
```

**Note:** This is a V2 optimization. For MVP, embeddings are computed on-demand.

## Data Files

After running `download_data.py`, you'll have:

- `drugs.csv` - FDA-approved drugs
- `proteins.csv` - Protein targets
- `embeddings/` - Cached embeddings (optional)

## TODO for Developers

### MVP Phase
1. Implement `download_data.py` to fetch real data from ChEMBL
2. Create sample dataset of ~100 drugs for testing
3. Add data validation and cleaning

### V2 Phase
1. Implement full database download (thousands of drugs)
2. Add BindingDB integration for known interactions
3. Implement embedding pre-computation
4. Set up vector database (pgvector or Pinecone)
5. Add data versioning and updates

## External API Keys

Some data sources may require API keys or registration:

- **ChEMBL**: Free, no key required
- **UniProt**: Free, no key required
- **BindingDB**: Free, registration recommended for large downloads
- **PubChem**: Free, no key required

## Data Size Estimates

- **Small dataset** (100 drugs, 50 targets): ~1 MB
- **Medium dataset** (1,000 drugs, 500 targets): ~10 MB
- **Large dataset** (10,000 drugs, 5,000 targets): ~100 MB
- **Full dataset** (all approved drugs): ~500 MB
- **With pre-computed embeddings**: +1-5 GB

## License

All data is sourced from public databases with open access licenses. Please cite original sources when using the data:

- ChEMBL: https://www.ebi.ac.uk/chembl/
- UniProt: https://www.uniprot.org/
- BindingDB: https://www.bindingdb.org/

