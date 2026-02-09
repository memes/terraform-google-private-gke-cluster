"""Test fixture for service account module with GAR access."""

import pathlib
import re
from collections.abc import Callable, Generator
from typing import Any

import pytest
from google.cloud import artifactregistry_v1, iam_admin_v1, resourcemanager_v3

from tests import run_tf_plan_apply_destroy

FIXTURE_NAME = "sa-gar"
FIXTURE_LABELS = {
    "fixture": FIXTURE_NAME,
}
EXPECTED_DISPLAY_NAME = "A test account with GAR access"
EXPECTED_DESCRIPTION = "A test account with GAR access provisioned by pytest and tofu just for unit testing purposes"
EXPECTED_PROJECT_ROLES = [
    "roles/container.defaultNodeServiceAccount",
    "roles/stackdriver.resourceMetadata.writer",
]


@pytest.fixture(scope="module")
def fixture_name(prefix: str) -> str:
    """Return the name to use for resources in this module."""
    return f"{prefix}-{FIXTURE_NAME}"


@pytest.fixture(scope="module")
def fixture_labels(labels: dict[str, str]) -> dict[str, str]:
    """Return a dict of labels for this test module."""
    return FIXTURE_LABELS | labels


@pytest.fixture(scope="module")
def fixture_output(
    sa_fixture_dir: Callable[[str], pathlib.Path],
    project_id: str,
    fixture_name: str,
    ar_repo: str,
) -> Generator[dict[str, Any], None, None]:
    """Create service account for test case."""
    assert ar_repo
    with run_tf_plan_apply_destroy(
        fixture=sa_fixture_dir(FIXTURE_NAME),
        tfvars={
            "project_id": project_id,
            "name": fixture_name,
            "display_name": EXPECTED_DISPLAY_NAME,
            "description": EXPECTED_DESCRIPTION,
            "repositories": [
                ar_repo,
            ],
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


def test_service_account(iam_admin_client: iam_admin_v1.IAMClient, fixture_output: dict[str, Any]) -> None:
    """Verify the service account meets expectations."""
    service_account = iam_admin_client.get_service_account(
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


def test_ar_roles(
    ar_client: artifactregistry_v1.ArtifactRegistryClient,
    fixture_output: dict[str, Any],
    ar_repo: str,
) -> None:
    """Verify the service account has expected project roles."""
    assert ar_repo
    sa_member = fixture_output["member"]
    repo_components = re.match(
        r"^(?P<location>[a-z]{2,}(?:-[a-z]+[1-9])?)-docker\.pkg\.dev/(?P<project>[^/]+)/(?P<repository>[^/]+)",
        ar_repo,
    )
    assert repo_components
    repo_components = repo_components.groupdict()
    policy = ar_client.get_iam_policy(
        request={
            "resource": ar_client.repository_path(
                project=repo_components["project"],
                location=repo_components["location"],
                repository=repo_components["repository"],
            ),
        },
    )
    assert policy
    bindings = policy.bindings
    assert bindings
    assert len(bindings) > 0
    reader_bindings = [binding for binding in bindings if binding.role == "roles/artifactregistry.reader"]
    assert reader_bindings
    assert len(reader_bindings) == 1
    for binding in reader_bindings:
        assert binding
        assert sa_member in binding.members
