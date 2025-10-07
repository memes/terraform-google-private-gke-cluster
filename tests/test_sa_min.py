"""Test fixture for service account module with minimal configuration."""

import pathlib
import re
from collections.abc import Generator
from typing import Any

import pytest
from google.cloud import iam_admin_v1, resourcemanager_v3

from .conftest import run_tofu_in_workspace

FIXTURE_NAME = "sa-min"
EXPECTED_DISPLAY_NAME = "Generated GKE Service Account"
EXPECTED_DESCRIPTION = "A Terraform generated Service Account suitable for use by GKE nodes. The service account is intended to have minimal roles required to log and report base metrics to Google Cloud Operations."  # noqa: E501
EXPECTED_PROJECT_ROLES = [
    "roles/container.defaultNodeServiceAccount",
    "roles/stackdriver.resourceMetadata.writer",
]


@pytest.fixture(scope="module")
def fixture_name(prefix: str) -> str:
    """Return the name to use for resources in this module."""
    return f"{prefix}-{FIXTURE_NAME}"


@pytest.fixture(scope="module")
def fixture_output(
    sa_fixture_dir: pathlib.Path,
    project_id: str,
    fixture_name: str,
) -> Generator[dict[str, Any], None, None]:
    """Create service account for test case."""
    with run_tofu_in_workspace(
        fixture=sa_fixture_dir,
        workspace=FIXTURE_NAME,
        tfvars={
            "project_id": project_id,
            "name": fixture_name,
        },
    ) as output:
        yield output


def test_output_values(fixture_output: dict[str, Any], project_id: str, fixture_name: str) -> None:
    """Verify the fixture output meets expectations."""
    sa_id = fixture_output["id"]
    assert sa_id
    assert re.match(pattern=f"projects/{project_id}/serviceAccounts/{fixture_name}@", string=sa_id)
    email = fixture_output["email"]
    assert email
    assert re.match(pattern=f"{fixture_name}@", string=email)
    member = fixture_output["member"]
    assert member
    assert re.match(pattern=f"serviceAccount:{fixture_name}@", string=member)


def test_service_account(iam_client: iam_admin_v1.IAMClient, fixture_output: dict[str, Any]) -> None:
    """Verify the service account meets expectations."""
    service_account = iam_client.get_service_account(
        request=iam_admin_v1.GetServiceAccountRequest(
            name=fixture_output["id"],
        ),
    )
    assert service_account
    assert service_account.email == fixture_output["email"]
    assert service_account.display_name == EXPECTED_DISPLAY_NAME
    assert service_account.description == EXPECTED_DESCRIPTION


def test_project_roles(
    projects_client: resourcemanager_v3.ProjectsClient,
    fixture_output: dict[str, Any],
    project_id: str,
) -> None:
    """Verify the service account has expected project roles."""
    sa_member = fixture_output["member"]
    policy = projects_client.get_iam_policy(
        resource=f"projects/{project_id}",
    )
    assert policy
    bindings = policy.bindings
    assert bindings
    assert len(bindings) > 0
    for role in EXPECTED_PROJECT_ROLES:
        sa_bindings = [binding for binding in bindings if binding.role == role]
        assert sa_bindings
        assert len(sa_bindings) == 1
        for binding in sa_bindings:
            assert binding
            assert sa_member in binding.members
