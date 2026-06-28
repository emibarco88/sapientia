"""
Module: runtime_config_service.py

Purpose:
Reads runtime configuration from ekr_runtime with safe Python fallbacks.
"""

from sapientia.db.connection import get_engine
from sapientia.repositories.runtime.runtime_repository import RuntimeRepository


class RuntimeConfigService:

    def get_config(
        self,
        component_code: str,
        defaults: dict | None = None,
    ) -> dict:
        defaults = defaults or {}

        try:
            engine = get_engine()

            with engine.begin() as connection:
                repository = RuntimeRepository(connection)
                db_config = repository.get_component_configuration(component_code)

            return {
                **defaults,
                **db_config,
            }

        except Exception:
            return defaults