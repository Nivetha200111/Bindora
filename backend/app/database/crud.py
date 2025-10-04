"""
CRUD operations for database models

Provides async database operations for drugs, proteins, and predictions.
"""
from typing import List, Optional, Dict, Any
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from sqlalchemy.orm import selectinload

from app.database.models import Drug, Protein, Prediction, SearchQuery, SystemStats

logger = structlog.get_logger()


class DrugCRUD:
    """CRUD operations for Drug model"""

    @staticmethod
    async def get_by_chembl_id(db: AsyncSession, chembl_id: str) -> Optional[Drug]:
        """Get drug by ChEMBL ID"""
        try:
            result = await db.execute(
                select(Drug).where(Drug.chembl_id == chembl_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get drug {chembl_id}", error=str(e))
            return None

    @staticmethod
    async def get_by_id(db: AsyncSession, drug_id: int) -> Optional[Drug]:
        """Get drug by internal ID"""
        try:
            result = await db.execute(
                select(Drug).where(Drug.id == drug_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get drug {drug_id}", error=str(e))
            return None

    @staticmethod
    async def get_drug_like(db: AsyncSession, limit: int = 100) -> List[Drug]:
        """Get drug-like molecules"""
        try:
            result = await db.execute(
                select(Drug)
                .where(Drug.is_drug_like == True)
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error("Failed to get drug-like molecules", error=str(e))
            return []

    @staticmethod
    async def get_by_clinical_phase(db: AsyncSession, phase: int, limit: int = 100) -> List[Drug]:
        """Get drugs by clinical phase"""
        try:
            result = await db.execute(
                select(Drug)
                .where(Drug.clinical_phase == phase)
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get drugs for phase {phase}", error=str(e))
            return []

    @staticmethod
    async def create(db: AsyncSession, drug_data: Dict[str, Any]) -> Optional[Drug]:
        """Create new drug record"""
        try:
            drug = Drug(**drug_data)
            db.add(drug)
            await db.flush()  # Get the ID without committing
            await db.refresh(drug)
            return drug
        except Exception as e:
            logger.error("Failed to create drug", error=str(e))
            return None

    @staticmethod
    async def update(db: AsyncSession, drug_id: int, update_data: Dict[str, Any]) -> Optional[Drug]:
        """Update drug record"""
        try:
            result = await db.execute(
                select(Drug).where(Drug.id == drug_id)
            )
            drug = result.scalar_one_or_none()

            if drug:
                for key, value in update_data.items():
                    setattr(drug, key, value)
                await db.flush()
                await db.refresh(drug)

            return drug
        except Exception as e:
            logger.error(f"Failed to update drug {drug_id}", error=str(e))
            return None

    @staticmethod
    async def count(db: AsyncSession) -> int:
        """Count total drugs"""
        try:
            result = await db.execute(select(func.count(Drug.id)))
            return result.scalar()
        except Exception as e:
            logger.error("Failed to count drugs", error=str(e))
            return 0


class ProteinCRUD:
    """CRUD operations for Protein model"""

    @staticmethod
    async def get_by_uniprot_id(db: AsyncSession, uniprot_id: str) -> Optional[Protein]:
        """Get protein by UniProt ID"""
        try:
            result = await db.execute(
                select(Protein).where(Protein.uniprot_id == uniprot_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get protein {uniprot_id}", error=str(e))
            return None

    @staticmethod
    async def get_by_gene_name(db: AsyncSession, gene_name: str) -> List[Protein]:
        """Get proteins by gene name"""
        try:
            result = await db.execute(
                select(Protein).where(Protein.gene_name == gene_name)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get proteins for gene {gene_name}", error=str(e))
            return []

    @staticmethod
    async def get_by_organism(db: AsyncSession, organism: str, limit: int = 100) -> List[Protein]:
        """Get proteins by organism"""
        try:
            result = await db.execute(
                select(Protein)
                .where(Protein.organism == organism)
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get proteins for organism {organism}", error=str(e))
            return []

    @staticmethod
    async def create(db: AsyncSession, protein_data: Dict[str, Any]) -> Optional[Protein]:
        """Create new protein record"""
        try:
            protein = Protein(**protein_data)
            db.add(protein)
            await db.flush()
            await db.refresh(protein)
            return protein
        except Exception as e:
            logger.error("Failed to create protein", error=str(e))
            return None

    @staticmethod
    async def count(db: AsyncSession) -> int:
        """Count total proteins"""
        try:
            result = await db.execute(select(func.count(Protein.id)))
            return result.scalar()
        except Exception as e:
            logger.error("Failed to count proteins", error=str(e))
            return 0


class PredictionCRUD:
    """CRUD operations for Prediction model"""

    @staticmethod
    async def get_by_protein_and_drug(db: AsyncSession, protein_id: int, drug_id: int) -> Optional[Prediction]:
        """Get prediction for specific protein-drug pair"""
        try:
            result = await db.execute(
                select(Prediction)
                .where(and_(
                    Prediction.protein_id == protein_id,
                    Prediction.drug_id == drug_id
                ))
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get prediction for protein {protein_id}, drug {drug_id}", error=str(e))
            return None

    @staticmethod
    async def get_by_protein(db: AsyncSession, protein_id: int, limit: int = 100) -> List[Prediction]:
        """Get all predictions for a protein"""
        try:
            result = await db.execute(
                select(Prediction)
                .where(Prediction.protein_id == protein_id)
                .order_by(desc(Prediction.binding_score))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get predictions for protein {protein_id}", error=str(e))
            return []

    @staticmethod
    async def get_by_drug(db: AsyncSession, drug_id: int, limit: int = 100) -> List[Prediction]:
        """Get all predictions for a drug"""
        try:
            result = await db.execute(
                select(Prediction)
                .where(Prediction.drug_id == drug_id)
                .order_by(desc(Prediction.binding_score))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get predictions for drug {drug_id}", error=str(e))
            return []

    @staticmethod
    async def create(db: AsyncSession, prediction_data: Dict[str, Any]) -> Optional[Prediction]:
        """Create new prediction record"""
        try:
            prediction = Prediction(**prediction_data)
            db.add(prediction)
            await db.flush()
            await db.refresh(prediction)
            return prediction
        except Exception as e:
            logger.error("Failed to create prediction", error=str(e))
            return None

    @staticmethod
    async def get_top_predictions(db: AsyncSession, limit: int = 50) -> List[Prediction]:
        """Get top predictions by binding score"""
        try:
            result = await db.execute(
                select(Prediction)
                .order_by(desc(Prediction.binding_score))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error("Failed to get top predictions", error=str(e))
            return []

    @staticmethod
    async def count(db: AsyncSession) -> int:
        """Count total predictions"""
        try:
            result = await db.execute(select(func.count(Prediction.id)))
            return result.scalar()
        except Exception as e:
            logger.error("Failed to count predictions", error=str(e))
            return 0


class SearchQueryCRUD:
    """CRUD operations for SearchQuery model"""

    @staticmethod
    async def create(db: AsyncSession, query_data: Dict[str, Any]) -> Optional[SearchQuery]:
        """Create new search query record"""
        try:
            search_query = SearchQuery(**query_data)
            db.add(search_query)
            await db.flush()
            await db.refresh(search_query)
            return search_query
        except Exception as e:
            logger.error("Failed to create search query", error=str(e))
            return None

    @staticmethod
    async def get_recent(db: AsyncSession, limit: int = 100) -> List[SearchQuery]:
        """Get recent search queries"""
        try:
            result = await db.execute(
                select(SearchQuery)
                .order_by(desc(SearchQuery.created_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error("Failed to get recent searches", error=str(e))
            return []

    @staticmethod
    async def count_by_type(db: AsyncSession, query_type: str) -> int:
        """Count searches by query type"""
        try:
            result = await db.execute(
                select(func.count(SearchQuery.id))
                .where(SearchQuery.query_type == query_type)
            )
            return result.scalar()
        except Exception as e:
            logger.error(f"Failed to count searches for type {query_type}", error=str(e))
            return 0


class SystemStatsCRUD:
    """CRUD operations for SystemStats model"""

    @staticmethod
    async def create_daily_stats(db: AsyncSession, stats_data: Dict[str, Any]) -> Optional[SystemStats]:
        """Create daily system statistics"""
        try:
            stats = SystemStats(**stats_data)
            db.add(stats)
            await db.flush()
            await db.refresh(stats)
            return stats
        except Exception as e:
            logger.error("Failed to create system stats", error=str(e))
            return None

    @staticmethod
    async def get_latest(db: AsyncSession) -> Optional[SystemStats]:
        """Get most recent system statistics"""
        try:
            result = await db.execute(
                select(SystemStats)
                .order_by(desc(SystemStats.date))
                .limit(1)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("Failed to get latest system stats", error=str(e))
            return None

    @staticmethod
    async def get_stats_range(db: AsyncSession, days: int = 30) -> List[SystemStats]:
        """Get system statistics for last N days"""
        try:
            from datetime import datetime, timedelta

            start_date = datetime.utcnow() - timedelta(days=days)

            result = await db.execute(
                select(SystemStats)
                .where(SystemStats.date >= start_date)
                .order_by(desc(SystemStats.date))
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get stats for last {days} days", error=str(e))
            return []

