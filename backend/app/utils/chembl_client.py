"""
ChEMBL API Client

Fetches drug and molecule data from ChEMBL database

TODO: YOU NEED TO IMPLEMENT THIS!

ChEMBL REST API documentation:
https://chembl.gitbook.io/chembl-interface-documentation/web-services/chembl-data-web-services

Example API calls:
- Get approved drugs: /api/data/molecule?max_phase=4
- Get drug by ID: /api/data/molecule/CHEMBL25
"""

import requests
from typing import List, Dict, Optional
from app.config import settings

CHEMBL_API_BASE = settings.CHEMBL_API_URL


async def fetch_approved_drugs(limit: int = 100) -> List[Dict]:
    """
    Fetch FDA-approved drugs from ChEMBL
    
    Args:
        limit: Maximum number of drugs to return
    
    Returns:
        List of drug dictionaries
    
    TODO:
    - Query ChEMBL API for approved drugs (max_phase=4)
    - Parse response
    - Extract relevant fields (chembl_id, name, smiles, etc.)
    - Return list of drug dictionaries
    
    Example implementation:
    ```python
    url = f"{CHEMBL_API_BASE}/molecule.json"
    params = {
        'max_phase': 4,
        'limit': limit
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    drugs = []
    for mol in data['molecules']:
        drugs.append({
            'chembl_id': mol['molecule_chembl_id'],
            'name': mol['pref_name'],
            'smiles': mol['molecule_structures']['canonical_smiles'],
            'clinical_phase': mol['max_phase']
        })
    return drugs
    ```
    """
    print(f"⚠️  fetch_approved_drugs() NOT FULLY IMPLEMENTED")
    print(f"   TODO: Fetch {limit} approved drugs from ChEMBL API")
    
    # PLACEHOLDER: Return sample drugs
    # Replace with actual ChEMBL API call
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
        },
        {
            'chembl_id': 'CHEMBL502',
            'name': 'Paracetamol',
            'smiles': 'CC(=O)Nc1ccc(O)cc1',
            'clinical_phase': 4
        },
        {
            'chembl_id': 'CHEMBL1201247',
            'name': 'Metformin',
            'smiles': 'CN(C)C(=N)NC(=N)N',
            'clinical_phase': 4
        },
        {
            'chembl_id': 'CHEMBL12',
            'name': 'Atenolol',
            'smiles': 'CC(C)NCC(O)COc1ccc(CC(N)=O)cc1',
            'clinical_phase': 4
        }
    ]
    
    return sample_drugs[:limit]


async def fetch_drug_by_id(chembl_id: str) -> Optional[Dict]:
    """
    Fetch drug information by ChEMBL ID
    
    Args:
        chembl_id: ChEMBL identifier
    
    Returns:
        Drug dictionary or None
    
    TODO: Implement single drug lookup
    """
    print(f"⚠️  fetch_drug_by_id() NOT FULLY IMPLEMENTED")
    print(f"   TODO: Fetch drug {chembl_id} from ChEMBL")
    
    # PLACEHOLDER
    drugs = await fetch_approved_drugs(limit=100)
    for drug in drugs:
        if drug['chembl_id'] == chembl_id:
            return drug
    return None


async def search_drugs_by_structure(smiles: str, similarity_threshold: float = 0.8) -> List[Dict]:
    """
    Search for drugs similar to a given structure
    
    Args:
        smiles: SMILES string
        similarity_threshold: Tanimoto similarity threshold
    
    Returns:
        List of similar drugs
    
    TODO: Implement structure similarity search
    """
    print(f"⚠️  search_drugs_by_structure() NOT IMPLEMENTED")
    print(f"   TODO: Search similar structures in ChEMBL")
    
    return []

