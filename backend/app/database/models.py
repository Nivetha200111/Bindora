"""
SQLAlchemy database models for drug-target interaction platform

Defines the database schema for storing drugs, proteins, and predictions.
Uses PostgreSQL with pgvector extension for vector similarity search.
"""
from datetime import datetime
from typing import List, Optional
import structlog
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, DateTime,
    ForeignKey, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

logger = structlog.get_logger()

Base = declarative_base()


class Drug(Base):
    """
    Drug molecule model

    Stores information about drug compounds from ChEMBL database.
    """
    __tablename__ = "drugs"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # ChEMBL identifier (unique)
    chembl_id = Column(String(20), unique=True, nullable=False, index=True)

    # Basic information
    name = Column(String(255), nullable=True)
    smiles = Column(Text, nullable=False)  # SMILES notation
    inchi_key = Column(String(27), nullable=True)  # InChI key

    # Molecular properties
    molecular_weight = Column(Float, nullable=True)
    logp = Column(Float, nullable=True)
    hbd = Column(Integer, nullable=True)  # Hydrogen bond donors
    hba = Column(Integer, nullable=True)  # Hydrogen bond acceptors
    tpsa = Column(Float, nullable=True)   # Topological polar surface area

    # Drug-likeness
    is_drug_like = Column(Boolean, nullable=True)
    passes_lipinski = Column(Boolean, nullable=True)

    # Clinical information
    clinical_phase = Column(Integer, nullable=True)  # 0=preclinical, 4=approved

    # External identifiers
    drugbank_id = Column(String(20), nullable=True)
    pubchem_cid = Column(String(20), nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Vector embedding for similarity search (pgvector)
    # Uncomment when using pgvector extension:
    # embedding = Column(Vector(2048), nullable=True)

    # Relationships
    predictions = relationship("Prediction", back_populates="drug")

    # Indexes for performance
    __table_args__ = (
        Index('ix_drugs_chembl_id', 'chembl_id'),
        Index('ix_drugs_clinical_phase', 'clinical_phase'),
        Index('ix_drugs_is_drug_like', 'is_drug_like'),
        CheckConstraint('clinical_phase >= 0 AND clinical_phase <= 4', name='check_clinical_phase'),
    )

    def __repr__(self):
        return f"<Drug(chembl_id='{self.chembl_id}', name='{self.name}')>"


class Protein(Base):
    """
    Protein target model

    Stores information about protein targets from UniProt database.
    """
    __tablename__ = "proteins"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # UniProt identifier (unique)
    uniprot_id = Column(String(20), unique=True, nullable=False, index=True)

    # Basic information
    name = Column(String(255), nullable=True)
    gene_name = Column(String(50), nullable=True, index=True)
    organism = Column(String(100), nullable=True)

    # Sequence information
    sequence = Column(Text, nullable=True)  # Amino acid sequence
    sequence_length = Column(Integer, nullable=True)

    # Structural information
    molecular_weight = Column(Float, nullable=True)
    structure_available = Column(Boolean, default=False)

    # Functional information
    function = Column(Text, nullable=True)
    subcellular_location = Column(String(255), nullable=True)
    tissue_specificity = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Vector embedding for similarity search (pgvector)
    # Uncomment when using pgvector extension:
    # embedding = Column(Vector(1280), nullable=True)

    # Relationships
    predictions = relationship("Prediction", back_populates="protein")

    # Indexes for performance
    __table_args__ = (
        Index('ix_proteins_uniprot_id', 'uniprot_id'),
        Index('ix_proteins_gene_name', 'gene_name'),
        Index('ix_proteins_organism', 'organism'),
    )

    def __repr__(self):
        return f"<Protein(uniprot_id='{self.uniprot_id}', gene_name='{self.gene_name}')>"


class Prediction(Base):
    """
    Drug-target binding prediction model

    Stores predictions made by the AI models.
    """
    __tablename__ = "predictions"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    protein_id = Column(Integer, ForeignKey('proteins.id'), nullable=False, index=True)
    drug_id = Column(Integer, ForeignKey('drugs.id'), nullable=False, index=True)

    # Prediction data
    binding_score = Column(Float, nullable=False)  # 0-100 scale
    similarity_score = Column(Float, nullable=True)  # Cosine similarity (-1 to 1)
    confidence = Column(Float, nullable=True)  # Prediction confidence

    # Prediction metadata
    prediction_method = Column(String(50), nullable=False, default="esm2_morgan_similarity")
    model_version = Column(String(20), nullable=False, default="1.0.0")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    protein = relationship("Protein", back_populates="predictions")
    drug = relationship("Drug", back_populates="predictions")

    # Indexes for performance
    __table_args__ = (
        Index('ix_predictions_protein_drug', 'protein_id', 'drug_id'),
        Index('ix_predictions_binding_score', 'binding_score'),
        Index('ix_predictions_created_at', 'created_at'),
        UniqueConstraint('protein_id', 'drug_id', 'model_version', name='uq_prediction_protein_drug_model'),
        CheckConstraint('binding_score >= 0 AND binding_score <= 100', name='check_binding_score'),
    )

    def __repr__(self):
        return f"<Prediction(protein_id={self.protein_id}, drug_id={self.drug_id}, score={self.binding_score})>"


class SearchQuery(Base):
    """
    Search query log model

    Tracks user searches for analytics and debugging.
    """
    __tablename__ = "search_queries"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Query information
    query_text = Column(String(1000), nullable=False)
    query_type = Column(String(20), nullable=False)  # 'disease', 'gene', 'sequence'

    # Results
    num_results = Column(Integer, nullable=False, default=0)
    search_time_ms = Column(Integer, nullable=True)  # Search duration in milliseconds

    # Metadata
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Indexes for performance
    __table_args__ = (
        Index('ix_search_queries_created_at', 'created_at'),
        Index('ix_search_queries_query_type', 'query_type'),
        CheckConstraint("query_type IN ('disease', 'gene', 'sequence')", name='check_query_type'),
    )

    def __repr__(self):
        return f"<SearchQuery(query='{self.query_text[:50]}...', type='{self.query_type}')>"


class SystemStats(Base):
    """
    System statistics model

    Stores daily statistics for monitoring and analytics.
    """
    __tablename__ = "system_stats"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Date
    date = Column(DateTime, nullable=False, index=True)

    # Counts
    total_drugs = Column(Integer, nullable=False, default=0)
    total_proteins = Column(Integer, nullable=False, default=0)
    total_predictions = Column(Integer, nullable=False, default=0)
    total_searches = Column(Integer, nullable=False, default=0)

    # Performance metrics
    avg_prediction_time_ms = Column(Float, nullable=True)
    avg_search_time_ms = Column(Float, nullable=True)

    # Cache statistics
    cache_hits = Column(Integer, nullable=False, default=0)
    cache_misses = Column(Integer, nullable=False, default=0)

    # Model status
    models_loaded = Column(Boolean, nullable=False, default=True)
    database_healthy = Column(Boolean, nullable=False, default=True)

    # Indexes for performance
    __table_args__ = (
        Index('ix_system_stats_date', 'date'),
        UniqueConstraint('date', name='uq_system_stats_date'),
    )

    def __repr__(self):
        return f"<SystemStats(date='{self.date}', predictions={self.total_predictions})>"


# Import Vector type for pgvector if available
try:
    from pgvector.sqlalchemy import Vector

    # Add vector columns to existing models when pgvector is available
    Drug.embedding = Column(Vector(2048), nullable=True)
    Protein.embedding = Column(Vector(1280), nullable=True)

    logger.info("pgvector extension detected, vector columns added")

except ImportError:
    logger.warning("pgvector not available, vector columns not added")
    # Vector columns are commented out above when pgvector is not available

