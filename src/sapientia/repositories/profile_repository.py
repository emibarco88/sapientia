"""
Module: profile_repository.py

Purpose:
Persists generic profiling results into ekr_profile tables.
"""

import json
from sqlalchemy import text

from sapientia.config.profiling_config import ProfilingConfig
from sapientia.models.profile import DatasetProfile


class ProfileRepository:
    def __init__(self, connection):
        self.connection = connection

    def refresh_profile(self, dataset_id: int, profile: DatasetProfile) -> None:
        self._delete_existing_profiles(dataset_id)
        self._insert_dataset_profile(dataset_id, profile)
        self._insert_dataset_samples(dataset_id, profile)
        self._insert_column_profiles(dataset_id, profile)

    def _delete_existing_profiles(self, dataset_id: int) -> None:
        column_ids = self.connection.execute(
            text("""
                SELECT column_id
                FROM ekr_core."column"
                WHERE dataset_id = :dataset_id
            """),
            {"dataset_id": dataset_id},
        ).fetchall()

        for row in column_ids:
            self.connection.execute(
                text("""
                    DELETE FROM ekr_profile.column_profile
                    WHERE column_id = :column_id
                """),
                {"column_id": row.column_id},
            )

        self.connection.execute(
            text("""
                DELETE FROM ekr_profile.dataset_profile
                WHERE dataset_id = :dataset_id
            """),
            {"dataset_id": dataset_id},
        )

        self.connection.execute(
            text("""
                DELETE FROM ekr_profile.dataset_sample
                WHERE dataset_id = :dataset_id
            """),
            {"dataset_id": dataset_id},
        )

    def _insert_dataset_profile(self, dataset_id: int, profile: DatasetProfile) -> None:
        self.connection.execute(
            text("""
                INSERT INTO ekr_profile.dataset_profile
                (
                    dataset_id,
                    row_count,
                    column_count,
                    duplicate_rows,
                    profile_json
                )
                VALUES
                (
                    :dataset_id,
                    :row_count,
                    :column_count,
                    :duplicate_rows,
                    CAST(:profile_json AS JSONB)
                )
            """),
            {
                "dataset_id": dataset_id,
                "row_count": profile.row_count,
                "column_count": profile.column_count,
                "duplicate_rows": profile.duplicate_rows,
                "profile_json": json.dumps(profile.profile_json, default=str, allow_nan=False),
            },
        )

    def _insert_dataset_samples(self, dataset_id: int, profile: DatasetProfile) -> None:
        if not ProfilingConfig.STORE_SAMPLE_DATA:
            return

        if not profile.sample_rows:
            return

        sample_rows = profile.sample_rows[:ProfilingConfig.STORED_SAMPLE_ROWS]

        for sample_number, sample_row in enumerate(sample_rows, start=1):
            self.connection.execute(
                text("""
                    INSERT INTO ekr_profile.dataset_sample
                    (
                        dataset_id,
                        sample_number,
                        sample_json
                    )
                    VALUES
                    (
                        :dataset_id,
                        :sample_number,
                        CAST(:sample_json AS JSONB)
                    )
                """),
                {
                    "dataset_id": dataset_id,
                    "sample_number": sample_number,
                    "sample_json": json.dumps(sample_row, default=str, allow_nan=False),
                },
            )

    def _insert_column_profiles(self, dataset_id: int, profile: DatasetProfile) -> None:
        column_map = self._get_column_id_map(dataset_id)

        for column_profile in profile.column_profiles:
            column_id = column_map.get(column_profile.column_name)

            if column_id is None:
                continue

            self.connection.execute(
                text("""
                    INSERT INTO ekr_profile.column_profile
                    (
                        column_id,
                        null_count,
                        null_percentage,
                        distinct_count,
                        unique_percentage,
                        min_value,
                        max_value,
                        min_length,
                        max_length,
                        avg_length,
                        inferred_data_type,
                        completeness_score,
                        validity_score,
                        consistency_score,
                        uniqueness_score,
                        quality_score,
                        sample_values,
                        top_values,
                        pattern_summary,
                        numeric_summary,
                        date_summary,
                        boolean_summary,
                        structure_summary,
                        anomaly_summary,
                        profile_json
                    )
                    VALUES
                    (
                        :column_id,
                        :null_count,
                        :null_percentage,
                        :distinct_count,
                        :unique_percentage,
                        :min_value,
                        :max_value,
                        :min_length,
                        :max_length,
                        :avg_length,
                        :inferred_data_type,
                        :completeness_score,
                        :validity_score,
                        :consistency_score,
                        :uniqueness_score,
                        :quality_score,
                        CAST(:sample_values AS JSONB),
                        CAST(:top_values AS JSONB),
                        CAST(:pattern_summary AS JSONB),
                        CAST(:numeric_summary AS JSONB),
                        CAST(:date_summary AS JSONB),
                        CAST(:boolean_summary AS JSONB),
                        CAST(:structure_summary AS JSONB),
                        CAST(:anomaly_summary AS JSONB),
                        CAST(:profile_json AS JSONB)
                    )
                """),
                {
                    "column_id": column_id,
                    "null_count": column_profile.null_count,
                    "null_percentage": column_profile.null_percentage,
                    "distinct_count": column_profile.distinct_count,
                    "unique_percentage": column_profile.unique_percentage,
                    "min_value": column_profile.min_value,
                    "max_value": column_profile.max_value,
                    "min_length": column_profile.min_length,
                    "max_length": column_profile.max_length,
                    "avg_length": column_profile.avg_length,
                    "inferred_data_type": column_profile.inferred_data_type,
                    "completeness_score": column_profile.completeness_score,
                    "validity_score": column_profile.validity_score,
                    "consistency_score": column_profile.consistency_score,
                    "uniqueness_score": column_profile.uniqueness_score,
                    "quality_score": column_profile.quality_score,
                    "sample_values": json.dumps(column_profile.sample_values, default=str, allow_nan=False),
                    "top_values": json.dumps(column_profile.top_values, default=str, allow_nan=False),
                    "pattern_summary": json.dumps(column_profile.pattern_summary, default=str, allow_nan=False),
                    "numeric_summary": json.dumps(column_profile.numeric_summary, default=str, allow_nan=False),
                    "date_summary": json.dumps(column_profile.date_summary, default=str, allow_nan=False),
                    "boolean_summary": json.dumps(column_profile.boolean_summary, default=str, allow_nan=False),
                    "structure_summary": json.dumps(column_profile.structure_summary, default=str, allow_nan=False),
                    "anomaly_summary": json.dumps(column_profile.anomaly_summary, default=str, allow_nan=False),
                    "profile_json": json.dumps(column_profile.profile_json, default=str, allow_nan=False),
                },
            )

    def _get_column_id_map(self, dataset_id: int) -> dict:
        rows = self.connection.execute(
            text("""
                SELECT column_id, name
                FROM ekr_core."column"
                WHERE dataset_id = :dataset_id
            """),
            {"dataset_id": dataset_id},
        ).fetchall()

        return {row.name: row.column_id for row in rows}