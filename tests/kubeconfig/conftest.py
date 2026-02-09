"""Kubeconfig module testing fixtures."""

import pathlib
import shutil
from collections.abc import Callable
from typing import Any

import pytest


@pytest.fixture(scope="session")
def kubeconfig_fixture_dir(
    tmp_path_factory: pytest.TempPathFactory,
    backend_tf_builder: Callable[..., None],
    common_fixture_dir_ignores: Callable[[Any, list[str]], set[str]],
) -> Callable[[str], pathlib.Path]:
    """Return a builder that makes a copy of the kubeconfig module with backend configured appropriately."""
    kubeconfig_module_dir = pathlib.Path(__file__).parent.parent.parent.joinpath("modules/kubeconfig").resolve()
    assert kubeconfig_module_dir.exists()
    assert kubeconfig_module_dir.is_dir()
    assert kubeconfig_module_dir.joinpath("main.tf").exists()
    assert kubeconfig_module_dir.joinpath("outputs.tf").exists()
    assert kubeconfig_module_dir.joinpath("variables.tf").exists()

    def _builder(name: str) -> pathlib.Path:
        fixture_dir = tmp_path_factory.mktemp(name)
        shutil.copytree(
            src=kubeconfig_module_dir,
            dst=fixture_dir,
            dirs_exist_ok=True,
            ignore=common_fixture_dir_ignores,
        )
        backend_tf_builder(
            fixture_dir=fixture_dir,
            name=name,
        )
        return fixture_dir

    return _builder
