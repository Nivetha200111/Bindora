"""
Drug Service - Detailed drug information and operations

Provides comprehensive drug information including molecular properties,
clinical trial data, similar drugs, and detailed molecular analysis.
"""
import time
from typing import Dict, List, Optional, Union
import structlog

logger = structlog.get_logger()

from app.models.drug_encoder import DrugEncoder
from app.utils.chembl_client import fetch_drug_by_id, search_similar_drugs


class DrugService:
    """
    Service for detailed drug information and operations

    Args:
        drug_encoder: Initialized DrugEncoder instance
    """

    def __init__(self, drug_encoder: DrugEncoder):
        self.drug_encoder = drug_encoder

        logger.info("Drug service initialized")

    async def get_drug_details(self, chembl_id: str) -> Dict[str, Union[str, float, int, bool, List]]:
        """
        Get comprehensive drug information

        Args:
            chembl_id: ChEMBL identifier

        Returns:
            Complete drug information dictionary

        Raises:
            ValueError: If drug not found
        """
        start_time = time.time()

        logger.info(f"Fetching drug details", chembl_id=chembl_id)

        try:
            # Fetch basic drug data from ChEMBL
            drug_data = await fetch_drug_by_id(chembl_id)

            if not drug_data:
                raise ValueError(f"Drug not found: {chembl_id}")

            # Calculate comprehensive molecular properties
            molecular_properties = await self._calculate_molecular_properties(drug_data)

            # Find similar drugs
            similar_drugs = await self._find_similar_drugs(drug_data)

            # Get clinical trial information
            clinical_trials = await self._get_clinical_trials(drug_data)

            # Build comprehensive response
            drug_details = {
                "chembl_id": drug_data.get("chembl_id", chembl_id),
                "name": drug_data.get("name"),
                "smiles": drug_data.get("smiles", ""),
                "description": drug_data.get("description"),
                "inchi_key": drug_data.get("inchi_key"),
                "molecular_properties": molecular_properties,
                "similar_drugs": similar_drugs,
                "clinical_trials": clinical_trials,
                "is_drug_like": molecular_properties.get("is_drug_like", False),
                "clinical_phase": drug_data.get("clinical_phase", 4),
                "drugbank_id": drug_data.get("drugbank_id"),
                "pubchem_cid": drug_data.get("pubchem_cid"),
                "atc_codes": drug_data.get("atc_codes", []),
                "indications": drug_data.get("indications", []),
                "mechanism_of_action": drug_data.get("mechanism_of_action"),
                "metabolism": drug_data.get("metabolism"),
                "toxicity": drug_data.get("toxicity"),
                "half_life": drug_data.get("half_life"),
                "bioavailability": drug_data.get("bioavailability")
            }

            details_time = time.time() - start_time

            logger.info(
                f"Retrieved drug details",
                chembl_id=chembl_id,
                name=drug_details.get("name"),
                retrieval_time=f"{details_time".2f"}s"
            )

            return drug_details

        except Exception as e:
            logger.error(f"Failed to get drug details for {chembl_id}: {e}")
            raise ValueError(f"Drug details retrieval failed: {e}")

    async def _calculate_molecular_properties(self, drug_data: Dict) -> Dict[str, Union[float, int, bool]]:
        """
        Calculate comprehensive molecular properties

        Args:
            drug_data: Basic drug information

        Returns:
            Dictionary of molecular properties
        """
        smiles = drug_data.get("smiles", "")

        if not smiles:
            return {}

        try:
            # Get standard descriptors
            descriptors = self.drug_encoder.encode_descriptors(smiles)

            # Calculate additional properties
            additional_props = await self._calculate_advanced_properties(smiles)

            # Combine all properties
            all_properties = {**descriptors, **additional_props}

            # Check drug-likeness
            is_drug_like = self.drug_encoder.is_drug_like(smiles)

            # Add drug-likeness to properties
            all_properties["is_drug_like"] = is_drug_like

            # Add Lipinski rule compliance details
            all_properties.update(self._check_lipinski_rules(all_properties))

            logger.debug(
                f"Calculated molecular properties",
                num_properties=len(all_properties),
                is_drug_like=is_drug_like
            )

            return all_properties

        except Exception as e:
            logger.error(f"Failed to calculate molecular properties: {e}")
            return {"is_drug_like": False}

    async def _calculate_advanced_properties(self, smiles: str) -> Dict[str, Union[float, int]]:
        """
        Calculate advanced molecular properties

        Args:
            smiles: SMILES string

        Returns:
            Dictionary of advanced properties
        """
        try:
            from rdkit import Chem
            from rdkit.Chem import Descriptors, GraphDescriptors, Crippen

            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return {}

            properties = {}

            # Pharmacokinetic properties
            properties["tpsa"] = float(Descriptors.TPSA(mol))

            # Structural properties
            properties["num_rotatable_bonds"] = int(Descriptors.NumRotatableBonds(mol))
            properties["num_rings"] = int(Descriptors.RingCount(mol))
            properties["num_aromatic_rings"] = int(Descriptors.NumAromaticRings(mol))
            properties["num_aliphatic_rings"] = int(Descriptors.NumAliphaticRings(mol))

            # Molecular complexity
            properties["fraction_sp3"] = float(Descriptors.FractionCSP3(mol))
            properties["num_stereocenters"] = int(len(Chem.FindMolChiralCenters(mol)))

            # Solubility prediction (rough estimate)
            properties["logp"] = float(Crippen.MolLogP(mol))

            # Synthetic accessibility (if available)
            try:
                from rdkit.Chem import rdMolDescriptors
                properties["synthetic_accessibility"] = float(rdMolDescriptors.CalculateSAScore(mol))
            except:
                properties["synthetic_accessibility"] = 0.0

            return properties

        except Exception as e:
            logger.warning(f"Failed to calculate advanced properties: {e}")
            return {}

    def _check_lipinski_rules(self, properties: Dict) -> Dict[str, bool]:
        """
        Check compliance with Lipinski's Rule of Five

        Args:
            properties: Molecular properties dictionary

        Returns:
            Dictionary with rule compliance flags
        """
        rules = {}

        try:
            # Rule 1: Molecular weight ≤ 500
            rules["molecular_weight_ok"] = properties.get("molecular_weight", 0) <= 500

            # Rule 2: LogP ≤ 5
            rules["logp_ok"] = properties.get("logp", 0) <= 5

            # Rule 3: H-bond donors ≤ 5
            rules["hbd_ok"] = properties.get("hbd", 0) <= 5

            # Rule 4: H-bond acceptors ≤ 10
            rules["hba_ok"] = properties.get("hba", 0) <= 10

            # Overall compliance
            rules["passes_lipinski"] = all([
                rules["molecular_weight_ok"],
                rules["logp_ok"],
                rules["hbd_ok"],
                rules["hba_ok"]
            ])

        except Exception as e:
            logger.warning(f"Failed to check Lipinski rules: {e}")
            rules = {
                "molecular_weight_ok": False,
                "logp_ok": False,
                "hbd_ok": False,
                "hba_ok": False,
                "passes_lipinski": False
            }

        return rules

    async def _find_similar_drugs(self, drug_data: Dict) -> List[str]:
        """
        Find structurally similar drugs

        Args:
            drug_data: Drug information

        Returns:
            List of similar drug ChEMBL IDs
        """
        try:
            smiles = drug_data.get("smiles", "")

            if not smiles:
                return []

            # Search for similar drugs using fingerprint similarity
            similar_drugs = await search_similar_drugs(smiles, limit=10)

            # Filter out the query drug itself
            query_chembl_id = drug_data.get("chembl_id")
            similar_drugs = [
                drug_id for drug_id in similar_drugs
                if drug_id != query_chembl_id
            ]

            logger.debug(
                f"Found similar drugs",
                query_drug=query_chembl_id,
                num_similar=len(similar_drugs)
            )

            return similar_drugs

        except Exception as e:
            logger.warning(f"Failed to find similar drugs: {e}")
            return []

    async def _get_clinical_trials(self, drug_data: Dict) -> List[Dict]:
        """
        Get clinical trial information for a drug

        Args:
            drug_data: Drug information

        Returns:
            List of clinical trial dictionaries
        """
        # TODO: Implement clinical trial data fetching
        # This would integrate with ClinicalTrials.gov API or other sources

        logger.debug("Clinical trials lookup not yet implemented")

        return []

    async def get_drug_properties(self, chembl_id: str) -> Dict[str, Union[float, int, bool]]:
        """
        Get just molecular properties for a drug (lighter than full details)

        Args:
            chembl_id: ChEMBL identifier

        Returns:
            Molecular properties dictionary
        """
        try:
            drug_data = await fetch_drug_by_id(chembl_id)

            if not drug_data or not drug_data.get("smiles"):
                return {}

            properties = await self._calculate_molecular_properties(drug_data)

            logger.debug(
                f"Retrieved drug properties",
                chembl_id=chembl_id,
                num_properties=len(properties)
            )

            return properties

        except Exception as e:
            logger.error(f"Failed to get drug properties for {chembl_id}: {e}")
            return {}

    async def validate_drug_smiles(self, smiles: str) -> Dict[str, Union[bool, str]]:
        """
        Validate SMILES string and return validation results

        Args:
            smiles: SMILES string to validate

        Returns:
            Validation results dictionary
        """
        try:
            is_valid = self.drug_encoder.is_valid_smiles(smiles)

            if not is_valid:
                return {
                    "valid": False,
                    "error": "Invalid SMILES format"
                }

            # Check if drug-like
            is_drug_like = self.drug_encoder.is_drug_like(smiles)

            # Get basic properties
            descriptors = self.drug_encoder.encode_descriptors(smiles)

            return {
                "valid": True,
                "is_drug_like": is_drug_like,
                "molecular_weight": descriptors.get("molecular_weight", 0),
                "logp": descriptors.get("logp", 0),
                "hbd": descriptors.get("hbd", 0),
                "hba": descriptors.get("hba", 0),
                "tpsa": descriptors.get("tpsa", 0)
            }

        except Exception as e:
            logger.error(f"SMILES validation failed: {e}")
            return {
                "valid": False,
                "error": str(e)
            }

    def __repr__(self) -> str:
        return "DrugService(drug_encoder=DrugEncoder)"
