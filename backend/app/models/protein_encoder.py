"""
Protein Sequence Encoder using ESM-2 model

Encodes protein sequences into vector embeddings using Facebook's ESM-2 model.
ESM-2 is a state-of-the-art protein language model trained on UniRef50.
"""
import re
import time
from typing import List, Optional, Union
import numpy as np
import structlog
from pathlib import Path

logger = structlog.get_logger()


class ProteinEncoder:
    """
    Protein sequence encoder using ESM-2 model

    Args:
        model_name: Hugging Face model identifier (default: facebook/esm2_t33_650M_UR50D)
        device: Device to run model on ('auto', 'cpu', 'cuda', 'mps')
        cache_dir: Directory to cache downloaded models
        max_length: Maximum sequence length (ESM-2 supports up to 1024)
    """

    def __init__(
        self,
        model_name: str = "facebook/esm2_t33_650M_UR50D",
        device: str = "auto",
        cache_dir: str = "./models",
        max_length: int = 1024
    ):
        self.model_name = model_name
        self.max_length = max_length
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        # Determine device
        if device == "auto":
            self.device = self._get_best_device()
        else:
            self.device = device

        logger.info(
            "Initializing protein encoder",
            model=model_name,
            device=self.device,
            max_length=max_length
        )

        # Lazy loading of model and tokenizer
        self._model = None
        self._tokenizer = None

        # Check if scientific libraries are available
        self._scientific_mode = self._check_scientific_libraries()

        if self._scientific_mode:
            # Load model on first use
            self._ensure_model_loaded()
        else:
            logger.warning("Running in demo mode - scientific libraries not available")

    def _get_best_device(self) -> str:
        """Determine the best available device for model inference"""
        try:
            import torch

            # Try CUDA
            if torch.cuda.is_available():
                logger.info("Using CUDA device")
                return "cuda"

            # Try MPS for Apple Silicon
            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                logger.info("Using MPS device")
                return "mps"

        except ImportError:
            logger.warning("PyTorch not available, falling back to CPU")

        logger.info("Using CPU device")
        return "cpu"

    def _check_scientific_libraries(self) -> bool:
        """Check if scientific libraries are available"""
        try:
            import torch
            import transformers
            return True
        except ImportError:
            return False

    def _ensure_model_loaded(self):
        """Lazy load model and tokenizer"""
        if not self._scientific_mode:
            return

        if self._model is None or self._tokenizer is None:
            start_time = time.time()

            try:
                from transformers import AutoTokenizer, AutoModel

                logger.info("Loading ESM-2 model and tokenizer", model=self.model_name)

                # Load tokenizer
                self._tokenizer = AutoTokenizer.from_pretrained(
                    self.model_name,
                    cache_dir=str(self.cache_dir),
                    local_files_only=False
                )

                # Load model
                self._model = AutoModel.from_pretrained(
                    self.model_name,
                    cache_dir=str(self.cache_dir),
                    local_files_only=False
                )

                # Move to device
                if self.device != "cpu":
                    try:
                        self._model = self._model.to(self.device)
                    except RuntimeError as e:
                        logger.warning(f"Failed to move model to {self.device}", error=str(e))
                        self.device = "cpu"
                        self._model = self._model.to("cpu")

                # Set to evaluation mode
                self._model.eval()

                load_time = time.time() - start_time
                logger.info(
                    "ESM-2 model loaded successfully",
                    load_time=f"{load_time".2f"}s",
                    device=self.device,
                    embedding_dim=1280
                )

            except Exception as e:
                logger.error("Failed to load ESM-2 model", error=str(e))
                raise RuntimeError(f"Could not load protein encoder model: {e}")

    def _validate_sequence(self, sequence: str) -> bool:
        """
        Validate amino acid sequence

        Args:
            sequence: Protein sequence string

        Returns:
            True if valid, False otherwise
        """
        if not sequence or not isinstance(sequence, str):
            return False

        # Standard amino acids (IUPAC one-letter codes)
        valid_amino_acids = set("ACDEFGHIKLMNPQRSTVWY")

        # Remove common separators and convert to uppercase
        cleaned = re.sub(r'[^A-Z]', '', sequence.upper())

        # Check if all characters are valid amino acids
        return all(aa in valid_amino_acids for aa in cleaned)

    def _preprocess_sequence(self, sequence: str) -> str:
        """
        Preprocess sequence for model input

        Args:
            sequence: Raw protein sequence

        Returns:
            Preprocessed sequence
        """
        # Remove whitespace and common separators
        cleaned = re.sub(r'[\s\-_]', '', sequence.upper())

        # Validate sequence
        if not self._validate_sequence(cleaned):
            raise ValueError(
                f"Invalid amino acid sequence. "
                f"Sequence must contain only standard amino acids (ACDEFGHIKLMNPQRSTVWY). "
                f"Got: {sequence[:50]}..."
            )

        # Truncate if too long
        if len(cleaned) > self.max_length:
            logger.warning(
                f"Sequence truncated from {len(cleaned)} to {self.max_length} amino acids"
            )
            cleaned = cleaned[:self.max_length]

        return cleaned

    def encode(self, sequence: str) -> np.ndarray:
        """
        Encode a single protein sequence into an embedding vector

        Args:
            sequence: Amino acid sequence (e.g., "MKTIIALSYIFCLVFA...")

        Returns:
            Embedding vector of shape (1280,)

        Raises:
            ValueError: If sequence is invalid or empty
            RuntimeError: If model inference fails
        """
        if not sequence or not sequence.strip():
            raise ValueError("Empty or None sequence provided")

        # Validate sequence first
        cleaned_sequence = self._preprocess_sequence(sequence)

        if not self._scientific_mode:
            # Demo mode: return mock embedding
            logger.info("Using demo mode for protein encoding")
            return self._generate_mock_embedding(cleaned_sequence)

        try:
            # Ensure model is loaded
            self._ensure_model_loaded()

            # Tokenize
            inputs = self._tokenizer(
                cleaned_sequence,
                return_tensors="pt",
                padding=False,
                truncation=True,
                max_length=self.max_length
            )

            # Move inputs to device
            if self.device != "cpu":
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Get embeddings
            with np.errstate(divide='ignore', invalid='ignore'):
                with torch.no_grad():
                    outputs = self._model(**inputs)
                    # Use mean pooling across sequence length
                    # Shape: (1, seq_len, hidden_size) -> (hidden_size,)
                    embeddings = outputs.last_hidden_state.mean(dim=1).cpu().numpy()

            # Squeeze to 1D array
            embedding = embeddings[0]  # Shape: (1280,)

            # Check for NaN or Inf values
            if not np.isfinite(embedding).all():
                logger.warning("Non-finite values in embedding, replacing with zeros")
                embedding = np.nan_to_num(embedding, nan=0.0, posinf=0.0, neginf=0.0)

            # Normalize to unit vector (optional but recommended)
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm

            logger.debug(
                f"Encoded protein sequence",
                sequence_length=len(cleaned_sequence),
                embedding_shape=embedding.shape
            )

            return embedding

        except Exception as e:
            logger.error("Failed to encode protein sequence", error=str(e))
            raise RuntimeError(f"Protein encoding failed: {e}")

    def _generate_mock_embedding(self, sequence: str) -> np.ndarray:
        """
        Generate mock embedding for demo purposes

        Args:
            sequence: Protein sequence

        Returns:
            Mock embedding vector
        """
        # Create deterministic mock embedding based on sequence hash
        import hashlib

        # Create hash of sequence for deterministic results
        seq_hash = int(hashlib.md5(sequence.encode()).hexdigest()[:8], 16)

        # Generate pseudo-random embedding
        np.random.seed(seq_hash)
        embedding = np.random.randn(1280).astype(np.float32)

        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        logger.debug(
            f"Generated mock protein embedding",
            sequence_length=len(sequence),
            embedding_shape=embedding.shape,
            demo_mode=True
        )

        return embedding

    def batch_encode(self, sequences: List[str]) -> np.ndarray:
        """
        Encode multiple protein sequences in batch

        Args:
            sequences: List of amino acid sequences

        Returns:
            Array of embeddings with shape (n_sequences, 1280)

        Raises:
            ValueError: If sequences list is empty or contains invalid sequences
        """
        if not sequences:
            raise ValueError("Empty sequences list provided")

        if not self._scientific_mode:
            # Demo mode: generate mock embeddings for all sequences
            logger.info(f"Using demo mode for batch encoding {len(sequences)} sequences")
            embeddings = []
            for seq in sequences:
                embedding = self._generate_mock_embedding(seq)
                embeddings.append(embedding)
            return np.array(embeddings)

        if len(sequences) == 1:
            # Single sequence case
            embedding = self.encode(sequences[0])
            return embedding.reshape(1, -1)

        try:
            # Preprocess all sequences
            cleaned_sequences = []
            for seq in sequences:
                cleaned_sequences.append(self._preprocess_sequence(seq))

            # Ensure model is loaded
            self._ensure_model_loaded()

            # Tokenize batch
            inputs = self._tokenizer(
                cleaned_sequences,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=self.max_length
            )

            # Move to device
            if self.device != "cpu":
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Get embeddings
            with torch.no_grad():
                outputs = self._model(**inputs)
                # Mean pooling across sequence length
                embeddings = outputs.last_hidden_state.mean(dim=1).cpu().numpy()

            # Handle non-finite values
            embeddings = np.nan_to_num(
                embeddings,
                nan=0.0,
                posinf=0.0,
                neginf=0.0
            )

            # Normalize embeddings
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1, norms)  # Avoid division by zero
            embeddings = embeddings / norms

            logger.info(
                f"Batch encoded {len(sequences)} protein sequences",
                batch_size=len(sequences),
                embedding_shape=embeddings.shape
            )

            return embeddings

        except Exception as e:
            logger.error("Failed to batch encode protein sequences", error=str(e))
            raise RuntimeError(f"Batch protein encoding failed: {e}")

    def get_embedding_dimension(self) -> int:
        """Get the dimension of generated embeddings"""
        return 1280  # ESM-2 t33_650M produces 1280-dimensional embeddings

    def __repr__(self) -> str:
        return f"ProteinEncoder(model={self.model_name}, device={self.device})"


# Import torch here to avoid issues if not installed
try:
    import torch
except ImportError:
    torch = None
    logger.warning("PyTorch not available. Protein encoding will not work.")
