"""Test fixture for Kubeconfig terraform/tofu test files."""

import pathlib
from collections.abc import Callable, Generator
from typing import Any

import pytest

from tests import run_tf_test

FIXTURE_NAME = "kubeconfig-tftest"


@pytest.fixture(scope="module")
def fixture_output(
    kubeconfig_fixture_dir: Callable[[str], pathlib.Path],
) -> Generator[list[dict[str, Any]], None, None]:
    """Run Kubeconfig module HCL tests."""
    with run_tf_test(
        fixture=kubeconfig_fixture_dir(FIXTURE_NAME),
    ) as output:
        yield output


def test_pass(
    fixture_output: list[dict[str, Any]],
) -> None:
    """Assert that every test and scenario was a success."""
    for entry in [x["test_run"] for x in fixture_output if "test_run" in x]:
        assert entry["status"] == "pass", f"tftest {entry['path']}:{entry['run']}: status is {entry['status']}"
