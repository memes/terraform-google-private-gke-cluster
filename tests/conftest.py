"""Common testing fixtures."""

import base64
import json
import os
import pathlib
import subprocess
import tempfile
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any, cast

import google.auth
import google.auth.credentials
import google.auth.transport.requests
import kubernetes.client
import pytest
from google.cloud import artifactregistry_v1, container_v1, iam_admin_v1, resourcemanager_v3

DEFAULT_PREFIX = "pgke"
DEFAULT_LABELS = {
    "use_case": "automated-tofu-testing",
    "module": "terraform-google-private-gke-cluster",
    "driver": "pytest",
}
DEFAULT_REGION = "us-west1"


@pytest.fixture(scope="session")
def prefix() -> str:
    """Return the prefix to use for test resources.

    Preference will be given to the environment variable TEST_PREFIX with default value of 'pgke'.
    """
    prefix = os.getenv("TEST_PREFIX", DEFAULT_PREFIX)
    if prefix:
        prefix = prefix.strip()
    if not prefix:
        prefix = DEFAULT_PREFIX
    assert prefix
    return prefix


@pytest.fixture(scope="session")
def project_id() -> str:
    """Return the project id to use for tests.

    Preference will be given to the environment variables TEST_GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_PROJECT followed by
    the default project identifier associated with local ADC credentials.
    """
    project_id = os.getenv("TEST_GOOGLE_CLOUD_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
    if project_id:
        project_id = project_id.strip()
    if not project_id:
        _, project_id = google.auth.default()
    assert project_id
    return project_id


@pytest.fixture(scope="session")
def labels() -> dict[str, str]:
    """Return a dict of labels to apply to resources from environment variable TEST_GOOGLE_LABELS.

    If the environment variable TEST_GOOGLE_LABELS is not empty and can be parsed as a comma-separated list of key:value
    pairs then return a dict of keys to values.
    """
    raw = os.getenv("TEST_GOOGLE_LABELS")
    if not raw:
        return DEFAULT_LABELS
    return DEFAULT_LABELS | dict([x.split(":") for x in raw.split(",")])


@pytest.fixture(scope="session")
def region() -> str:
    """Return the Compute Engine region to use for tests.

    Preference will be given to the environment variables TEST_GOOGLE_REGION with fallback to 'us-west1'.
    """
    region = os.getenv("TEST_GOOGLE_REGION", DEFAULT_REGION)
    if region:
        region = region.strip()
    if not region:
        region = DEFAULT_REGION
    assert region
    return region


@pytest.fixture(scope="session")
def root_fixture_dir() -> pathlib.Path:
    """Return the fully-qualified directory at the fixture to exercise the root module."""
    root_fixture_dir = pathlib.Path(__file__).parent.joinpath("fixtures/root").resolve()
    assert root_fixture_dir.exists()
    assert root_fixture_dir.is_dir()
    assert root_fixture_dir.joinpath("main.tf").exists()
    assert root_fixture_dir.joinpath("outputs.tf").exists()
    assert root_fixture_dir.joinpath("variables.tf").exists()
    return root_fixture_dir


@pytest.fixture(scope="session")
def sa_fixture_dir() -> pathlib.Path:
    """Return the fully-qualified directory at the fixture to exercise the sa module."""
    sa_fixture_dir = pathlib.Path(__file__).parent.joinpath("fixtures/sa").resolve()
    assert sa_fixture_dir.exists()
    assert sa_fixture_dir.is_dir()
    assert sa_fixture_dir.joinpath("main.tf").exists()
    assert sa_fixture_dir.joinpath("outputs.tf").exists()
    assert sa_fixture_dir.joinpath("variables.tf").exists()
    return sa_fixture_dir


@pytest.fixture(scope="session")
def autopilot_fixture_dir() -> pathlib.Path:
    """Return the fully-qualified directory at the fixture to exercise the autopilot module."""
    autopilot_fixture_dir = pathlib.Path(__file__).parent.joinpath("fixtures/autopilot").resolve()
    assert autopilot_fixture_dir.exists()
    assert autopilot_fixture_dir.is_dir()
    assert autopilot_fixture_dir.joinpath("main.tf").exists()
    assert autopilot_fixture_dir.joinpath("outputs.tf").exists()
    assert autopilot_fixture_dir.joinpath("variables.tf").exists()
    return autopilot_fixture_dir


@pytest.fixture(scope="session")
def gar_fixture_dir() -> pathlib.Path:
    """Return the fully-qualified directory at the fixture to create a testing GAR module."""
    gar_fixture_dir = pathlib.Path(__file__).parent.joinpath("fixtures/gar").resolve()
    assert gar_fixture_dir.exists()
    assert gar_fixture_dir.is_dir()
    assert gar_fixture_dir.joinpath("main.tf").exists()
    assert gar_fixture_dir.joinpath("outputs.tf").exists()
    assert gar_fixture_dir.joinpath("variables.tf").exists()
    return gar_fixture_dir


@pytest.fixture(scope="session")
def vpc_fixture_dir() -> pathlib.Path:
    """Return the fully-qualified directory at the fixture to create a testing VPC module."""
    vpc_fixture_dir = pathlib.Path(__file__).parent.joinpath("fixtures/vpc").resolve()
    assert vpc_fixture_dir.exists()
    assert vpc_fixture_dir.is_dir()
    assert vpc_fixture_dir.joinpath("main.tf").exists()
    assert vpc_fixture_dir.joinpath("outputs.tf").exists()
    assert vpc_fixture_dir.joinpath("variables.tf").exists()
    return vpc_fixture_dir


@pytest.fixture(scope="session")
def kubeconfig_fixture_dir() -> pathlib.Path:
    """Return the fully-qualified directory at the fixture to create a testing kubeconfig module."""
    kubeconfig_fixture_dir = pathlib.Path(__file__).parent.joinpath("fixtures/kubeconfig").resolve()
    assert kubeconfig_fixture_dir.exists()
    assert kubeconfig_fixture_dir.is_dir()
    assert kubeconfig_fixture_dir.joinpath("main.tf").exists()
    assert kubeconfig_fixture_dir.joinpath("outputs.tf").exists()
    assert kubeconfig_fixture_dir.joinpath("variables.tf").exists()
    return kubeconfig_fixture_dir


def skip_destroy_phase() -> bool:
    """Determine if tofu destroy phase should be skipped for successful fixtures."""
    return os.getenv("TEST_SKIP_DESTROY_PHASE", "False").lower() in ["true", "t", "yes", "y", "1"]


@contextmanager
def run_tofu_in_workspace(
    fixture: pathlib.Path,
    workspace: str | None,
    tfvars: dict[str, Any] | None,
) -> Generator[dict[str, Any], None, None]:
    """Execute tofu init/apply/destroy lifecycle for a fixture in an optional workspace, yielding the output post-apply.

    NOTE: Resources will not be destroyed if the test case raises an error.
    """
    if tfvars is None:
        tfvars = {}
    tf_command = os.getenv("TEST_TF_COMMAND", "tofu")
    if workspace is not None and workspace != "":
        subprocess.run(
            [
                tf_command,
                f"-chdir={fixture!s}",
                "workspace",
                "select",
                "-or-create",
                workspace,
            ],
            check=True,
            capture_output=True,
        )
    subprocess.run(
        [
            tf_command,
            f"-chdir={fixture!s}",
            "init",
            "-no-color",
        ],
        check=True,
        capture_output=True,
    )
    with tempfile.NamedTemporaryFile(
        mode="w",
        prefix="tfvars",
        suffix=".json",
        encoding="utf-8",
        delete_on_close=False,
        delete=True,
    ) as tfvar_file:
        json.dump(tfvars, tfvar_file, ensure_ascii=False, indent=2)
        tfvar_file.close()
        subprocess.run(
            [
                tf_command,
                f"-chdir={fixture!s}",
                "apply",
                "-no-color",
                "-auto-approve",
                f"-var-file={tfvar_file.name}",
            ],
            check=True,
            capture_output=True,
        )
        output = subprocess.run(
            [
                tf_command,
                f"-chdir={fixture!s}",
                "output",
                "-no-color",
                "-json",
            ],
            check=True,
            capture_output=True,
        )
        try:
            yield {k: v["value"] for k, v in json.loads(output.stdout).items()}
            if not skip_destroy_phase():
                subprocess.run(
                    [
                        tf_command,
                        f"-chdir={fixture!s}",
                        "destroy",
                        "-no-color",
                        "-auto-approve",
                        f"-var-file={tfvar_file.name}",
                    ],
                    check=True,
                    capture_output=True,
                )
        finally:
            subprocess.run(
                [
                    tf_command,
                    f"-chdir={fixture!s}",
                    "workspace",
                    "select",
                    "default",
                ],
                check=True,
                capture_output=True,
            )


@pytest.fixture(scope="session")
def iam_client() -> iam_admin_v1.IAMClient:
    """Return an IAM client."""
    return iam_admin_v1.IAMClient()


@pytest.fixture(scope="session")
def projects_client() -> resourcemanager_v3.ProjectsClient:
    """Return a Resource Manager Projects client."""
    return resourcemanager_v3.ProjectsClient()


@pytest.fixture(scope="session")
def gar_client() -> artifactregistry_v1.ArtifactRegistryClient:
    """Return a GAR client."""
    return artifactregistry_v1.ArtifactRegistryClient()


@pytest.fixture(scope="session")
def cluster_manager_client() -> container_v1.ClusterManagerClient:
    """Return a Cluster Manager client."""
    return container_v1.ClusterManagerClient()


@contextmanager
def kubernetes_api_client(
    host: str,
    ca: str,
    proxy_url: str | None = None,
) -> Generator[kubernetes.client.ApiClient, None, None]:
    """Yield a configured API client built from GKE parameters.

    NOTE: API client expects CA certificate to be passed as a file, so this will create a temporary file that will be
    destroyed after the API client is released.
    """
    credentials, _ = google.auth.default()
    credentials = cast("google.auth.credentials.Credentials", credentials)
    request = google.auth.transport.requests.Request()
    credentials.refresh(request)
    with tempfile.NamedTemporaryFile(
        mode="w+b",
        prefix="ca",
        suffix=".pem",
        delete_on_close=False,
        delete=True,
    ) as ca_cert_file:
        ca_cert_file.write(base64.standard_b64decode(ca))
        ca_cert_file.close()
        config = kubernetes.client.Configuration(
            host=host,
            api_key_prefix={
                "authorization": "Bearer",
            },
            api_key={
                "authorization": credentials.token,
            },
        )
        config.ssl_ca_cert = ca_cert_file.name  # pyright: ignore[reportAttributeAccessIssue]
        config.verify_ssl = True
        if proxy_url:
            config.proxy = proxy_url  # pyright: ignore[reportAttributeAccessIssue]
        client = kubernetes.client.ApiClient(configuration=config)
        assert client
        yield client
