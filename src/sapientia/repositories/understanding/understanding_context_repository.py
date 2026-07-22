"""
Module: understanding_context_repository.py

Purpose:
Provides backward compatibility for code that still imports
UnderstandingContextRepository.

The implementation now lives in EnterpriseEvidenceRepository.
New code should use EnterpriseEvidenceRepository directly.
"""

from sapientia.repositories.understanding.enterprise_evidence_repository import (
    EnterpriseEvidenceRepository,
)


class UnderstandingContextRepository(
    EnterpriseEvidenceRepository
):
    """
    Backward-compatible alias for EnterpriseEvidenceRepository.

    Existing code can continue using:

        UnderstandingContextRepository(connection)
            .get_understanding_context(dataset_id)

    New code should prefer:

        EnterpriseEvidenceRepository(connection)
            .load_dataset_context(dataset_id)
    """

    pass