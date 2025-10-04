"""
Drug Molecule Encoder using RDKit

Encodes drug molecules from SMILES strings into vector representations.
Supports Morgan fingerprints and molecular property calculation.
"""
import warnings
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import structlog

logger = structlog.get_logger()

try:
    from rdkit import Chem
    from rdkit.Chem import AllChem, Descriptors, Lipinski, QED
    from rdkit.Chem.rdMolDescriptors import CalcTPSA
    RDKIT_AVAILABLE = True
except ImportError:
    logger.warning("RDKit not available. Drug encoding will not work.")
    RDKIT_AVAILABLE = False


class DrugEncoder:
    """
    Drug molecule encoder using RDKit

    Args:
        fingerprint_size: Size of Morgan fingerprint (default: 2048)
        fingerprint_radius: Radius for Morgan fingerprint (default: 2)
        normalize_properties: Whether to normalize property values (default: True)
    """

    def __init__(
        self,
        fingerprint_size: int = 2048,
        fingerprint_radius: int = 2,
        normalize_properties: bool = True
    ):
        self.fingerprint_size = fingerprint_size
        self.fingerprint_radius = fingerprint_radius
        self.normalize_properties = normalize_properties

        # Check if scientific libraries are available
        self._scientific_mode = RDKIT_AVAILABLE

        if not self._scientific_mode:
            logger.warning("RDKit not available, running in demo mode")

        # Property normalization ranges (based on typical drug-like molecules)
        self.property_ranges = {
            'molecular_weight': (100, 800),
            'logp': (-5, 8),
            'hbd': (0, 10),
            'hba': (0, 15),
            'tpsa': (0, 200),
            'rotatable_bonds': (0, 20),
            'aromatic_rings': (0, 8),
            'heavy_atoms': (5, 100),
            'ring_count': (0, 10),
            'fraction_sp3': (0, 1),
            'num_stereocenters': (0, 10),
            'qed': (0, 1)  # Quantitative Estimation of Drug-likeness
        }

        logger.info(
            "Drug encoder initialized",
            fingerprint_size=fingerprint_size,
            fingerprint_radius=fingerprint_radius
        )

    def is_valid_smiles(self, smiles: str) -> bool:
        """
        Validate SMILES string format

        Args:
            smiles: SMILES string to validate

        Returns:
            True if valid SMILES format, False otherwise
        """
        if not smiles or not isinstance(smiles, str):
            return False

        try:
            mol = Chem.MolFromSmiles(smiles)
            return mol is not None
        except Exception:
            return False

    def _parse_molecule(self, smiles: str) -> Optional[Chem.Mol]:
        """
        Parse SMILES string into RDKit molecule object

        Args:
            smiles: SMILES string

        Returns:
            RDKit molecule object or None if parsing fails
        """
        try:
            mol = Chem.MolFromSmiles(smiles)

            if mol is None:
                logger.warning(f"Failed to parse SMILES: {smiles}")
                return None

            # Sanitize molecule
            Chem.SanitizeMol(mol)

            return mol

        except Exception as e:
            logger.warning(f"Error parsing SMILES {smiles}: {e}")
            return None

    def encode_morgan_fingerprint(self, smiles: str) -> np.ndarray:
        """
        Generate Morgan (circular) fingerprint for a molecule

        Args:
            smiles: SMILES string

        Returns:
            Binary fingerprint as numpy array of shape (fingerprint_size,)

        Raises:
            ValueError: If SMILES is invalid
        """
        if not self._scientific_mode:
            # Demo mode: return mock fingerprint
            logger.info("Using demo mode for drug fingerprinting")
            return self._generate_mock_fingerprint(smiles)

        mol = self._parse_molecule(smiles)

        if mol is None:
            raise ValueError(f"Invalid SMILES string: {smiles}")

        try:
            # Generate Morgan fingerprint
            fp = AllChem.GetMorganFingerprintAsBitVect(
                mol,
                radius=self.fingerprint_radius,
                nBits=self.fingerprint_size
            )

            # Convert to numpy array
            fingerprint = np.array(fp, dtype=np.float32)

            logger.debug(
                f"Generated Morgan fingerprint",
                smiles_length=len(smiles),
                fingerprint_size=fingerprint.shape[0],
                active_bits=int(fingerprint.sum())
            )

            return fingerprint

        except Exception as e:
            logger.error(f"Failed to generate fingerprint for {smiles}: {e}")
            raise RuntimeError(f"Fingerprint generation failed: {e}")

    def encode_descriptors(self, smiles: str) -> Dict[str, float]:
        """
        Calculate molecular descriptors for a drug molecule

        Args:
            smiles: SMILES string

        Returns:
            Dictionary of molecular properties

        Raises:
            ValueError: If SMILES is invalid
        """
        if not self._scientific_mode:
            # Demo mode: return mock descriptors
            logger.info("Using demo mode for molecular descriptors")
            return self._generate_mock_descriptors(smiles)

        mol = self._parse_molecule(smiles)

        if mol is None:
            raise ValueError(f"Invalid SMILES string: {smiles}")

        try:
            descriptors = {}

            # Basic Lipinski properties
            descriptors['molecular_weight'] = float(Descriptors.MolWt(mol))
            descriptors['logp'] = float(Descriptors.MolLogP(mol))
            descriptors['hbd'] = float(Lipinski.NumHDonors(mol))
            descriptors['hba'] = float(Lipinski.NumHAcceptors(mol))
            descriptors['tpsa'] = float(CalcTPSA(mol))

            # Additional descriptors
            descriptors['rotatable_bonds'] = float(Lipinski.NumRotatableBonds(mol))
            descriptors['aromatic_rings'] = float(Lipinski.NumAromaticRings(mol))
            descriptors['heavy_atoms'] = float(mol.GetNumHeavyAtoms())
            descriptors['ring_count'] = float(Descriptors.RingCount(mol))

            # Stereochemistry
            descriptors['num_stereocenters'] = float(len(Chem.FindMolChiralCenters(mol, includeUnspecified=False)))

            # Drug-likeness score
            descriptors['qed'] = float(QED.qed(mol))

            # Fraction sp3 carbons
            num_atoms = mol.GetNumAtoms()
            if num_atoms > 0:
                num_sp3 = sum(1 for atom in mol.GetAtoms() if atom.GetHybridization() == Chem.HybridizationType.SP3)
                descriptors['fraction_sp3'] = num_sp3 / num_atoms
            else:
                descriptors['fraction_sp3'] = 0.0

            # Normalize properties if requested
            if self.normalize_properties:
                descriptors = self._normalize_properties(descriptors)

            logger.debug(
                f"Calculated molecular descriptors",
                smiles_length=len(smiles),
                num_descriptors=len(descriptors)
            )

            return descriptors

        except Exception as e:
            logger.error(f"Failed to calculate descriptors for {smiles}: {e}")
            raise RuntimeError(f"Descriptor calculation failed: {e}")

    def _normalize_properties(self, descriptors: Dict[str, float]) -> Dict[str, float]:
        """
        Normalize property values to [0, 1] range

        Args:
            descriptors: Dictionary of property values

        Returns:
            Dictionary with normalized values
        """
        normalized = {}

        for prop, value in descriptors.items():
            if prop in self.property_ranges:
                min_val, max_val = self.property_ranges[prop]

                # Clip to range and normalize
                clipped_value = max(min_val, min(max_val, value))
                normalized_value = (clipped_value - min_val) / (max_val - min_val)

                # Ensure value is in [0, 1]
                normalized[prop] = max(0.0, min(1.0, normalized_value))
            else:
                normalized[prop] = value

        return normalized

    def encode_combined(self, smiles: str) -> np.ndarray:
        """
        Generate combined fingerprint and descriptor vector

        Args:
            smiles: SMILES string

        Returns:
            Combined vector (fingerprint + normalized descriptors)
        """
        # Get fingerprint
        fingerprint = self.encode_morgan_fingerprint(smiles)

        # Get descriptors
        descriptors = self.encode_descriptors(smiles)

        # Convert descriptors to array (in same order every time)
        descriptor_keys = sorted(descriptors.keys())
        descriptor_values = np.array([descriptors[key] for key in descriptor_keys])

        # Concatenate
        combined = np.concatenate([fingerprint, descriptor_values])

        logger.debug(
            f"Generated combined encoding",
            fingerprint_size=len(fingerprint),
            descriptor_size=len(descriptor_values),
            total_size=len(combined)
        )

        return combined

    def is_drug_like(self, smiles: str) -> bool:
        """
        Check if molecule passes Lipinski's Rule of Five

        Lipinski's Rule of Five:
        - Molecular weight < 500 Da
        - LogP < 5
        - Hydrogen bond donors ≤ 5
        - Hydrogen bond acceptors ≤ 10

        Args:
            smiles: SMILES string

        Returns:
            True if drug-like, False otherwise
        """
        try:
            descriptors = self.encode_descriptors(smiles)

            rules = [
                descriptors['molecular_weight'] <= 500,
                descriptors['logp'] <= 5,
                descriptors['hbd'] <= 5,
                descriptors['hba'] <= 10,
            ]

            is_drug_like = all(rules)

            logger.debug(
                f"Drug-likeness check",
                molecular_weight=descriptors['molecular_weight'],
                logp=descriptors['logp'],
                hbd=descriptors['hbd'],
                hba=descriptors['hba'],
                is_drug_like=is_drug_like
            )

            return is_drug_like

        except Exception as e:
            logger.warning(f"Could not check drug-likeness for {smiles}: {e}")
            return False

    def calculate_similarity(self, smiles1: str, smiles2: str) -> float:
        """
        Calculate Tanimoto similarity between two molecules

        Args:
            smiles1: First SMILES string
            smiles2: Second SMILES string

        Returns:
            Tanimoto similarity coefficient (0-1)
        """
        try:
            # Get fingerprints
            fp1 = self.encode_morgan_fingerprint(smiles1)
            fp2 = self.encode_morgan_fingerprint(smiles2)

            # Calculate Tanimoto coefficient
            intersection = np.sum(fp1 * fp2)
            union = np.sum(fp1) + np.sum(fp2) - intersection

            if union == 0:
                return 0.0

            similarity = intersection / union

            logger.debug(
                f"Calculated molecular similarity",
                similarity=f"{similarity".3f"}",
                intersection=intersection,
                union=union
            )

            return float(similarity)

        except Exception as e:
            logger.error(f"Failed to calculate similarity: {e}")
            return 0.0

    def get_fingerprint_size(self) -> int:
        """Get the size of generated fingerprints"""
        return self.fingerprint_size

    def get_property_names(self) -> List[str]:
        """Get list of calculated property names"""
        return list(self.property_ranges.keys())

    def _generate_mock_fingerprint(self, smiles: str) -> np.ndarray:
        """
        Generate mock fingerprint for demo purposes

        Args:
            smiles: SMILES string

        Returns:
            Mock fingerprint vector
        """
        import hashlib

        # Create deterministic mock fingerprint based on SMILES hash
        smiles_hash = int(hashlib.md5(smiles.encode()).hexdigest()[:8], 16)

        # Generate pseudo-random fingerprint
        np.random.seed(smiles_hash)
        fingerprint = np.random.randint(0, 2, self.fingerprint_size).astype(np.float32)

        logger.debug(
            f"Generated mock drug fingerprint",
            smiles_length=len(smiles),
            fingerprint_size=fingerprint.shape[0],
            active_bits=int(fingerprint.sum()),
            demo_mode=True
        )

        return fingerprint

    def _generate_mock_descriptors(self, smiles: str) -> Dict[str, float]:
        """
        Generate mock molecular descriptors for demo purposes

        Args:
            smiles: SMILES string

        Returns:
            Dictionary of mock molecular properties
        """
        import hashlib

        # Create deterministic mock properties based on SMILES hash
        smiles_hash = int(hashlib.md5(smiles.encode()).hexdigest()[:8], 16)

        # Generate pseudo-random but realistic properties
        np.random.seed(smiles_hash)

        descriptors = {
            'molecular_weight': 150.0 + np.random.rand() * 400,  # 150-550 Da
            'logp': -2.0 + np.random.rand() * 7,  # -2 to 5
            'hbd': int(np.random.rand() * 6),  # 0-5
            'hba': int(np.random.rand() * 12),  # 0-11
            'tpsa': 20.0 + np.random.rand() * 150,  # 20-170 Å²
            'rotatable_bonds': int(np.random.rand() * 10),  # 0-9
            'aromatic_rings': int(np.random.rand() * 4),  # 0-3
            'num_stereocenters': int(np.random.rand() * 3),  # 0-2
            'fraction_sp3': 0.1 + np.random.rand() * 0.8,  # 0.1-0.9
            'qed': 0.2 + np.random.rand() * 0.7  # 0.2-0.9
        }

        logger.debug(
            f"Generated mock molecular descriptors",
            smiles_length=len(smiles),
            num_descriptors=len(descriptors),
            demo_mode=True
        )

        return descriptors

    def __repr__(self) -> str:
        return (
            f"DrugEncoder("
            f"fingerprint_size={self.fingerprint_size}, "
            f"fingerprint_radius={self.fingerprint_radius}"
            f")"
        )
