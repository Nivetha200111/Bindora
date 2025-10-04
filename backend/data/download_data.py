"""
Data Download Script

Downloads and prepares drug and protein data for the Bindora platform.
This script fetches data from ChEMBL and UniProt to populate the database.

Usage:
    python data/download_data.py [--drugs-only] [--proteins-only] [--limit N]

Options:
    --drugs-only: Only download drug data
    --proteins-only: Only download protein data
    --limit N: Limit number of records (default: 1000 for drugs, 10000 for proteins)
"""
import asyncio
import argparse
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import structlog

logger = structlog.get_logger()

from app.utils.chembl_client import fetch_approved_drugs
from app.utils.uniprot_client import search_proteins_by_disease, fetch_protein_sequence


class DataDownloader:
    """
    Downloads and processes data from external sources

    Args:
        data_dir: Directory to save downloaded data
        limit_drugs: Maximum drugs to download
        limit_proteins: Maximum proteins to download
    """

    def __init__(
        self,
        data_dir: str = "./data",
        limit_drugs: int = 1000,
        limit_proteins: int = 10000
    ):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.limit_drugs = limit_drugs
        self.limit_proteins = limit_proteins

        logger.info(
            "Data downloader initialized",
            data_dir=str(self.data_dir),
            limit_drugs=limit_drugs,
            limit_proteins=limit_proteins
        )

    async def download_all(self):
        """Download all data (drugs and proteins)"""
        logger.info("Starting complete data download")

        # Download drugs
        await self.download_drugs()

        # Download proteins
        await self.download_proteins()

        logger.info("Complete data download finished")

    async def download_drugs(self):
        """Download approved drugs from ChEMBL"""
        logger.info(f"Downloading {self.limit_drugs} approved drugs from ChEMBL")

        try:
            drugs = await fetch_approved_drugs(limit=self.limit_drugs)

            if not drugs:
                logger.warning("No drugs downloaded from ChEMBL")
                return

            # Save to CSV
            drugs_file = self.data_dir / "drugs.csv"
            await self._save_drugs_csv(drugs, drugs_file)

            # Save to JSON for easier loading
            drugs_json_file = self.data_dir / "drugs.json"
            await self._save_drugs_json(drugs, drugs_json_file)

            logger.info(f"Saved {len(drugs)} drugs to {drugs_file}")

        except Exception as e:
            logger.error(f"Drug download failed: {e}")
            raise

    async def _save_drugs_csv(self, drugs: List[Dict], filepath: Path):
        """Save drugs to CSV file"""
        try:
            import pandas as pd

            # Convert to DataFrame
            df = pd.DataFrame(drugs)

            # Select and reorder columns
            columns = [
                "chembl_id", "name", "smiles", "molecular_weight",
                "clinical_phase", "is_drug_like"
            ]

            # Filter to existing columns
            available_columns = [col for col in columns if col in df.columns]
            df = df[available_columns]

            # Save to CSV
            df.to_csv(filepath, index=False)

        except ImportError:
            logger.warning("Pandas not available, skipping CSV export")
        except Exception as e:
            logger.error(f"Failed to save drugs CSV: {e}")

    async def _save_drugs_json(self, drugs: List[Dict], filepath: Path):
        """Save drugs to JSON file"""
        try:
            # Convert to JSON-serializable format
            json_data = {
                "metadata": {
                    "source": "ChEMBL",
                    "total_drugs": len(drugs),
                    "downloaded_at": str(pd.Timestamp.now()) if 'pd' in globals() else None
                },
                "drugs": drugs
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Failed to save drugs JSON: {e}")

    async def download_proteins(self):
        """Download protein targets from UniProt"""
        logger.info(f"Downloading {self.limit_proteins} protein targets from UniProt")

        try:
            proteins = []

            # Common disease-related genes to fetch
            disease_genes = [
                "BRCA1", "BRCA2", "TP53", "EGFR", "ESR1", "PIK3CA",
                "CDKN2A", "APC", "MLH1", "VHL", "RB1", "PTEN",
                "CDH1", "STK11", "SMAD4", "BMPR1A", "MEN1", "RET",
                "NF1", "NF2", "TSC1", "TSC2", "VHL", "WT1"
            ]

            # Fetch proteins for each gene
            for gene in disease_genes[:20]:  # Limit to first 20
                try:
                    sequence = await fetch_protein_sequence(gene)
                    if sequence:
                        protein = {
                            "gene_name": gene,
                            "sequence": sequence,
                            "sequence_length": len(sequence),
                            "organism": "human"
                        }
                        proteins.append(protein)

                        if len(proteins) >= self.limit_proteins:
                            break

                except Exception as e:
                    logger.warning(f"Failed to fetch protein for gene {gene}: {e}")
                    continue

            # Also try to get some disease-associated proteins
            try:
                disease_proteins = await search_proteins_by_disease("cancer")
                for protein in disease_proteins[:10]:  # Add up to 10 more
                    if len(proteins) >= self.limit_proteins:
                        break

                    try:
                        sequence = await fetch_protein_sequence(protein.get("gene_name", ""))
                        if sequence:
                            protein_data = {
                                "gene_name": protein.get("gene_name"),
                                "uniprot_id": protein.get("uniprot_id"),
                                "sequence": sequence,
                                "sequence_length": len(sequence),
                                "organism": protein.get("organism", "human")
                            }
                            proteins.append(protein_data)
                    except Exception:
                        continue

            except Exception as e:
                logger.warning(f"Failed to get disease proteins: {e}")

            if not proteins:
                logger.warning("No proteins downloaded from UniProt")
                return

            # Save to CSV
            proteins_file = self.data_dir / "proteins.csv"
            await self._save_proteins_csv(proteins, proteins_file)

            # Save to JSON
            proteins_json_file = self.data_dir / "proteins.json"
            await self._save_proteins_json(proteins, proteins_json_file)

            logger.info(f"Saved {len(proteins)} proteins to {proteins_file}")

        except Exception as e:
            logger.error(f"Protein download failed: {e}")
            raise

    async def _save_proteins_csv(self, proteins: List[Dict], filepath: Path):
        """Save proteins to CSV file"""
        try:
            import pandas as pd

            df = pd.DataFrame(proteins)

            # Select columns
            columns = ["gene_name", "uniprot_id", "sequence", "sequence_length", "organism"]
            available_columns = [col for col in columns if col in df.columns]
            df = df[available_columns]

            df.to_csv(filepath, index=False)

        except ImportError:
            logger.warning("Pandas not available, skipping CSV export")
        except Exception as e:
            logger.error(f"Failed to save proteins CSV: {e}")

    async def _save_proteins_json(self, proteins: List[Dict], filepath: Path):
        """Save proteins to JSON file"""
        try:
            json_data = {
                "metadata": {
                    "source": "UniProt",
                    "total_proteins": len(proteins),
                    "downloaded_at": str(pd.Timestamp.now()) if 'pd' in globals() else None
                },
                "proteins": proteins
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Failed to save proteins JSON: {e}")

    async def download_sample_data(self):
        """Download sample data for testing"""
        logger.info("Downloading sample data")

        # Sample drugs (would normally come from ChEMBL)
        sample_drugs = [
            {
                "chembl_id": "CHEMBL25",
                "name": "Aspirin",
                "smiles": "CC(=O)Oc1ccccc1C(=O)O",
                "molecular_weight": 180.16,
                "clinical_phase": 4,
                "is_drug_like": True
            },
            {
                "chembl_id": "CHEMBL192",
                "name": "Ibuprofen",
                "smiles": "CC(C)Cc1ccc(cc1)C(C)C(=O)O",
                "molecular_weight": 206.28,
                "clinical_phase": 4,
                "is_drug_like": True
            },
            {
                "chembl_id": "CHEMBL502",
                "name": "Paracetamol",
                "smiles": "CC(=O)Nc1ccc(O)cc1",
                "molecular_weight": 151.16,
                "clinical_phase": 4,
                "is_drug_like": True
            }
        ]

        # Sample proteins (would normally come from UniProt)
        sample_proteins = [
            {
                "gene_name": "BRCA1",
                "sequence": "MDLSALRVEEVQNVINAMQKILECPICLELIKEPVSTKCDHIFCKFCMLKLLNQKKGPSQCPLCKNDITKRSLQESTRFSQLVEELLKIICAFQLDTGLEYANSYNFAKKENNSPEHLKDEVSIIQSMGYRNRAKRLLQSEPENPSLQETSLSVQLSNLGTVRTLRTKQRIQPQKTSVYIELGSDSSEDTVNKATYCSVGDQELLQITPQGTRDEISLDSAKKAACEFSETDVTNTEHHQPSNNDLNTTEKRAAERHPEKYQGSSVSNLHVEPCGTNTHASSLQHENSSLLLTKDRMNVEKAEFCNKSKQPGLARSQHNRWAGSKETCNDRRTPSTEKKVDLNADPLCERKEWNKQKLPCSENPRDTEDVPWITLNSSIQKVNEWFSRSDELLGSDDSHDGESESNAKVADVLDVLNEVDEYSGSSEKIDLLASDPHEALICKSERVHSKSVESNIEDKIFGKTYRKKASLPNLSHVTENLIIGAFVTEPQIIQERPLTNKLKRKRRPTSGLHPEDFIKKADLAVQKTPEMINQGTNQTEQNGQVMNITNSGHENKTKGDSIQNEKNPNPIESLEKESAFKTKAEPISSSISNMELELNIHNSKAPKKNRLRRKSSTRHIHALELVVSRNLSPPNCTELQIDSCSSSEEIKKKKYNQMPVRHSRNLQLMEGKEPATGAKKSNKPNEQTSKRHDSDTFPELKLTNAPGSFTKCSNTSELKEFVNPSLPREEKEEKLETVKVSNNAEDPKDLMLSGERVLQTERSVESSSISLVPGTDYGTQESISLLEVSTLGKAKTEPNKCVSQCAAFENPKGLIHGCSKDNRNDTEGFKYPLGHEVNHSRETSIEMEESELDAQYLQNTFKVSKRQSFAPFSNPGNAEEECATFSAHSGSLKKQSPKVTFECEQKEENQGKNESNIKPVQTVNITAGFPVVGQKDKPVDNAKCSIKGGSRFCLSSQFRGNETGLITPNKHGLLQNPYRIPPLFPIKSFVKTKCKKNLLEENFEEHSMSPEREMGNENIPSTVSTISRNNIRENVFKEASSSNINEVGSSTNEVGSSINEIGSSDENIQAELGRNRGPKLNAMLRLGVLQPEVYKQSLPGSNCKHPEIKKQEYEEVVQTVNTDFSPYLISDNLEQPMGSSHASQVCSETPDDLLDDGEIGEDVDSDRMLDNRATPPKIPKACCVPTELSAISMLYLDENEKVVLKNYQDMVVEGCGCR",
                "sequence_length": 1863,
                "organism": "human"
            }
        ]

        # Save sample data
        sample_file = self.data_dir / "sample_data.json"

        sample_data = {
            "metadata": {
                "description": "Sample data for testing and development",
                "drugs_count": len(sample_drugs),
                "proteins_count": len(sample_proteins)
            },
            "drugs": sample_drugs,
            "proteins": sample_proteins
        }

        with open(sample_file, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved sample data to {sample_file}")


async def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Download data for Bindora platform")
    parser.add_argument("--drugs-only", action="store_true", help="Only download drug data")
    parser.add_argument("--proteins-only", action="store_true", help="Only download protein data")
    parser.add_argument("--limit-drugs", type=int, default=1000, help="Limit number of drugs")
    parser.add_argument("--limit-proteins", type=int, default=10000, help="Limit number of proteins")
    parser.add_argument("--sample-only", action="store_true", help="Only create sample data")

    args = parser.parse_args()

    print("=" * 60)
    print("Bindora - Data Download Script")
    print("=" * 60)

    downloader = DataDownloader(
        limit_drugs=args.limit_drugs,
        limit_proteins=args.limit_proteins
    )

    try:
        if args.sample_only:
            await downloader.download_sample_data()
        elif args.drugs_only:
            await downloader.download_drugs()
        elif args.proteins_only:
            await downloader.download_proteins()
        else:
            await downloader.download_all()

        print("\n" + "=" * 60)
        print("✅ Data download complete!")
        print("=" * 60)

        # Show downloaded files
        data_files = list(Path("./data").glob("*.csv")) + list(Path("./data").glob("*.json"))
        if data_files:
            print("\n📁 Downloaded files:")
            for file in sorted(data_files):
                size_mb = file.stat().st_size / (1024 * 1024)
                print(f"  • {file.name} ({size_mb:.".1f"MB)")

        print("
🚀 Next steps:"        print("1. Review the downloaded data files")
        print("2. Start the API server: uvicorn app.main:app --reload")
        print("3. Test the API at http://localhost:8000/docs")

    except KeyboardInterrupt:
        print("\n⚠️  Download interrupted by user")
    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
