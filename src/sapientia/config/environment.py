"""
Module: environment.py

Purpose:
Loads Sapientia environment variables once during application startup.

The loader resolves the project-level .env file explicitly rather than
relying on python-dotenv stack-frame discovery.
"""

from __future__ import annotations

import os
from pathlib import Path
from threading import Lock

from dotenv import load_dotenv


_environment_lock = Lock()
_environment_loaded = False


def find_project_root(
    start_path: Path | None = None,
) -> Path:
    """
    Find the Sapientia project root.

    The project root is identified by the presence of one or more common
    project markers such as .env, pyproject.toml, requirements.txt or
    the src directory.

    Parameters
    ----------
    start_path:
        Optional starting path. Defaults to this module's location.

    Returns
    -------
    Path
        Resolved project root.

    Raises
    ------
    RuntimeError
        If a suitable project root cannot be found.
    """

    current_path = (
        start_path.resolve()
        if start_path is not None
        else Path(__file__).resolve()
    )

    if current_path.is_file():
        current_path = current_path.parent

    for candidate in (
        current_path,
        *current_path.parents,
    ):
        has_src_directory = (
            candidate / "src"
        ).is_dir()

        has_project_marker = any(
            (
                (candidate / ".env").is_file(),
                (candidate / "pyproject.toml").is_file(),
                (candidate / "requirements.txt").is_file(),
            )
        )

        if (
            has_src_directory
            and has_project_marker
        ):
            return candidate

    raise RuntimeError(
        "Unable to locate the Sapientia project root. "
        "Expected a parent directory containing the src directory "
        "and a project marker such as .env or pyproject.toml."
    )


def load_application_environment(
    env_file: str | Path | None = None,
    *,
    override: bool = False,
    required: bool = True,
) -> Path | None:
    """
    Load Sapientia environment variables once.

    Parameters
    ----------
    env_file:
        Optional explicit environment file path. When omitted, the
        project-level .env file is used.

    override:
        Whether values from .env should replace variables already
        present in the operating-system environment.

    required:
        Whether a missing .env file should raise an exception.

    Returns
    -------
    Path | None
        The loaded environment file path, or None when the file is
        optional and does not exist.
    """

    global _environment_loaded

    if _environment_loaded:
        return _resolve_environment_path(
            env_file=env_file,
        )

    with _environment_lock:
        if _environment_loaded:
            return _resolve_environment_path(
                env_file=env_file,
            )

        environment_path = (
            _resolve_environment_path(
                env_file=env_file,
            )
        )

        if not environment_path.is_file():
            if required:
                raise FileNotFoundError(
                    "Sapientia environment file was not found: "
                    f"{environment_path}"
                )

            return None

        loaded = load_dotenv(
            dotenv_path=environment_path,
            override=override,
        )

        if not loaded and required:
            raise RuntimeError(
                "Sapientia environment file could not be loaded: "
                f"{environment_path}"
            )

        _environment_loaded = True

        return environment_path


def require_environment_variable(
    variable_name: str,
) -> str:
    """
    Return a required environment variable.

    Raises a clear configuration exception when the variable is absent.
    """

    value = os.getenv(
        variable_name,
    )

    if value is None or not value.strip():
        raise RuntimeError(
            "Required environment variable is missing: "
            f"{variable_name}"
        )

    return value.strip()


def _resolve_environment_path(
    env_file: str | Path | None,
) -> Path:
    """
    Resolve the environment file path.
    """

    if env_file is not None:
        supplied_path = Path(
            env_file
        ).expanduser()

        if supplied_path.is_absolute():
            return supplied_path.resolve()

        return (
            Path.cwd()
            / supplied_path
        ).resolve()

    configured_path = os.getenv(
        "SAPIENTIA_ENV_FILE"
    )

    if configured_path:
        supplied_path = Path(
            configured_path
        ).expanduser()

        if supplied_path.is_absolute():
            return supplied_path.resolve()

        return (
            Path.cwd()
            / supplied_path
        ).resolve()

    return (
        find_project_root()
        / ".env"
    )