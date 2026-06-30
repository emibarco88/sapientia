"""
Module: business_domain_repository.py

Purpose:
Reads business domain reference data.
"""

from sqlalchemy import text


class BusinessDomainRepository:
    def __init__(self, connection):
        self.connection = connection

    def get_business_domain_id(self, domain_code: str | None) -> int:
        code = (domain_code or "UNKNOWN").upper().strip()

        row = self.connection.execute(
            text("""
                SELECT business_domain_id
                FROM ekr_business.business_domain
                WHERE domain_code = :domain_code
                  AND is_active = TRUE
            """),
            {"domain_code": code},
        ).fetchone()

        if row:
            return row.business_domain_id

        unknown = self.connection.execute(
            text("""
                SELECT business_domain_id
                FROM ekr_business.business_domain
                WHERE domain_code = 'UNKNOWN'
            """)
        ).fetchone()

        if not unknown:
            raise ValueError("UNKNOWN business domain is missing.")

        return unknown.business_domain_id