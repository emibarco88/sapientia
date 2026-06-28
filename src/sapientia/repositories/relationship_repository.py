"""
Module: relationship_repository.py

Purpose:
Provides CRUD operations for the ekr_core.relationship table.
"""

from sqlalchemy import text
from sapientia.models.metadata import RelationshipMetadata


class RelationshipRepository:
    def __init__(self, connection):
        self.connection = connection

    def delete_by_parent_dataset(self, parent_dataset_id: int) -> None:
        sql = text("""
            DELETE FROM ekr_core.relationship
            WHERE parent_dataset_id = :parent_dataset_id
        """)

        self.connection.execute(sql, {"parent_dataset_id": parent_dataset_id})

    def create(
        self,
        parent_dataset_id: int,
        child_dataset_id: int,
        relationship: RelationshipMetadata,
    ) -> int:
        sql = text("""
            INSERT INTO ekr_core.relationship
            (
                parent_dataset_id,
                child_dataset_id,
                relationship_type,
                confidence,
                description
            )
            VALUES
            (
                :parent_dataset_id,
                :child_dataset_id,
                :relationship_type,
                :confidence,
                :description
            )
            RETURNING relationship_id
        """)

        result = self.connection.execute(
            sql,
            {
                "parent_dataset_id": parent_dataset_id,
                "child_dataset_id": child_dataset_id,
                "relationship_type": relationship.relationship_type,
                "confidence": relationship.confidence,
                "description": relationship.description,
            },
        )

        return result.scalar_one()