"""
ChEMBL API Client

Fetches drug and molecule data from ChEMBL database.
ChEMBL is a large-scale bioactivity database maintained by EMBL-EBI.

API Documentation: https://chembl.gitbook.io/chembl-interface-documentation/
"""
import asyncio
import time
from typing import Dict, List, Optional, Any
import structlog
import httpx

logger = structlog.get_logger()

from app.config import settings


class ChEMBLClient:
    """
    Client for ChEMBL database API

    Args:
        base_url: ChEMBL API base URL
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts
        retry_delay: Delay between retries in seconds
    """

    def __init__(
        self,
        base_url: str = settings.CHEMBL_API_URL,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        logger.info("ChEMBL client initialized", base_url=base_url)

    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make HTTP request to ChEMBL API with retry logic

        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters

        Returns:
            JSON response data

        Raises:
            RuntimeError: If request fails after retries
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    logger.debug(f"Making ChEMBL request", url=url, attempt=attempt + 1)

                    response = await client.get(url, params=params)

                    if response.status_code == 200:
                        return response.json()
                    elif response.status_code == 404:
                        logger.warning(f"ChEMBL resource not found", url=url)
                        return {"error": "Not found"}
                    else:
                        logger.warning(
                            f"ChEMBL API error",
                            status_code=response.status_code,
                            url=url
                        )

            except httpx.TimeoutException:
                logger.warning(f"ChEMBL request timeout", url=url, attempt=attempt + 1)
            except httpx.RequestError as e:
                logger.warning(f"ChEMBL request error", error=str(e), attempt=attempt + 1)

            # Wait before retry (except on last attempt)
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff

        raise RuntimeError(f"ChEMBL API request failed after {self.max_retries} attempts")

    async def fetch_approved_drugs(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Fetch FDA-approved drugs from ChEMBL

        Args:
            limit: Maximum number of drugs to return

        Returns:
            List of drug dictionaries
        """
        try:
            logger.info(f"Fetching approved drugs from ChEMBL", limit=limit)

            # ChEMBL API endpoint for molecules
            endpoint = "molecule.json"

            params = {
                "max_phase": 4,  # Approved drugs only
                "limit": min(limit, 1000),  # ChEMBL limits to 1000 per request
                "format": "json"
            }

            response_data = await self._make_request(endpoint, params)

            molecules = response_data.get("molecules", [])
            drugs = []

            for mol in molecules:
                try:
                    # Extract relevant fields
                    drug = {
                        "chembl_id": mol.get("molecule_chembl_id"),
                        "name": mol.get("pref_name"),
                        "smiles": self._extract_smiles(mol),
                        "molecular_weight": mol.get("molecule_properties", {}).get("mw_freebase"),
                        "clinical_phase": mol.get("max_phase", 4),
                        "drugbank_id": None,  # Would need additional API call
                        "description": None,   # Would need additional API call
                        "inchi_key": None      # Would need additional API call
                    }

                    # Only include drugs with SMILES
                    if drug["smiles"]:
                        drugs.append(drug)

                except Exception as e:
                    logger.warning(f"Error processing drug {mol.get('molecule_chembl_id')}: {e}")
                    continue

            logger.info(f"Retrieved {len(drugs)} approved drugs from ChEMBL")
            return drugs

        except Exception as e:
            logger.error(f"Failed to fetch approved drugs: {e}")
            return []

    def _extract_smiles(self, molecule_data: Dict) -> Optional[str]:
        """
        Extract SMILES string from molecule data

        Args:
            molecule_data: ChEMBL molecule dictionary

        Returns:
            SMILES string or None if not available
        """
        # Try different SMILES fields
        molecule_structures = molecule_data.get("molecule_structures", {})

        # Canonical SMILES is preferred
        smiles = molecule_structures.get("canonical_smiles")
        if smiles:
            return smiles

        # Fall back to standard SMILES
        smiles = molecule_structures.get("standard_smiles")
        if smiles:
            return smiles

        return None

    async def fetch_drug_by_id(self, chembl_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch detailed drug information by ChEMBL ID

        Args:
            chembl_id: ChEMBL identifier

        Returns:
            Drug dictionary or None if not found
        """
        try:
            logger.info(f"Fetching drug details", chembl_id=chembl_id)

            endpoint = f"molecule/{chembl_id}.json"

            response_data = await self._make_request(endpoint)

            if "error" in response_data:
                return None

            molecule = response_data.get("molecules", [{}])[0]

            if not molecule:
                return None

            # Extract comprehensive drug information
            drug = {
                "chembl_id": molecule.get("molecule_chembl_id"),
                "name": molecule.get("pref_name"),
                "smiles": self._extract_smiles(molecule),
                "inchi_key": molecule.get("molecule_structures", {}).get("standard_inchi_key"),
                "molecular_weight": molecule.get("molecule_properties", {}).get("mw_freebase"),
                "logp": molecule.get("molecule_properties", {}).get("alogp"),
                "clinical_phase": molecule.get("max_phase", 4),
                "drugbank_id": None,  # Would need cross-reference
                "pubchem_cid": None,  # Would need cross-reference
                "atc_codes": molecule.get("atc_classifications", []),
                "indications": [],  # Would need drug indications API
                "mechanism_of_action": None,  # Would need mechanism API
                "metabolism": None,  # Would need metabolism API
                "toxicity": None,    # Would need toxicity API
                "half_life": None,   # Would need pharmacokinetics API
                "bioavailability": None  # Would need pharmacokinetics API
            }

            # Fetch additional information if needed
            # TODO: Implement drug indications, mechanism, etc.

            logger.info(f"Retrieved drug details", chembl_id=chembl_id)
            return drug

        except Exception as e:
            logger.error(f"Failed to fetch drug {chembl_id}: {e}")
            return None

    async def search_similar_drugs(self, smiles: str, limit: int = 10) -> List[str]:
        """
        Search for drugs similar to a given structure

        Args:
            smiles: SMILES string of query molecule
            limit: Maximum number of similar drugs to return

        Returns:
            List of similar drug ChEMBL IDs
        """
        try:
            logger.info(f"Searching for similar drugs", query_smiles_length=len(smiles))

            # This would require similarity search functionality
            # ChEMBL doesn't have direct similarity search API
            # TODO: Implement using molecular fingerprints

            logger.info("Drug similarity search not yet implemented")
            return []

        except Exception as e:
            logger.error(f"Similar drug search failed: {e}")
            return []

    async def get_drug_indications(self, chembl_id: str) -> List[str]:
        """
        Get clinical indications for a drug

        Args:
            chembl_id: ChEMBL identifier

        Returns:
            List of indication strings
        """
        try:
            # TODO: Implement drug indications API call
            # This would use ChEMBL's drug indications endpoint
            logger.info("Drug indications lookup not yet implemented")
            return []

        except Exception as e:
            logger.error(f"Drug indications lookup failed: {e}")
            return []

    async def get_drug_mechanism(self, chembl_id: str) -> Optional[str]:
        """
        Get mechanism of action for a drug

        Args:
            chembl_id: ChEMBL identifier

        Returns:
            Mechanism of action string or None
        """
        try:
            # TODO: Implement mechanism of action API call
            logger.info("Mechanism of action lookup not yet implemented")
            return None

        except Exception as e:
            logger.error(f"Mechanism lookup failed: {e}")
            return None


# Global client instance
chembl_client = ChEMBLClient()


# Convenience functions
async def fetch_approved_drugs(limit: int = 1000) -> List[Dict[str, Any]]:
    """Fetch FDA-approved drugs from ChEMBL"""
    return await chembl_client.fetch_approved_drugs(limit)


async def fetch_drug_by_id(chembl_id: str) -> Optional[Dict[str, Any]]:
    """Fetch drug by ChEMBL ID"""
    return await chembl_client.fetch_drug_by_id(chembl_id)


async def search_similar_drugs(smiles: str, limit: int = 10) -> List[str]:
    """Search for similar drugs"""
    return await chembl_client.search_similar_drugs(smiles, limit)
