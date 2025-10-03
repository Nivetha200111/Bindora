"""
Data Download Script

Run this script to download and prepare drug and protein data for the platform.

Usage:
    python data/download_data.py

TODO: YOU NEED TO IMPLEMENT THIS!

This script should:
1. Download FDA-approved drugs from ChEMBL
2. Download protein targets from UniProt
3. Download known drug-target interactions from BindingDB
4. Save to CSV/JSON files or database
5. Generate embeddings (optional, can be done on-demand)

For MVP: Download a small dataset of ~100 drugs
For V2: Full database with thousands of drugs and targets
"""

import pandas as pd
import requests
import os
from pathlib import Path

DATA_DIR = Path(__file__).parent


def download_approved_drugs():
    """
    Download FDA-approved drugs from ChEMBL
    
    TODO: Implement ChEMBL data download
    
    Example:
    - Query ChEMBL API for max_phase=4 (approved drugs)
    - Extract chembl_id, name, smiles, molecular properties
    - Save to drugs.csv
    """
    print("📥 Downloading approved drugs from ChEMBL...")
    print("⚠️  TODO: Implement ChEMBL download")
    
    # PLACEHOLDER: Create sample data file
    sample_drugs = [
        {
            'chembl_id': 'CHEMBL25',
            'name': 'Aspirin',
            'smiles': 'CC(=O)Oc1ccccc1C(=O)O',
            'clinical_phase': 4
        },
        {
            'chembl_id': 'CHEMBL192',
            'name': 'Ibuprofen',
            'smiles': 'CC(C)Cc1ccc(cc1)C(C)C(=O)O',
            'clinical_phase': 4
        }
    ]
    
    df = pd.DataFrame(sample_drugs)
    df.to_csv(DATA_DIR / 'drugs.csv', index=False)
    print(f"✅ Saved {len(df)} drugs to drugs.csv")


def download_protein_targets():
    """
    Download protein targets from UniProt
    
    TODO: Implement UniProt data download
    
    Example:
    - Query UniProt for human proteins
    - Extract uniprot_id, gene_name, sequence
    - Save to proteins.csv
    """
    print("📥 Downloading protein targets from UniProt...")
    print("⚠️  TODO: Implement UniProt download")
    
    # PLACEHOLDER: Create sample data file
    sample_proteins = [
        {
            'uniprot_id': 'P38398',
            'gene_name': 'BRCA1',
            'sequence': 'MDLSALRVEEVQNVINAMQKILECPICLELIKEPVSTKCDHIFCKFCMLKLLNQKKGPSQC...'
        }
    ]
    
    df = pd.DataFrame(sample_proteins)
    df.to_csv(DATA_DIR / 'proteins.csv', index=False)
    print(f"✅ Saved {len(df)} proteins to proteins.csv")


def download_drug_target_interactions():
    """
    Download known drug-target interactions from BindingDB
    
    TODO: Implement BindingDB data download
    
    This is needed for training ML models (V2)
    """
    print("📥 Downloading drug-target interactions from BindingDB...")
    print("⚠️  TODO: Implement BindingDB download (V2 feature)")


def main():
    """Main execution function"""
    print("=" * 60)
    print("Drug-Target Matcher - Data Download")
    print("=" * 60)
    
    # Create data directory if it doesn't exist
    DATA_DIR.mkdir(exist_ok=True)
    
    # Download data
    download_approved_drugs()
    download_protein_targets()
    download_drug_target_interactions()
    
    print("\n" + "=" * 60)
    print("✅ Data download complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Review the downloaded data files")
    print("2. Implement the AI models in app/models/")
    print("3. Start the API server: uvicorn app.main:app --reload")


if __name__ == "__main__":
    main()

