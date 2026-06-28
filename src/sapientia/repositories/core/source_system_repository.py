from sqlalchemy import text


class SourceSystemRepository:
    def __init__(self, connection):
        self.connection = connection

    def get_by_name(self, project_id: int, name: str):
        sql = text("""
            SELECT source_system_id
            FROM ekr_core.source_system
            WHERE project_id = :project_id
              AND name = :name
        """)

        result = self.connection.execute(sql, {
            "project_id": project_id,
            "name": name
        }).fetchone()

        return result[0] if result else None

    def create(self, project_id: int, name: str, source_type: str, description: str = None) -> int:
        sql = text("""
            INSERT INTO ekr_core.source_system
            (
                project_id,
                name,
                source_type,
                description
            )
            VALUES
            (
                :project_id,
                :name,
                :source_type,
                :description
            )
            RETURNING source_system_id
        """)

        result = self.connection.execute(sql, {
            "project_id": project_id,
            "name": name,
            "source_type": source_type,
            "description": description,
        })

        return result.scalar_one()

    def create_or_get(self, project_id: int, name: str, source_type: str, description: str = None) -> int:
        existing_id = self.get_by_name(project_id, name)

        if existing_id:
            return existing_id

        return self.create(
            project_id=project_id,
            name=name,
            source_type=source_type,
            description=description,
        )