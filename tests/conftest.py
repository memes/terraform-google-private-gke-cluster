"""Common testing fixtures."""

import os
import pathlib
import random
import re
import shutil
from collections.abc import Callable, Generator
from typing import Any

import google.auth
import google.auth.credentials
import pytest
import requests
from google.api_core import exceptions
from google.cloud import artifactregistry_v1, compute_v1, container_v1, iam_admin_v1, resourcemanager_v3

from tests import handle_extended_operation, handle_operation, skip_destroy_phase

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
                                for k, v in secondaries.items()
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


@pytest.fixture(scope="session")
def ar_client() -> artifactregistry_v1.ArtifactRegistryClient:
    """Return a AR client."""
    return artifactregistry_v1.ArtifactRegistryClient()


@pytest.fixture(scope="session")
def ar_repo(
    prefix: str,
    project_id: str,
    region: str,
    labels: dict[str, str],
    ar_client: artifactregistry_v1.ArtifactRegistryClient,
) -> Generator[str, None, None]:
    """Create an OCI Artifact Registry for test cases."""
    name = f"{prefix}-common"
    try:
        registry = ar_client.get_repository(
            request=artifactregistry_v1.GetRepositoryRequest(
                name=f"projects/{project_id}/locations/{region}/repositories/{name}",
            ),
        )
        uri = registry.registry_uri
    except exceptions.NotFound:
        registry = handle_operation(
            ar_client.create_repository(
                request=artifactregistry_v1.CreateRepositoryRequest(
                    parent=f"projects/{project_id}/locations/{region}",
                    repository_id=name,
                    repository=artifactregistry_v1.Repository(
                        format_="DOCKER",
                        description="OCI Artifact Registry for terraform-google-private-gke-cluster testing",
                        labels=labels,
                    ),
                ),
            ),
        )
        assert registry
        uri = registry.registry_uri or f"{region}-docker.pkg.dev/{project_id}/{name}"
    yield uri
    if not skip_destroy_phase():
        handle_operation(
            ar_client.delete_repository(
                request=artifactregistry_v1.DeleteRepositoryRequest(
                    name=f"projects/{project_id}/locations/{region}/repositories/{name}",
                ),
            ),
        )


@pytest.fixture(scope="session")
def instances_client() -> compute_v1.InstancesClient:
    """Return a reusable Compute Engine v1 Instances API client."""
    return compute_v1.InstancesClient()


@pytest.fixture(scope="session")
def regions_client() -> compute_v1.RegionsClient:
    """Return a reusable Compute Engine v2 Regions API client."""
    return compute_v1.RegionsClient()


@pytest.fixture(scope="session")
def shuffled_zones(
    pytestconfig: pytest.Config,
    project_id: str,
    region: str,
    regions_client: compute_v1.RegionsClient,
) -> Generator[list[str], None, None]:
    """Return a list of Compute Engine zone names."""
    cache_key = f"terraform-google-private-gke-cluster/zones-{region}"
    zones = pytestconfig.cache.get(cache_key, None)
    if zones is None:
        result = regions_client.get(
            request=compute_v1.GetRegionRequest(
                project=project_id,
                region=region,
            ),
        )
        zones = random.sample([zone.split("/")[-1] for zone in result.zones], len(result.zones))
        pytestconfig.cache.set(cache_key, zones)
    yield zones
    if not skip_destroy_phase():
        pytestconfig.cache.set(cache_key, None)


@pytest.fixture(scope="session")
def iam_admin_client() -> iam_admin_v1.IAMClient:
    """Return an initialized IAM Admin v1 client."""
    return iam_admin_v1.IAMClient()


@pytest.fixture(scope="session")
def service_account_builder(
    request: pytest.FixtureRequest,
    project_id: str,
    iam_admin_client: iam_admin_v1.IAMClient,
) -> Callable[[str, str, str], str]:
    """Return a builder of service accounts."""

    def _builder(
        name: str,
        display_name: str | None = None,
        description: str | None = None,
    ) -> str:
        """Create a service account with given name, returning it's email address, with automatic deletion after use."""
        if display_name is None:
            display_name = "terraform-google-private-gke-cluster test account"
        if description is None:
            description = "A test service account for automated GKE testing."

        def _cleanup() -> None:
            if not skip_destroy_phase():
                iam_admin_client.delete_service_account(
                    request=iam_admin_v1.DeleteServiceAccountRequest(
                        name=sa.name,
                    ),
                )

        try:
            sa_accounts = iam_admin_client.list_service_accounts(
                name=f"projects/{project_id}",
            )
            sa = next(sa for sa in sa_accounts if re.search(f"serviceAccounts/{name}", sa.name))
        except (StopIteration, exceptions.NotFound):
            sa = iam_admin_client.create_service_account(
                request=iam_admin_v1.CreateServiceAccountRequest(
                    account_id=name,
                    name=f"projects/{project_id}",
                    service_account=iam_admin_v1.ServiceAccount(
                        display_name=display_name,
                        description=description,
                    ),
                ),
            )
        request.addfinalizer(_cleanup)
        return sa.email

    return _builder


@pytest.fixture(scope="session")
def bastion_builder(
    request: pytest.FixtureRequest,
    project_id: str,
    shuffled_zones: list[str],
    instances_client: compute_v1.InstancesClient,
) -> Callable[[str, str, str, str | None, str | None, dict[str, str] | None], compute_v1.Instance]:
    """Return a builder of Bastion instances."""

    def _builder(
        name: str,
        subnet: str,
        sa_email: str,
        zone: str | None = None,
        description: str | None = None,
        labels: dict[str, str] | None = None,
    ) -> compute_v1.Instance:
        """Create a bastion instance with given name with NAT'd public IP."""
        if description is None:
            description = "Bastion instance for terraform-google-private-gke-cluster test case."
        if labels is None:
            labels = {}
        if zone is None:
            zone = shuffled_zones[0]

        def _cleanup() -> None:
            if not skip_destroy_phase():
                handle_extended_operation(
                    instances_client.delete(
                        request=compute_v1.DeleteInstanceRequest(
                            instance=name,
                            project=project_id,
                            zone=zone,
                        ),
                    ),
                )

        try:
            instance = instances_client.get(
                request=compute_v1.GetInstanceRequest(
                    instance=name,
                    project=project_id,
                    zone=zone,
                ),
            )
        except exceptions.NotFound:
            handle_extended_operation(
                instances_client.insert(
                    request=compute_v1.InsertInstanceRequest(
                        instance_resource=compute_v1.Instance(
                            name=name,
                            description=description,
                            deletion_protection=False,
                            disks=[
                                compute_v1.AttachedDisk(
                                    auto_delete=True,
                                    boot=True,
                                    initialize_params=compute_v1.AttachedDiskInitializeParams(
                                        description=f"{name} boot disk",
                                        disk_size_gb=20,
                                        disk_type=f"projects/{project_id}/zones/{zone}/diskTypes/pd-standard",
                                        labels=labels,
                                        source_image="projects/confidential-vm-images/global/images/family/cos-stable",
                                    ),
                                    mode="READ_WRITE",
                                ),
                            ],
                            network_interfaces=[
                                compute_v1.NetworkInterface(
                                    access_configs=[
                                        compute_v1.AccessConfig(
                                            type_="ONE_TO_ONE_NAT",
                                        ),
                                    ],
                                    nic_type="VIRTIO_NET",
                                    subnetwork=subnet,
                                ),
                            ],
                            service_accounts=[
                                compute_v1.ServiceAccount(
                                    email=sa_email,
                                    scopes=[
                                        "https://www.googleapis.com/auth/cloud-platform",
                                    ],
                                ),
                            ],
                            labels=labels,
                            machine_type=f"zones/{zone}/machineTypes/e2-medium",
                            metadata=compute_v1.Metadata(
                                items=[
                                    compute_v1.Items(key="enable-oslogin", value="TRUE"),
                                    compute_v1.Items(
                                        key="user-data",
                                        value="""#cloud-config
# Launches a forward-proxy container from a (private) repo on boot.
---
write_files:
  - path: /etc/systemd/system/forward-proxy.service
    permissions: '0o644'
    owner: root:root
    content: |
      [Unit]
      Description=Launch a forward-proxy in a container
      After=network-online.target
      FailureAction=none
      StartLimitIntervalSec=10
      StartLimitBurst=5

      [Service]
      Type=simple
      Environment="HOME=/var/run/forward-proxy"
      ExecStart=/usr/bin/docker run --rm --publish 8888:8888/tcp --name forward-proxy ghcr.io/memes/terraform-google-private-bastion/forward-proxy:4.0.1
      ExecStop=/usr/bin/docker stop forward-proxy
      ExecStopPost=/usr/bin/docker rm forward-proxy
      RestartSec=1
      Restart=on-failure

      [Install]
      WantedBy=multi-user.target

runcmd:
  - systemctl daemon-reload
  - systemctl enable --now forward-proxy

""",  # noqa: E501
                                    ),
                                ],
                            ),
                        ),
                        project=project_id,
                        zone=zone,
                    ),
                ),
            )
            instance = instances_client.get(
                request=compute_v1.GetInstanceRequest(
                    instance=name,
                    project=project_id,
                    zone=zone,
                ),
            )

        request.addfinalizer(_cleanup)
        return instance

    return _builder
