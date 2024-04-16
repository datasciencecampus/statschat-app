"""Functions for retrieving TOML configuration files."""

from importlib import resources

import toml
from typing import Optional


def _load_default(name: str) -> dict:
    """
    Get the default configuration for a task.

    Parameters
    ----------
    name : str, {"main", "questions", "webscraping"}
        Name of the task. Must be one of `main`, `questions`, or
        `webscraping`.

    Raises
    ------
    ValueError
        If `name` is invalid.

    Returns
    -------
    config : dict
        The contents of the default configuration file.
    """

    if name not in ("main", "questions", "webscraping"):
        raise ValueError(
            "Name is invalid. Must be one of `main`, `questions`, or `webscraping`."
        )

    configs = resources.files("statschat._config")
    with resources.as_file(configs.joinpath(f"{name}.toml")) as c:
        config = toml.load(c)

    return config


def load_config(path: Optional[str] = None, name: Optional[str] = None):
    """
    Load a configuration from file.

    You can either:
    - pass a path to a TOML configuration file, or
    - use one of the defaults via the name of the task

    If you specify both, `path` takes precedence.

    Parameters
    ----------
    path : str, optional
        Path to the configuration file.
    name : {"main", "questions", "webscraping"}, optional
        Name of the task to use their default configuration. Must be one
        of `main`, `questions`, or `webscraping`.

    Returns
    -------
    config : dict
        The contents of the configuration file.
    """

    if path is None and name is None:
        raise ValueError("At least one of `path` and `name` must be specified.")

    if isinstance(path, str):
        return toml.load(path)

    return _load_default(name)
