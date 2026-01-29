"""SA module testing fixtures."""

from collections.abc import Callable

import pytest
from google.api_core import exceptions
from google.cloud import artifactregistry_v1, iam_admin_v1

from tests import handle_extended_operation, skip_destroy_phase


@pytest.fixture(scope="session")
def iam_client() -> iam_admin_v1.IAMClient:
    """Return an IAM client."""
    return iam_admin_v1.IAMClient()


@pytest.fixture(scope="session")
def ar_client() -> artifactregistry_v1.ArtifactRegistryClient:
    """Return a AR client."""
    return artifactregistry_v1.ArtifactRegistryClient()


@pytest.fixture(scope="session")
def ar_builder(
    request: pytest.FixtureRequest,
    project_id: str,
    region: str,
    ar_client: artifactregistry_v1.ArtifactRegistryClient,
) -> Callable[[str, str | None, dict[str, str] | None], str]:
    """Return a builder of OCI Artifact Registry resources."""

    def _builder(name: str, description: str | None = None, labels: dict[str, str] | None = None) -> str:
        """Create an OCI Artifact Registry with given name, with automatic deletion after use."""
        assert name
        if description is None:
            description = "Testing GAR for terraform-google-private-gke-cluster."
        if labels is None:
            labels = {}

        def _cleanup() -> None:
            if not skip_destroy_phase():
                handle_extended_operation(
                    ar_client.delete_repository(
                        request=artifactregistry_v1.DeleteRepositoryRequest(
                            name=f"projects/{project_id}/locations/{region}/repositories/{name}",
                        ),
                    ),
                )

        try:
            registry = ar_client.get_repository(
                request=artifactregistry_v1.GetRepositoryRequest(
                    name=f"projects/{project_id}/locations/{region}/repositories/{name}",
                ),
            )
            uri = registry.registry_uri
        except exceptions.NotFound:
            registry = handle_extended_operation(
                ar_client.create_repository(
                    request=artifactregistry_v1.CreateRepositoryRequest(
                        parent=f"projects/{project_id}/locations/{region}",
                        repository_id=name,
                        repository=artifactregistry_v1.Repository(
                            format_="DOCKER",
                            description=description,
                            labels=labels,
                        ),
                    ),
                ),
            )
            assert registry
            uri = registry.registry_uri or f"{region}-docker.pkg.dev/{project_id}/{name}"

        request.addfinalizer(_cleanup)
        return uri

    return _builder
