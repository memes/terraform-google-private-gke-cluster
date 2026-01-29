"""Common testing fixtures."""

import base64
import os
import pathlib
import shutil
import tempfile
from collections.abc import Callable, Generator
from contextlib import contextmanager
from typing import Any, cast

import google.auth
import google.auth.credentials
import google.auth.transport.requests
import kubernetes.client
import pytest
import requests
from google.api_core import exceptions
from google.cloud import compute_v1, container_v1, resourcemanager_v3

from tests import handle_extended_operation, skip_destroy_phase

DEFAULT_PREFIX = "pgke"
DEFAULT_LABELS = {
    "use_case": "automated-tofu-testing",
    "module": "terraform-google-private-gke-cluster",
    "driver": "pytest",
}
DEFAULT_REGION = "us-west1"
DEFAULT_TF_STATE_PREFIX = "tests/terraform-google-private-gke-cluster"


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

    Preference will be given to the environment variable TEST_GOOGLE_REGION with fallback to the default value of
    'us-central1'.
    """
    region = os.getenv("TEST_GOOGLE_REGION", DEFAULT_REGION)
    if region:
        region = region.strip()
    if not region:
        region = DEFAULT_REGION
    assert region
    return region


@pytest.fixture(scope="session")
def tf_state_bucket() -> str:
    """Return the Google Cloud Storage bucket name to use for tofu/terraform state files."""
    bucket = os.getenv("TEST_GOOGLE_TF_STATE_BUCKET")
    if bucket:
        bucket = bucket.strip()
    assert bucket
    return bucket


@pytest.fixture(scope="session")
def tf_state_prefix() -> str:
    """Return the prefix to use for tofu/terraform state files in bucket.

    Preference will be given to the variable TEST_GOOGLE_TF_STATE_PREFIX with fallback to the default value of
    'tests/terraform-google-f5-bigip-ha'.
    """
    prefix = os.getenv("TEST_GOOGLE_TF_STATE_PREFIX", DEFAULT_TF_STATE_PREFIX)
    if prefix:
        prefix = prefix.strip()
    if not prefix:
        prefix = DEFAULT_TF_STATE_PREFIX
    assert prefix
    return prefix


@pytest.fixture(scope="session")
def backend_tf_builder(tf_state_bucket: str, tf_state_prefix: str) -> Callable[[pathlib.Path, str], None]:
    """Create or overwrite a _backend.tf file in the provided fixture_dir that configures GCS backend for state."""

    def _backend_tf(fixture_dir: pathlib.Path, name: str) -> None:
        assert fixture_dir.exists()
        assert name
        fixture_dir.joinpath("_backend.tf").write_text(
            "\n".join(
                [
                    "terraform {",
                    '  backend "gcs" {',
                    f'    bucket = "{tf_state_bucket}"',
                    f'    prefix = "{tf_state_prefix}/{name}"',
                    "  }",
                    "}",
                ],
            ),
        )

    return _backend_tf


@pytest.fixture(scope="session")
def common_fixture_dir_ignores() -> Callable[[Any, list[str]], set[str]]:
    """Return a set of ignore patterns that are unrelated to module sources or supporting files."""
    return shutil.ignore_patterns(".*", "*.md", "*.toml", "uv.lock", "tests")


@pytest.fixture(scope="session")
def root_fixture_dir(
    tmp_path_factory: pytest.TempPathFactory,
    backend_tf_builder: Callable[..., None],
    common_fixture_dir_ignores: Callable[[Any, list[str]], set[str]],
) -> Callable[[str], pathlib.Path]:
    """Return a builder that makes a copy of the root module with backend configured appropriately."""
    root_module_dir = pathlib.Path(__file__).parent.parent.resolve()
    assert root_module_dir.exists()
    assert root_module_dir.is_dir()
    assert root_module_dir.joinpath("main.tf").exists()
    assert root_module_dir.joinpath("outputs.tf").exists()
    assert root_module_dir.joinpath("variables.tf").exists()

    def _builder(name: str) -> pathlib.Path:
        fixture_dir = tmp_path_factory.mktemp(name)
        shutil.copytree(
            src=root_module_dir,
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


@pytest.fixture(scope="session")
def sa_fixture_dir(
    tmp_path_factory: pytest.TempPathFactory,
    backend_tf_builder: Callable[..., None],
    common_fixture_dir_ignores: Callable[[Any, list[str]], set[str]],
) -> Callable[[str], pathlib.Path]:
    """Return a builder that makes a copy of the sa module with backend configured appropriately."""
    sa_module_dir = pathlib.Path(__file__).parent.parent.joinpath("modules/sa").resolve()
    assert sa_module_dir.exists()
    assert sa_module_dir.is_dir()
    assert sa_module_dir.joinpath("main.tf").exists()
    assert sa_module_dir.joinpath("outputs.tf").exists()
    assert sa_module_dir.joinpath("variables.tf").exists()

    def _builder(name: str) -> pathlib.Path:
        fixture_dir = tmp_path_factory.mktemp(name)
        shutil.copytree(
            src=sa_module_dir,
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


@pytest.fixture(scope="session")
def autopilot_fixture_dir(
    tmp_path_factory: pytest.TempPathFactory,
    backend_tf_builder: Callable[..., None],
    common_fixture_dir_ignores: Callable[[Any, list[str]], set[str]],
) -> Callable[[str], pathlib.Path]:
    """Return a builder that makes a copy of the autopilot module with backend configured appropriately."""
    autopilot_module_dir = pathlib.Path(__file__).parent.parent.joinpath("modules/autopilot").resolve()
    assert autopilot_module_dir.exists()
    assert autopilot_module_dir.is_dir()
    assert autopilot_module_dir.joinpath("main.tf").exists()
    assert autopilot_module_dir.joinpath("outputs.tf").exists()
    assert autopilot_module_dir.joinpath("variables.tf").exists()

    def _builder(name: str) -> pathlib.Path:
        fixture_dir = tmp_path_factory.mktemp(name)
        shutil.copytree(
            src=autopilot_module_dir,
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


@pytest.fixture(scope="session")
def kubeconfig_fixture_dir(
    tmp_path_factory: pytest.TempPathFactory,
    backend_tf_builder: Callable[..., None],
    common_fixture_dir_ignores: Callable[[Any, list[str]], set[str]],
) -> Callable[[str], pathlib.Path]:
    """Return a builder that makes a copy of the kubeconfig module with backend configured appropriately."""
    kubeconfig_module_dir = pathlib.Path(__file__).parent.parent.joinpath("modules/kubeconfig").resolve()
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


@pytest.fixture(scope="session")
def projects_client() -> resourcemanager_v3.ProjectsClient:
    """Return a Resource Manager Projects client."""
    return resourcemanager_v3.ProjectsClient()


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


@pytest.fixture(scope="session")
def networks_client() -> compute_v1.NetworksClient:
    """Return an initialized Compute Engine v1 Networks API client."""
    return compute_v1.NetworksClient()


@pytest.fixture(scope="session")
def subnetworks_client() -> compute_v1.SubnetworksClient:
    """Return an initialized Compute Engine v1 Subnetworks API client."""
    return compute_v1.SubnetworksClient()


@pytest.fixture(scope="session")
def network_builder(
    request: pytest.FixtureRequest,
    project_id: str,
    networks_client: compute_v1.NetworksClient,
) -> Callable[[str, str], str]:
    """Return a builder of global VPC networks."""

    def _builder(name: str, description: str | None = None) -> str:
        """Create a VPC network with given name, returning it's self-link, with automatic deletion after use."""
        assert name
        if description is None:
            description = "VPC network for automated BIG-IP HA repo testing."

        def _cleanup() -> None:
            if not skip_destroy_phase():
                handle_extended_operation(
                    networks_client.delete(
                        request=compute_v1.DeleteNetworkRequest(
                            network=name,
                            project=project_id,
                        ),
                    ),
                )

        try:
            network = networks_client.get(
                request=compute_v1.GetNetworkRequest(
                    network=name,
                    project=project_id,
                ),
            )
            self_link = network.self_link
        except exceptions.NotFound:
            handle_extended_operation(
                networks_client.insert(
                    request=compute_v1.InsertNetworkRequest(
                        network_resource=compute_v1.Network(
                            name=name,
                            auto_create_subnetworks=False,
                            description=description,
                        ),
                        project=project_id,
                    ),
                ),
            )
            self_link = f"https://www.googleapis.com/compute/v1/projects/{project_id}/global/networks/{name}"

        request.addfinalizer(_cleanup)
        return self_link

    return _builder


@pytest.fixture(scope="session")
def subnet_builder(
    request: pytest.FixtureRequest,
    project_id: str,
    region: str,
    subnetworks_client: compute_v1.SubnetworksClient,
) -> Callable[[str, str, str | None, dict[str, str] | None, str | None], str]:
    """Return a builder of subnets."""

    def _builder(
        name: str,
        network_self_link: str,
        primary_cidr: str | None = None,
        secondaries: dict[str, str] | None = None,
        description: str | None = None,
    ) -> str:
        """Create a VPC subnetwork with given name, returning it's self-link, with automatic deletion after use."""
        assert name
        assert network_self_link
        if primary_cidr is None:
            primary_cidr = "172.16.0.0/24"
        if not secondaries:
            secondaries = {
                "pods": "10.0.0.0/16",
                "services": "10.100.0.0/20",
            }
        if description is None:
            description = "VPC subnet for automated BIG-IP HA repo testing."

        def _cleanup() -> None:
            if not skip_destroy_phase():
                handle_extended_operation(
                    subnetworks_client.delete(
                        request=compute_v1.DeleteSubnetworkRequest(
                            subnetwork=name,
                            project=project_id,
                            region=region,
                        ),
                    ),
                )

        try:
            subnet = subnetworks_client.get(
                request=compute_v1.GetSubnetworkRequest(
                    subnetwork=name,
                    project=project_id,
                    region=region,
                ),
            )
            self_link = subnet.self_link
        except exceptions.NotFound:
            handle_extended_operation(
                subnetworks_client.insert(
                    request=compute_v1.InsertSubnetworkRequest(
                        subnetwork_resource=compute_v1.Subnetwork(
                            name=name,
                            description=description,
                            network=network_self_link,
                            ip_cidr_range=primary_cidr,
                            region=region,
                            secondary_ip_ranges=[
                                compute_v1.SubnetworkSecondaryRange(
                                    ip_cidr_range=v,
                                    range_name=k,
                                )
                                for k, v in secondaries
                            ],
                        ),
                        project=project_id,
                        region=region,
                    ),
                ),
            )
            self_link = (
                f"https://www.googleapis.com/compute/v1/projects/{project_id}/regions/{region}/subnetworks/{name}"
            )

        request.addfinalizer(_cleanup)
        return self_link

    return _builder


@pytest.fixture(scope="session")
def firewalls_client() -> compute_v1.FirewallsClient:
    """Return a reusable Compute Engine v1 Firewalls Client API client."""
    return compute_v1.FirewallsClient()


@pytest.fixture(scope="session")
def source_cidr() -> str:
    """Return the public IPv4 address of this testing machine, as reported by AWS, to use as testing source CIDR."""
    ip_address = requests.get("https://checkip.amazonaws.com").text.strip()
    assert ip_address
    return f"{ip_address}/32"


@pytest.fixture(scope="session")
def allow_ingress_firewall_builder(
    request: pytest.FixtureRequest,
    project_id: str,
    firewalls_client: compute_v1.FirewallsClient,
    source_cidr: str,
) -> Callable[[str, str], str]:
    """Return a builder of VPC network firewalls that allow ingress to everything from the source address."""

    def _builder(network: str, name: str) -> str:
        """Create a Firewall Rule on the network."""

        def _cleanup() -> None:
            if not skip_destroy_phase():
                firewalls_client.delete(
                    request=compute_v1.DeleteFirewallRequest(
                        firewall=name,
                        project=project_id,
                    ),
                )

        try:
            rule = firewalls_client.get(
                request=compute_v1.GetFirewallRequest(
                    firewall=name,
                    project=project_id,
                ),
            )
        except exceptions.NotFound:
            rule = firewalls_client.insert(
                request=compute_v1.InsertFirewallRequest(
                    firewall_resource=compute_v1.Firewall(
                        name=name,
                        description="Allow ingress from testing workstation",
                        direction="INGRESS",
                        priority=500,
                        network=network,
                        allowed=[
                            compute_v1.Allowed(
                                I_p_protocol="all",
                            ),
                        ],
                        source_ranges=[
                            source_cidr,
                        ],
                    ),
                    project=project_id,
                ),
            )
        request.addfinalizer(_cleanup)
        return rule.self_link

    return _builder
