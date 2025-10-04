"""
UniProt API Client

Fetches protein sequence and annotation data from UniProt database.
UniProt is a comprehensive protein sequence and annotation database.

API Documentation: https://www.uniprot.org/help/api
"""
import asyncio
import re
import time
from typing import Dict, List, Optional, Any
import structlog
import httpx

logger = structlog.get_logger()

from app.config import settings


class UniProtClient:
    """
    Client for UniProt database API

    Args:
        base_url: UniProt API base URL
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts
        retry_delay: Delay between retries in seconds
    """

    def __init__(
        self,
        base_url: str = settings.UNIPROT_API_URL,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        logger.info("UniProt client initialized", base_url=base_url)

    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make HTTP request to UniProt API with retry logic

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            JSON response data
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    logger.debug(f"Making UniProt request", url=url, attempt=attempt + 1)

                    response = await client.get(url, params=params)

                    if response.status_code == 200:
                        return response.json()
                    elif response.status_code == 404:
                        logger.warning(f"UniProt resource not found", url=url)
                        return {"error": "Not found"}
                    else:
                        logger.warning(
                            f"UniProt API error",
                            status_code=response.status_code,
                            url=url
                        )

            except httpx.TimeoutException:
                logger.warning(f"UniProt request timeout", url=url, attempt=attempt + 1)
            except httpx.RequestError as e:
                logger.warning(f"UniProt request error", error=str(e), attempt=attempt + 1)

            # Wait before retry
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay * (2 ** attempt))

        raise RuntimeError(f"UniProt API request failed after {self.max_retries} attempts")

    async def fetch_protein_sequence(self, gene_symbol: str, organism: str = "human") -> Optional[str]:
        """
        Fetch protein sequence by gene symbol

        Args:
            gene_symbol: Gene symbol (e.g., "BRCA1", "TP53")
            organism: Organism name (default: "human")

        Returns:
            Amino acid sequence or None if not found
        """
        try:
            logger.info(f"Fetching protein sequence", gene_symbol=gene_symbol, organism=organism)

            # Map organism names to UniProt taxonomy IDs
            organism_map = {
                "human": "9606",
                "mouse": "10090",
                "rat": "10116",
                "zebrafish": "7955",
                "fruitfly": "7227",
                "yeast": "559292",
                "ecoli": "562"
            }

            taxonomy_id = organism_map.get(organism.lower())
            if not taxonomy_id:
                logger.warning(f"Unknown organism: {organism}")
                taxonomy_id = "9606"  # Default to human

            # Search for protein by gene name
            search_endpoint = "uniprotkb/search"
            search_params = {
                "query": f"gene:{gene_symbol} AND organism_id:{taxonomy_id}",
                "format": "json",
                "size": 1,  # Get best match
                "fields": "accession,gene_names,organism_name,sequence"
            }

            search_response = await self._make_request(search_endpoint, search_params)

            results = search_response.get("results", [])

            if not results:
                logger.warning(f"No protein found for gene {gene_symbol}")
                return None

            # Get the primary accession ID
            accession = results[0].get("primaryAccession") or results[0].get("accession", [{}])[0].get("value")

            if not accession:
                logger.warning(f"No accession ID found for gene {gene_symbol}")
                return None

            # Fetch full sequence in FASTA format
            fasta_endpoint = f"uniprotkb/{accession}.fasta"
            fasta_response = await self._make_request(fasta_endpoint)

            if "error" in fasta_response:
                logger.warning(f"FASTA not found for {accession}")
                return None

            # Parse FASTA sequence
            sequence = self._parse_fasta(fasta_response)

            logger.info(
                f"Retrieved protein sequence",
                gene_symbol=gene_symbol,
                accession=accession,
                sequence_length=len(sequence) if sequence else 0
            )

            return sequence

        except Exception as e:
            logger.error(f"Failed to fetch protein sequence for {gene_symbol}: {e}")
            return None

    def _parse_fasta(self, fasta_text: str) -> str:
        """
        Parse protein sequence from FASTA format

        Args:
            fasta_text: FASTA formatted text

        Returns:
            Amino acid sequence (uppercase, no whitespace)
        """
        lines = fasta_text.strip().split('\n')

        # Remove header lines (starting with '>')
        sequence_lines = [line.strip() for line in lines if not line.startswith('>')]

        # Join and clean sequence
        sequence = ''.join(sequence_lines).upper()

        # Remove any non-amino acid characters
        sequence = re.sub(r'[^A-Z]', '', sequence)

        return sequence

    async def fetch_protein_info(self, uniprot_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch comprehensive protein information

        Args:
            uniprot_id: UniProt accession ID

        Returns:
            Protein information dictionary or None if not found
        """
        try:
            logger.info(f"Fetching protein information", uniprot_id=uniprot_id)

            # Fetch protein data
            endpoint = f"uniprotkb/{uniprot_id}.json"
            response_data = await self._make_request(endpoint)

            if "error" in response_data:
                return None

            # Extract relevant information
            protein_data = response_data.get("results", [{}])[0]

            if not protein_data:
                return None

            # Build comprehensive protein info
            protein_info = {
                "uniprot_id": protein_data.get("primaryAccession") or uniprot_id,
                "name": protein_data.get("proteinDescription", {}).get("recommendedName", {}).get("fullName", {}).get("value"),
                "gene_name": None,
                "organism": protein_data.get("organism", {}).get("scientificName"),
                "sequence": self._extract_sequence(protein_data),
                "sequence_length": len(self._extract_sequence(protein_data)) if self._extract_sequence(protein_data) else 0,
                "molecular_weight": protein_data.get("proteinDescription", {}).get("molecularWeight"),
                "function": self._extract_function(protein_data),
                "subcellular_location": self._extract_subcellular_location(protein_data),
                "tissue_specificity": self._extract_tissue_specificity(protein_data),
                "pathway": self._extract_pathway(protein_data),
                "disease_associations": self._extract_disease_associations(protein_data),
                "drug_interactions": self._extract_drug_interactions(protein_data),
                "structure_available": self._check_structure_availability(protein_data),
                "go_terms": self._extract_go_terms(protein_data),
                "interpro_domains": self._extract_interpro_domains(protein_data),
                "post_translational_modifications": self._extract_ptms(protein_data),
                "expression_data": self._extract_expression_data(protein_data),
                "references": self._extract_references(protein_data)
            }

            # Extract gene name
            gene_names = protein_data.get("genes", [])
            if gene_names:
                protein_info["gene_name"] = gene_names[0].get("geneName", {}).get("value")

            logger.info(
                f"Retrieved protein information",
                uniprot_id=uniprot_id,
                name=protein_info.get("name")
            )

            return protein_info

        except Exception as e:
            logger.error(f"Failed to fetch protein info for {uniprot_id}: {e}")
            return None

    def _extract_sequence(self, protein_data: Dict) -> Optional[str]:
        """Extract sequence from protein data"""
        sequence = protein_data.get("sequence", {}).get("value")
        return sequence.upper() if sequence else None

    def _extract_function(self, protein_data: Dict) -> Optional[str]:
        """Extract function description"""
        comments = protein_data.get("comments", [])
        for comment in comments:
            if comment.get("commentType") == "FUNCTION":
                texts = comment.get("texts", [])
                if texts:
                    return texts[0].get("value", "")
        return None

    def _extract_subcellular_location(self, protein_data: Dict) -> Optional[str]:
        """Extract subcellular location"""
        comments = protein_data.get("comments", [])
        for comment in comments:
            if comment.get("commentType") == "SUBCELLULAR LOCATION":
                texts = comment.get("texts", [])
                if texts:
                    return texts[0].get("value", "")
        return None

    def _extract_tissue_specificity(self, protein_data: Dict) -> Optional[str]:
        """Extract tissue specificity"""
        comments = protein_data.get("comments", [])
        for comment in comments:
            if comment.get("commentType") == "TISSUE SPECIFICITY":
                texts = comment.get("texts", [])
                if texts:
                    return texts[0].get("value", "")
        return None

    def _extract_pathway(self, protein_data: Dict) -> Optional[str]:
        """Extract pathway information"""
        comments = protein_data.get("comments", [])
        for comment in comments:
            if comment.get("commentType") == "PATHWAY":
                texts = comment.get("texts", [])
                if texts:
                    return texts[0].get("value", "")
        return None

    def _extract_disease_associations(self, protein_data: Dict) -> List[str]:
        """Extract disease associations"""
        diseases = []
        comments = protein_data.get("comments", [])

        for comment in comments:
            if comment.get("commentType") == "DISEASE":
                disease_name = comment.get("disease", {}).get("diseaseName")
                if disease_name:
                    diseases.append(disease_name)

        return diseases

    def _extract_drug_interactions(self, protein_data: Dict) -> List[str]:
        """Extract drug interaction information"""
        # TODO: Extract from comments or cross-reference with ChEMBL
        return []

    def _check_structure_availability(self, protein_data: Dict) -> bool:
        """Check if 3D structure is available"""
        # Look for PDB cross-references
        xrefs = protein_data.get("uniProtKBCrossReferences", [])
        for xref in xrefs:
            if xref.get("database") == "PDB":
                return True
        return False

    def _extract_go_terms(self, protein_data: Dict) -> Dict[str, List[str]]:
        """Extract Gene Ontology terms"""
        go_terms = {"molecular_function": [], "biological_process": [], "cellular_component": []}

        # Extract from annotations
        annotations = protein_data.get("annotations", [])

        for annotation in annotations:
            if annotation.get("annotationType") == "go":
                go_id = annotation.get("goId")
                go_name = annotation.get("goName")
                go_aspect = annotation.get("goAspect", "").lower()

                if go_aspect in go_terms and go_id and go_name:
                    go_terms[go_aspect].append(f"{go_id}: {go_name}")

        return go_terms

    def _extract_interpro_domains(self, protein_data: Dict) -> List[str]:
        """Extract InterPro domain information"""
        domains = []
        xrefs = protein_data.get("uniProtKBCrossReferences", [])

        for xref in xrefs:
            if xref.get("database") == "InterPro":
                domain_id = xref.get("id")
                domain_name = xref.get("properties", [{}])[0].get("value")
                if domain_id and domain_name:
                    domains.append(f"{domain_id}: {domain_name}")

        return domains

    def _extract_ptms(self, protein_data: Dict) -> List[str]:
        """Extract post-translational modifications"""
        ptms = []
        features = protein_data.get("features", [])

        for feature in features:
            if feature.get("type") == "MODIFIED RESIDUE":
                description = feature.get("description", "")
                if description:
                    ptms.append(description)

        return ptms

    def _extract_expression_data(self, protein_data: Dict) -> Optional[Dict]:
        """Extract expression data"""
        # TODO: Extract from comments or external sources
        return None

    def _extract_references(self, protein_data: Dict) -> List[str]:
        """Extract literature references"""
        references = []
        xrefs = protein_data.get("uniProtKBCrossReferences", [])

        for xref in xrefs:
            if xref.get("database") == "PubMed":
                pmid = xref.get("id")
                if pmid:
                    references.append(f"PMID:{pmid}")

        return references

    async def search_proteins_by_disease(self, disease_name: str) -> List[Dict[str, Any]]:
        """
        Search for proteins associated with a disease

        Args:
            disease_name: Name of the disease

        Returns:
            List of protein dictionaries
        """
        try:
            logger.info(f"Searching proteins by disease", disease_name=disease_name)

            # Search for proteins associated with disease
            search_endpoint = "uniprotkb/search"
            search_params = {
                "query": f"disease:{disease_name}",
                "format": "json",
                "size": 10,  # Limit to top 10
                "fields": "accession,gene_names,protein_name,organism_name"
            }

            response_data = await self._make_request(search_endpoint, search_params)

            proteins = []
            results = response_data.get("results", [])

            for result in results:
                protein = {
                    "uniprot_id": result.get("primaryAccession") or result.get("accession", [{}])[0].get("value"),
                    "name": result.get("proteinName"),
                    "gene_name": None,
                    "organism": result.get("organismName")
                }

                # Extract gene name
                gene_names = result.get("geneNames", [])
                if gene_names:
                    protein["gene_name"] = gene_names[0].get("value")

                if protein["uniprot_id"]:
                    proteins.append(protein)

            logger.info(f"Found {len(proteins)} proteins associated with disease")
            return proteins

        except Exception as e:
            logger.error(f"Disease protein search failed: {e}")
            return []


# Global client instance
uniprot_client = UniProtClient()


# Convenience functions
async def fetch_protein_sequence(gene_symbol: str, organism: str = "human") -> Optional[str]:
    """Fetch protein sequence by gene symbol"""
    return await uniprot_client.fetch_protein_sequence(gene_symbol, organism)


async def fetch_protein_info(uniprot_id: str) -> Optional[Dict[str, Any]]:
    """Fetch comprehensive protein information"""
    return await uniprot_client.fetch_protein_info(uniprot_id)


async def search_proteins_by_disease(disease_name: str) -> List[Dict[str, Any]]:
    """Search proteins associated with a disease"""
    return await uniprot_client.search_proteins_by_disease(disease_name)
