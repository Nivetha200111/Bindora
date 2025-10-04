"""
Embedding Pre-computation Script

Pre-computes and caches embeddings for drugs and proteins to speed up predictions.
This script can take a long time to run but significantly improves API performance.

Usage:
    python data/process_embeddings.py [--drugs-only] [--proteins-only] [--batch-size N]

Options:
    --drugs-only: Only process drug embeddings
    --proteins-only: Only process protein embeddings
    --batch-size N: Batch size for processing (default: 32)
"""
import asyncio
import argparse
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
import structlog
import numpy as np

logger = structlog.get_logger()

from app.models.protein_encoder import ProteinEncoder
from app.models.drug_encoder import DrugEncoder
from app.utils.cache import embedding_cache


class EmbeddingProcessor:
    """
    Processes and caches embeddings for drugs and proteins

    Args:
        protein_encoder: Initialized ProteinEncoder
        drug_encoder: Initialized DrugEncoder
        batch_size: Batch size for processing
    """

    def __init__(
        self,
        protein_encoder: ProteinEncoder,
        drug_encoder: DrugEncoder,
        batch_size: int = 32
    ):
        self.protein_encoder = protein_encoder
        self.drug_encoder = drug_encoder
        self.batch_size = batch_size

        logger.info(
            "Embedding processor initialized",
            batch_size=batch_size,
            protein_model=protein_encoder.model_name,
            drug_fp_size=drug_encoder.get_fingerprint_size()
        )

    async def process_all_embeddings(self, data_dir: str = "./data"):
        """
        Process embeddings for all available data

        Args:
            data_dir: Directory containing drug and protein data
        """
        logger.info("Starting complete embedding processing")

        data_path = Path(data_dir)

        # Process protein embeddings
        await self.process_protein_embeddings(data_path)

        # Process drug embeddings
        await self.process_drug_embeddings(data_path)

        logger.info("Complete embedding processing finished")

    async def process_protein_embeddings(self, data_path: Path):
        """Process protein embeddings"""
        logger.info("Processing protein embeddings")

        # Look for protein data files
        protein_files = [
            data_path / "proteins.json",
            data_path / "proteins.csv"
        ]

        proteins = []

        for file_path in protein_files:
            if file_path.exists():
                try:
                    if file_path.suffix == ".json":
                        proteins = await self._load_proteins_json(file_path)
                    elif file_path.suffix == ".csv":
                        proteins = await self._load_proteins_csv(file_path)

                    if proteins:
                        logger.info(f"Loaded {len(proteins)} proteins from {file_path}")
                        break

                except Exception as e:
                    logger.warning(f"Failed to load proteins from {file_path}: {e}")

        if not proteins:
            logger.warning("No protein data found")
            return

        # Process embeddings in batches
        await self._process_protein_embeddings_batch(proteins)

    async def _load_proteins_json(self, file_path: Path) -> List[Dict]:
        """Load proteins from JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return data.get("proteins", [])

    async def _load_proteins_csv(self, file_path: Path) -> List[Dict]:
        """Load proteins from CSV file"""
        try:
            import pandas as pd

            df = pd.read_csv(file_path)
            return df.to_dict('records')

        except ImportError:
            logger.warning("Pandas not available, skipping CSV loading")
            return []

    async def _process_protein_embeddings_batch(self, proteins: List[Dict]):
        """Process protein embeddings in batches"""
        total_proteins = len(proteins)
        processed = 0
        cached = 0

        logger.info(f"Processing {total_proteins} protein embeddings in batches of {self.batch_size}")

        for i in range(0, total_proteins, self.batch_size):
            batch = proteins[i:i + self.batch_size]
            batch_sequences = [p.get("sequence", "") for p in batch]

            # Filter out empty sequences
            valid_batch = [(j, seq) for j, seq in enumerate(batch_sequences) if seq]

            if not valid_batch:
                continue

            try:
                # Check cache first
                uncached_indices = []
                uncached_sequences = []

                for idx, sequence in valid_batch:
                    if not await embedding_cache.get_protein_embedding(sequence):
                        uncached_indices.append(idx)
                        uncached_sequences.append(sequence)

                # Process uncached sequences
                if uncached_sequences:
                    start_time = time.time()

                    # Encode proteins
                    embeddings = self.protein_encoder.batch_encode(uncached_sequences)

                    # Cache embeddings
                    for (orig_idx, sequence), embedding in zip(
                        [valid_batch[i] for i in uncached_indices],
                        embeddings
                    ):
                        await embedding_cache.set_protein_embedding(sequence, embedding)

                    process_time = time.time() - start_time

                    logger.info(
                        f"Processed protein embedding batch",
                        batch_start=i,
                        batch_size=len(uncached_sequences),
                        process_time=f"{process_time".2f"}s"
                    )

                processed += len(valid_batch)
                cached += len(valid_batch) - len(uncached_sequences)

                # Progress logging
                if processed % 100 == 0:
                    logger.info(
                        f"Protein embedding progress",
                        processed=processed,
                        total=total_proteins,
                        cached=cached
                    )

        logger.info(
            f"Protein embedding processing complete",
            total_processed=processed,
            total_cached=cached
        )

    async def process_drug_embeddings(self, data_path: Path):
        """Process drug embeddings"""
        logger.info("Processing drug embeddings")

        # Look for drug data files
        drug_files = [
            data_path / "drugs.json",
            data_path / "drugs.csv"
        ]

        drugs = []

        for file_path in drug_files:
            if file_path.exists():
                try:
                    if file_path.suffix == ".json":
                        drugs = await self._load_drugs_json(file_path)
                    elif file_path.suffix == ".csv":
                        drugs = await self._load_drugs_csv(file_path)

                    if drugs:
                        logger.info(f"Loaded {len(drugs)} drugs from {file_path}")
                        break

                except Exception as e:
                    logger.warning(f"Failed to load drugs from {file_path}: {e}")

        if not drugs:
            logger.warning("No drug data found")
            return

        # Process embeddings in batches
        await self._process_drug_embeddings_batch(drugs)

    async def _load_drugs_json(self, file_path: Path) -> List[Dict]:
        """Load drugs from JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return data.get("drugs", [])

    async def _load_drugs_csv(self, file_path: Path) -> List[Dict]:
        """Load drugs from CSV file"""
        try:
            import pandas as pd

            df = pd.read_csv(file_path)
            return df.to_dict('records')

        except ImportError:
            logger.warning("Pandas not available, skipping CSV loading")
            return []

    async def _process_drug_embeddings_batch(self, drugs: List[Dict]):
        """Process drug embeddings in batches"""
        total_drugs = len(drugs)
        processed = 0
        cached = 0

        logger.info(f"Processing {total_drugs} drug embeddings in batches of {self.batch_size}")

        for i in range(0, total_drugs, self.batch_size):
            batch = drugs[i:i + self.batch_size]
            batch_smiles = [d.get("smiles", "") for d in batch]

            # Filter out empty SMILES
            valid_batch = [(j, smiles) for j, smiles in enumerate(batch_smiles) if smiles]

            if not valid_batch:
                continue

            try:
                # Check cache first
                uncached_indices = []
                uncached_smiles = []

                for idx, smiles in valid_batch:
                    if not await embedding_cache.get_drug_embedding(smiles):
                        uncached_indices.append(idx)
                        uncached_smiles.append(smiles)

                # Process uncached drugs
                if uncached_smiles:
                    start_time = time.time()

                    # Encode drugs (get fingerprints)
                    embeddings = []
                    for smiles in uncached_smiles:
                        try:
                            fp = self.drug_encoder.encode_morgan_fingerprint(smiles)
                            embeddings.append(fp)
                        except Exception as e:
                            logger.warning(f"Failed to encode drug {smiles}: {e}")
                            # Use zero vector as fallback
                            embeddings.append(np.zeros(self.drug_encoder.get_fingerprint_size()))

                    # Cache embeddings
                    for (orig_idx, smiles), embedding in zip(
                        [valid_batch[i] for i in uncached_indices],
                        embeddings
                    ):
                        await embedding_cache.set_drug_embedding(smiles, embedding)

                    process_time = time.time() - start_time

                    logger.info(
                        f"Processed drug embedding batch",
                        batch_start=i,
                        batch_size=len(uncached_smiles),
                        process_time=f"{process_time".2f"}s"
                    )

                processed += len(valid_batch)
                cached += len(valid_batch) - len(uncached_smiles)

                # Progress logging
                if processed % 100 == 0:
                    logger.info(
                        f"Drug embedding progress",
                        processed=processed,
                        total=total_drugs,
                        cached=cached
                    )

        logger.info(
            f"Drug embedding processing complete",
            total_processed=processed,
            total_cached=cached
        )

    async def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        # This would require Redis info, simplified for now
        return {
            "protein_embeddings_cached": "unknown",
            "drug_embeddings_cached": "unknown"
        }


async def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Process embeddings for Bindora platform")
    parser.add_argument("--drugs-only", action="store_true", help="Only process drug embeddings")
    parser.add_argument("--proteins-only", action="store_true", help="Only process protein embeddings")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size for processing")
    parser.add_argument("--data-dir", default="./data", help="Directory containing data files")

    args = parser.parse_args()

    print("=" * 60)
    print("Bindora - Embedding Processing Script")
    print("=" * 60)

    try:
        # Initialize encoders
        logger.info("Initializing AI models for embedding processing")

        protein_encoder = ProteinEncoder()
        drug_encoder = DrugEncoder()

        processor = EmbeddingProcessor(
            protein_encoder=protein_encoder,
            drug_encoder=drug_encoder,
            batch_size=args.batch_size
        )

        if args.drugs_only:
            await processor.process_drug_embeddings(Path(args.data_dir))
        elif args.proteins_only:
            await processor.process_protein_embeddings(Path(args.data_dir))
        else:
            await processor.process_all_embeddings(args.data_dir)

        print("\n" + "=" * 60)
        print("✅ Embedding processing complete!")
        print("=" * 60)

        print("
🚀 Next steps:"        print("1. Start the API server: uvicorn app.main:app --reload")
        print("2. Test predictions - they should be much faster now!")

    except KeyboardInterrupt:
        print("\n⚠️  Processing interrupted by user")
    except Exception as e:
        print(f"\n❌ Processing failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
