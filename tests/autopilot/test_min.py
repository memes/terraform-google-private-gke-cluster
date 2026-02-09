"""Test fixture for Autopilot GKE cluster with minimal configuration."""

import base64
import pathlib
import re
import urllib.parse
from collections.abc import Callable, Generator
from typing import Any, cast

import pytest
from cryptography import x509
from google.cloud import compute_v1, container_v1

from tests import (
    assert_any_labelled_service_exists,
    assert_namespace,
    get_public_address,
    kubernetes_api_client,
    run_tf_plan_apply_destroy,
    wait_for_forward_proxy,
)
from tests.autopilot import (
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
    assert_default_node_pool_auto_config,
    assert_default_node_pool_defaults,
    assert_default_node_pools,
    assert_default_notification_config,
    assert_default_pod_autoscaling,
    assert_default_release_channel,
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

FIXTURE_NAME = "auto-min"
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
def network_self_link(
    fixture_name: str,
    network_builder: Callable[..., str],
    allow_ingress_firewall_builder: Callable[..., None],
) -> str:
    """Create testing VPC network."""
    self_link = network_builder(fixture_name)
    allow_ingress_firewall_builder(
        network=self_link,
        name=f"{fixture_name}-allow-ingress",
    )
    return self_link


@pytest.fixture(scope="module")
def subnet_self_link(
    fixture_name: str,
    network_self_link: str,
    subnet_builder: Callable[..., str],
) -> str:
    """Create testing VPC subnet with default secondary ranges."""
    return subnet_builder(name=fixture_name, network_self_link=network_self_link)


@pytest.fixture(scope="module")
def bastion_sa_email(service_account_builder: Callable[..., str], fixture_name: str) -> str:
    """Create a service account for this test case's bastion host and return it's email identifier."""
    return service_account_builder(name=f"{fixture_name}-jmp")


@pytest.fixture(scope="module")
def bastion(
    fixture_name: str,
    fixture_labels: dict[str, str],
    bastion_sa_email: str,
    subnet_self_link: str,
    bastion_builder: Callable[..., compute_v1.Instance],
) -> compute_v1.Instance:
    """Create a testing Bastion instance, returning the instance object."""
    return bastion_builder(
        name=f"{fixture_name}-jmp",
        subnet=subnet_self_link,
        sa_email=bastion_sa_email,
        labels=fixture_labels,
    )


@pytest.fixture(scope="module")
def bastion_proxy_url(
    bastion: compute_v1.Instance,
) -> str:
    """Return the URL to use for proxying through bastion."""
    proxy_url = f"http://{get_public_address(bastion)}:8888"
    wait_for_forward_proxy(proxy_url)
    return proxy_url


@pytest.fixture(scope="module")
def sa_fixture_output(
    sa_fixture_dir: Callable[[str], pathlib.Path],
    project_id: str,
    fixture_name: str,
    fixture_labels: dict[str, str],
) -> Generator[dict[str, Any], None, None]:
    """Create service account for test case."""
    with run_tf_plan_apply_destroy(
        fixture=sa_fixture_dir(f"{FIXTURE_NAME}-sa"),
        tfvars={
            "project_id": project_id,
            "name": fixture_name,
            "labels": fixture_labels,
        },
    ) as output:
        yield output


@pytest.fixture(scope="module")
def fixture_output(
    autopilot_fixture_dir: Callable[[str], pathlib.Path],
    project_id: str,
    fixture_name: str,
    subnet_self_link: str,
    sa_fixture_output: dict[str, Any],
) -> Generator[dict[str, Any], None, None]:
    """Create GKE Autopilot cluster for test case."""
    service_account = cast("str", sa_fixture_output["email"])
    assert service_account
    with run_tf_plan_apply_destroy(
        fixture=autopilot_fixture_dir(FIXTURE_NAME),
        tfvars={
            "project_id": project_id,
            "name": fixture_name,
            "service_account": service_account,
            "subnet": {
                "self_link": subnet_self_link,
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
    dns_endpoint_url = fixture_output["dns_endpoint_url"]
    assert dns_endpoint_url
    url = urllib.parse.urlparse(dns_endpoint_url)
    assert url
    assert url.scheme == "https"
    assert re.search(f"{region}\\.gke\\.goog$", url.hostname)
    assert not url.port
    assert "private_ip_endpoint_url" not in fixture_output


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


# NOTE: Labels are not passed as variable, this test cannot verify and does nothing.
def test_resource_labels(cluster: container_v1.Cluster, fixture_labels: dict[str, str]) -> None:
    """Verify the GKE cluster resource labels configuration meets expectations."""


def test_legacy_abac_config(cluster: container_v1.Cluster) -> None:
    """Verify the GKE cluster legacy ABAC configuration meets expectations."""
    assert_default_legacy_abac(cluster.legacy_abac)


def test_network_policy_config(cluster: container_v1.Cluster) -> None:
    """Verify the GKE cluster addons configuration meets expectations."""
    assert_default_network_policy(cluster.network_policy)


def test_default_ip_allocation_policy(
    cluster: container_v1.Cluster,
) -> None:
    """Verify the GKE cluster IP allocation policy meets expectations."""
    assert_default_ip_allocation_policy(
        cluster.ip_allocation_policy,
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


def test_node_pool_auto_config(cluster: container_v1.Cluster) -> None:
    """Verify the GKE cluster node pool auto config meets expectations."""
    assert_default_node_pool_auto_config(cluster.node_pool_auto_config)


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


def test_default_dns_config(cluster: container_v1.Cluster) -> None:
    """Verify the GKE cluster default DNS configuration meets expectations."""
    assert_default_dns_config(dns_config=cluster.network_config.dns_config)


def test_remote_dns_endpoint_url(
    fixture_output: dict[str, Any],
) -> None:
    """Verify that access to DNS Kubernetes API from this device is successful."""
    endpoint_url = fixture_output["dns_endpoint_url"]
    assert endpoint_url

    with kubernetes_api_client(
        host=endpoint_url,
    ) as client:
        assert_namespace(client=client, namespace="kube-system")
        assert_any_labelled_service_exists(
            client=client,
            namespace="kube-system",
            label_selector="kubernetes.io/cluster-service=true",
        )


def test_proxied_dns_endpoint_url(
    fixture_output: dict[str, Any],
    bastion_proxy_url: str,
) -> None:
    """Verify that access to DNS Kubernetes API proxied through a VPC bastion is successful."""
    endpoint_url = fixture_output["dns_endpoint_url"]
    assert endpoint_url
    assert bastion_proxy_url

    with kubernetes_api_client(
        host=endpoint_url,
        proxy_url=bastion_proxy_url,
    ) as client:
        assert_namespace(client=client, namespace="kube-system")
        assert_any_labelled_service_exists(
            client=client,
            namespace="kube-system",
            label_selector="kubernetes.io/cluster-service=true",
        )
