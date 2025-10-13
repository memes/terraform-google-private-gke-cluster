"""Test fixture for Autopilot GKE cluster with NAP configuration."""

import base64
import ipaddress
import pathlib
import urllib.parse
from collections import Counter
from collections.abc import Generator
from typing import Any, cast

import pytest
from cryptography import x509
from google.cloud import container_v1

from .conftest import kubernetes_api_client, run_tofu_in_workspace
from .gke_autopilot_assertions import (
    assert_anonymous_authentication_config,
    assert_compliance_posture_config,
    assert_default_addons_config,
    assert_default_authenticator_groups_config,
    assert_default_autopilot,
    assert_default_binary_authorization,
    assert_default_cluster_autoscaling,
    assert_default_cluster_config,
    assert_default_confidential_nodes,
    assert_default_control_plane_endpoints_config,
    assert_default_cost_management_config,
    assert_default_database_encryption,
    assert_default_dns_config,
    assert_default_fleet,
    assert_default_identity_service_config,
    assert_default_ip_allocation_policy,
    assert_default_legacy_abac,
    assert_default_logging_config,
    assert_default_maintenance_policy,
    assert_default_master_auth,
    assert_default_mesh_certificates,
    assert_default_monitoring_config,
    assert_default_network_config,
    assert_default_network_policy,
    assert_default_node_pool_defaults,
    assert_default_node_pools,
    assert_default_notification_config,
    assert_default_pod_autoscaling,
    assert_default_release_channel,
    assert_default_resource_labels,
    assert_default_resource_usage_export_config,
    assert_default_security_posture_config,
    assert_default_shielded_nodes,
    assert_default_vertical_pod_autoscaling,
    assert_default_workload_identity_config,
    assert_enable_k8s_beta_apis,
    assert_enterprise_config,
    assert_gke_auto_upgrade_config,
    assert_rbac_binding_config,
    assert_secret_manager_config,
    assert_user_managed_keys_config,
)
from .kubernetes_assertions import (
    assert_any_labelled_service_exists,
    assert_namespace,
)

FIXTURE_NAME = "auto-nap"
FIXTURE_LABELS = {
    "fixture": FIXTURE_NAME,
}


@pytest.fixture(scope="module")
def fixture_name(prefix: str) -> str:
    """Return the name to use for resources in this module."""
    return f"{prefix}-{FIXTURE_NAME}"


@pytest.fixture(scope="module")
def fixture_labels(labels: dict[str, str]) -> dict[str, str]:
    """Return a dict of labels for this test module."""
    return FIXTURE_LABELS | labels


@pytest.fixture(scope="module")
def sa_fixture_output(
    sa_fixture_dir: pathlib.Path,
    project_id: str,
    fixture_name: str,
) -> Generator[dict[str, Any], None, None]:
    """Create a service account for the test case."""
    with run_tofu_in_workspace(
        fixture=sa_fixture_dir,
        workspace=FIXTURE_NAME,
        tfvars={
            "project_id": project_id,
            "name": fixture_name,
        },
    ) as output:
        yield output


@pytest.fixture(scope="module")
def vpc_fixture_output(
    vpc_fixture_dir: pathlib.Path,
    project_id: str,
    fixture_name: str,
    region: str,
    fixture_labels: dict[str, str],
) -> Generator[dict[str, Any], None, None]:
    """Create a VPC and bastion for the test case."""
    with run_tofu_in_workspace(
        fixture=vpc_fixture_dir,
        workspace=FIXTURE_NAME,
        tfvars={
            "project_id": project_id,
            "name": fixture_name,
            "region": region,
            "labels": fixture_labels,
            "nap": {
                "tags": [
                    fixture_name,
                ],
            },
        },
    ) as output:
        yield output


@pytest.fixture(scope="module")
def fixture_output(
    autopilot_fixture_dir: pathlib.Path,
    project_id: str,
    fixture_name: str,
    fixture_labels: dict[str, str],
    sa_fixture_output: dict[str, Any],
    vpc_fixture_output: dict[str, Any],
) -> Generator[dict[str, Any], None, None]:
    """Create GKE Autopilot cluster for test case."""
    service_account = cast("str", sa_fixture_output["email"])
    assert service_account
    subnet = cast("dict[str, str]", vpc_fixture_output["subnet"])
    assert subnet
    bastion_ip_address = vpc_fixture_output["bastion_ip_address"]
    assert bastion_ip_address
    with run_tofu_in_workspace(
        fixture=autopilot_fixture_dir,
        workspace=FIXTURE_NAME,
        tfvars={
            "project_id": project_id,
            "name": fixture_name,
            "service_account": service_account,
            "subnet": subnet,
            "master_authorized_networks": [
                {
                    "cidr_block": f"{bastion_ip_address}/32",
                    "display_name": "bastion",
                },
            ],
            "labels": fixture_labels,
            "nap": {
                "tags": [
                    fixture_name,
                ],
            },
        },
    ) as output:
        yield output


@pytest.fixture(scope="module")
def cluster(
    fixture_output: dict[str, Any],
    cluster_manager_client: container_v1.ClusterManagerClient,
) -> container_v1.Cluster:
    """Return the GKE Cluster object matching the fixture output."""
    cluster_id = fixture_output["id"]
    assert cluster_id
    cluster = cluster_manager_client.get_cluster(
        request=container_v1.GetClusterRequest(
            name=cluster_id,
        ),
    )
    assert cluster
    return cluster


@pytest.fixture(scope="module")
def network_self_link(vpc_fixture_output: dict[str, Any]) -> str:
    """Return the VPC network self-link for test fixture."""
    network_self_link = cast("str", vpc_fixture_output.get("self_link"))
    assert network_self_link
    return network_self_link


@pytest.fixture(scope="module")
def subnet_self_link(vpc_fixture_output: dict[str, Any]) -> str:
    """Return the VPC subnet self-link for test fixture."""
    subnet = cast("dict[str, str]", vpc_fixture_output["subnet"])
    assert subnet
    return subnet["self_link"]


@pytest.fixture(scope="module")
def pods_range_name(vpc_fixture_output: dict[str, Any]) -> str:
    """Return the VPC subnet secondary range name to use for pods/cluster in test fixture."""
    subnet = cast("dict[str, str]", vpc_fixture_output["subnet"])
    assert subnet
    return subnet["pods_range_name"]


@pytest.fixture(scope="module")
def services_range_name(vpc_fixture_output: dict[str, Any]) -> str:
    """Return the VPC subnet secondary range name to use for services in test fixture."""
    subnet = cast("dict[str, str]", vpc_fixture_output["subnet"])
    assert subnet
    return subnet["services_range_name"]


@pytest.fixture(scope="module")
def service_account(sa_fixture_output: dict[str, Any]) -> str:
    """Return the email address of the service account for this test fixture."""
    service_account = cast("str", sa_fixture_output["email"])
    assert service_account
    return service_account


def test_output_values(fixture_output: dict[str, Any], project_id: str, region: str, fixture_name: str) -> None:
    """Verify the fixture output meets expectations."""
    cluster_id = fixture_output["id"]
    assert cluster_id
    assert cluster_id == f"projects/{project_id}/locations/{region}/clusters/{fixture_name}"
    name = fixture_output["name"]
    assert name
    assert name == fixture_name
    location = fixture_output["location"]
    assert location
    assert location == region
    ca_cert_b64 = cast("str", fixture_output["ca_cert"])
    assert ca_cert_b64
    ca_cert_raw = base64.standard_b64decode(ca_cert_b64)
    ca_cert = x509.load_pem_x509_certificate(data=ca_cert_raw)
    assert ca_cert
    endpoint_url = fixture_output["endpoint_url"]
    assert endpoint_url
    url = urllib.parse.urlparse(endpoint_url)
    assert url
    assert url.scheme == "https"
    assert not url.port
    address = ipaddress.IPv4Address(url.hostname)
    assert address
    assert address.is_private
    assert "public_endpoint_url" not in fixture_output


def test_base_config(
    cluster: container_v1.Cluster,
    fixture_name: str,
    network_self_link: str,
    subnet_self_link: str,
) -> None:
    """Verify the GKE cluster base configuration meets expectations."""
    assert_default_cluster_config(
        cluster=cluster,
        expected_name=fixture_name,
        network=network_self_link,
        subnet=subnet_self_link,
    )


def test_master_auth(cluster: container_v1.Cluster) -> None:
    """Verify the GKE cluster master authentication configuration meets expectations."""
    assert_default_master_auth(cluster.master_auth)


def test_addons_config(cluster: container_v1.Cluster) -> None:
    """Verify the GKE cluster addons configuration meets expectations."""
    assert_default_addons_config(cluster.addons_config)


def test_node_pools(cluster: container_v1.Cluster) -> None:
    """Verify the cluster node pools meet expectations."""
    assert_default_node_pools(cluster.node_pools)


def test_resource_labels(cluster: container_v1.Cluster, fixture_labels: dict[str, str]) -> None:
    """Verify the GKE cluster resource labels configuration meets expectations."""
    assert_default_resource_labels(resource_labels=cluster.resource_labels, expected_labels=fixture_labels)


def test_legacy_abac_config(cluster: container_v1.Cluster) -> None:
    """Verify the GKE cluster legacy ABAC configuration meets expectations."""
    assert_default_legacy_abac(cluster.legacy_abac)


def test_network_policy_config(cluster: container_v1.Cluster) -> None:
    """Verify the GKE cluster addons configuration meets expectations."""
    assert_default_network_policy(cluster.network_policy)


def test_default_ip_allocation_policy(
    cluster: container_v1.Cluster,
    pods_range_name: str,
    services_range_name: str,
) -> None:
    """Verify the GKE cluster IP allocation policy meets expectations."""
    assert_default_ip_allocation_policy(
        cluster.ip_allocation_policy,
        cluster_range_name=pods_range_name,
        services_range_name=services_range_name,
    )


def test_maintenance_policy(cluster: container_v1.Cluster) -> None:
    """Verify the GKE cluster maintenance policy meets expectations."""
    assert_default_maintenance_policy(cluster.maintenance_policy)


def test_binary_authorization(cluster: container_v1.Cluster) -> None:
    """Verify the GKE cluster binary_authorization configuration meets expectations."""
    assert_default_binary_authorization(cluster.binary_authorization)


def test_cluster_autoscaling_config(cluster: container_v1.Cluster, service_account: str) -> None:
    """Verify the GKE cluster autoscaling configuration meets expectations."""
    assert_default_cluster_autoscaling(
        cluster_autoscaling=cluster.autoscaling,
        service_account=service_account,
    )


def test_default_network_config(cluster: container_v1.Cluster, network_self_link: str, subnet_self_link: str) -> None:
    """Verify the GKE cluster default network configuration meets expectations."""
    assert_default_network_config(
        network_config=cluster.network_config,
        network=network_self_link,
        subnet=subnet_self_link,
    )


def test_resource_usage_export_config(cluster: container_v1.Cluster) -> None:
    """Verify the GKE cluster resource usage export configuration meets expectations."""
    assert_default_resource_usage_export_config(cluster.resource_usage_export_config)


def test_authenticator_groups_config(cluster: container_v1.Cluster) -> None:
    """Verify the GKE cluster authenticator groups configuration meets expectations."""
    assert_default_authenticator_groups_config(cluster.authenticator_groups_config)


def test_database_encryption(cluster: container_v1.Cluster) -> None:
    """Verify the GKE cluster database encryption meets expectations."""
    assert_default_database_encryption(cluster.database_encryption)


def test_vertical_pod_autoscaling(cluster: container_v1.Cluster) -> None:
    """Verify the GKE cluster vertical pod autoscaling meets expectations."""
    assert_default_vertical_pod_autoscaling(cluster.vertical_pod_autoscaling)


def test_shielded_nodes(cluster: container_v1.Cluster) -> None:
    """Verify the GKE cluster shielded nodes config meets expectations."""
    assert_default_shielded_nodes(cluster.shielded_nodes)


def test_release_channel(cluster: container_v1.Cluster) -> None:
    """Verify the GKE cluster master authentication configuration meets expectations."""
    assert_default_release_channel(cluster.release_channel)


def test_workload_identity_config(cluster: container_v1.Cluster, project_id: str) -> None:
    """Verify the GKE cluster workload identity config meets expectations."""
    assert_default_workload_identity_config(
        workload_identity_config=cluster.workload_identity_config,
        project_id=project_id,
    )


def test_mesh_certificates(cluster: container_v1.Cluster) -> None:
    """Verify the GKE cluster mesh certificates config meets expectations."""
    assert_default_mesh_certificates(cluster.mesh_certificates)


def test_cost_management_config(cluster: container_v1.Cluster) -> None:
    """Verify the GKE cluster cost management config meets expectations."""
    assert_default_cost_management_config(cluster.cost_management_config)


def test_notification_config(cluster: container_v1.Cluster) -> None:
    """Verify the GKE cluster notification config meets expectations."""
    assert_default_notification_config(cluster.notification_config)


def test_confidential_nodes(cluster: container_v1.Cluster) -> None:
    """Verify the GKE cluster confidential nodes config meets expectations."""
    assert_default_confidential_nodes(cluster.confidential_nodes)


def test_identity_service_config(cluster: container_v1.Cluster) -> None:
    """Verify the GKE cluster identity service config meets expectations."""
    assert_default_identity_service_config(cluster.identity_service_config)


def test_autopilot(cluster: container_v1.Cluster) -> None:
    """Verify the GKE cluster autopilot config meets expectations."""
    assert_default_autopilot(cluster.autopilot)


def test_node_pool_defaults(cluster: container_v1.Cluster) -> None:
    """Verify the GKE cluster node pool defaults meets expectations."""
    assert_default_node_pool_defaults(cluster.node_pool_defaults)


def test_logging_config(cluster: container_v1.Cluster) -> None:
    """Verify the GKE cluster logging config meets expectations."""
    assert_default_logging_config(cluster.logging_config)


def test_monitoring_config(cluster: container_v1.Cluster) -> None:
    """Verify the GKE cluster monitoring config meets expectations."""
    assert_default_monitoring_config(cluster.monitoring_config)


def test_node_pool_auto_config(cluster: container_v1.Cluster, fixture_name: str) -> None:
    """Verify the GKE cluster node pool auto config meets expectations."""
    node_pool_auto_config = cluster.node_pool_auto_config
    assert node_pool_auto_config is not None
    assert node_pool_auto_config.network_tags is not None
    expected_tags = [
        fixture_name,
    ]
    assert Counter(node_pool_auto_config.network_tags.tags) == Counter(expected_tags)
    assert node_pool_auto_config.resource_manager_tags is not None
    assert len(node_pool_auto_config.resource_manager_tags.tags) == 0
    assert node_pool_auto_config.node_kubelet_config is not None
    assert node_pool_auto_config.linux_node_config is not None


def test_pod_autoscaling(cluster: container_v1.Cluster) -> None:
    """Verify the GKE cluster pod autoscaling meets expectations."""
    assert_default_pod_autoscaling(cluster.pod_autoscaling)


def test_fleet(cluster: container_v1.Cluster) -> None:
    """Verify the GKE cluster fleet configuration meets expectations."""
    assert_default_fleet(cluster.fleet)


def test_security_posture_config(cluster: container_v1.Cluster) -> None:
    """Verify the GKE cluster security posture configuration meets expectations."""
    assert_default_security_posture_config(cluster.security_posture_config)


def test_control_plane_endpoints_config(cluster: container_v1.Cluster) -> None:
    """Verify the GKE cluster control plane endpoints configuration meets expectations."""
    assert_default_control_plane_endpoints_config(cluster.control_plane_endpoints_config)


def test_enable_k8s_beta_apis(cluster: container_v1.Cluster) -> None:
    """Verify the GKE cluster beta APIs configuration meets expectations."""
    assert_enable_k8s_beta_apis(cluster.enable_k8s_beta_apis)


def test_enterprise_config(cluster: container_v1.Cluster) -> None:
    """Verify the GKE cluster enterprise configuration meets expectations."""
    assert_enterprise_config(cluster.enterprise_config)


def test_secret_manager_config(cluster: container_v1.Cluster) -> None:
    """Verify the GKE cluster Secret Manager CSI configuration meets expectations."""
    assert_secret_manager_config(cluster.secret_manager_config)


def test_compliance_posture_config(cluster: container_v1.Cluster) -> None:
    """Verify the GKE cluster compliance posture configuration meets expectations."""
    assert_compliance_posture_config(cluster.compliance_posture_config)


def test_user_managed_keys_config(cluster: container_v1.Cluster) -> None:
    """Verify the GKE cluster user managed keys configuration meets expectations."""
    assert_user_managed_keys_config(cluster.user_managed_keys_config)


def test_rbac_binding_config(cluster: container_v1.Cluster) -> None:
    """Verify the GKE cluster RBAC binding configuration meets expectations."""
    assert_rbac_binding_config(cluster.rbac_binding_config)


def test_gke_auto_upgrade_config(cluster: container_v1.Cluster) -> None:
    """Verify the GKE cluster auto upgrade configuration meets expectations."""
    assert_gke_auto_upgrade_config(cluster.gke_auto_upgrade_config)


def test_anonymous_authentication_config(cluster: container_v1.Cluster) -> None:
    """Verify the GKE cluster anonymous authentication configuration meets expectations."""
    assert_anonymous_authentication_config(cluster.anonymous_authentication_config)


def test_private_api_access_via_proxy(
    fixture_output: dict[str, Any],
    vpc_fixture_output: dict[str, Any],
) -> None:
    """Verify that access to Kubernetes API through bastion is successful."""
    endpoint_url = fixture_output["endpoint_url"]
    assert endpoint_url
    ca_cert = fixture_output["ca_cert"]
    assert ca_cert
    bastion_public_ip_address = vpc_fixture_output["bastion_public_ip_address"]
    assert bastion_public_ip_address
    with kubernetes_api_client(
        host=endpoint_url,
        ca=ca_cert,
        proxy_url=f"http://{bastion_public_ip_address}:8888",
    ) as client:
        assert_namespace(client=client, namespace="kube-system")
        assert_any_labelled_service_exists(
            client=client,
            namespace="kube-system",
            label_selector="kubernetes.io/cluster-service=true",
        )


def test_default_dns_config(cluster: container_v1.Cluster) -> None:
    """Verify the GKE cluster default DNS configuration meets expectations."""
    assert_default_dns_config(dns_config=cluster.network_config.dns_config)
