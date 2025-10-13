"""Google Kubernetes Engine resource assertions for Autopilot deployments.

NOTE: This module imports and re-exports assertions from the set common to Standard and Autopilot deployments.
"""

from collections.abc import MutableSequence

from google.cloud import container_v1

from .gke_common_assertions import (
    assert_anonymous_authentication_config,
    assert_compliance_posture_config,
    assert_default_authenticator_groups_config,
    assert_default_binary_authorization,
    assert_default_confidential_nodes,
    assert_default_control_plane_endpoints_config,
    assert_default_cost_management_config,
    assert_default_database_encryption,
    assert_default_fleet,
    assert_default_identity_service_config,
    assert_default_ip_allocation_policy,
    assert_default_legacy_abac,
    assert_default_logging_config,
    assert_default_maintenance_policy,
    assert_default_master_auth,
    assert_default_network_policy,
    assert_default_node_pool_auto_config,
    assert_default_notification_config,
    assert_default_release_channel,
    assert_default_resource_labels,
    assert_default_resource_usage_export_config,
    assert_default_security_posture_config,
    assert_default_shielded_nodes,
    assert_default_workload_identity_config,
    assert_enable_k8s_beta_apis,
    assert_enterprise_config,
    assert_gke_auto_upgrade_config,
    assert_secret_manager_config,
    assert_user_managed_keys_config,
)

EXPECTED_CLUSTER_STATUSES = [container_v1.Cluster.Status.RECONCILING, container_v1.Cluster.Status.RUNNING]


def assert_default_cluster_config(
    cluster: container_v1.Cluster | None,
    expected_name: str,
    network: str,
    subnet: str,
    expected_description: str | None = None,
) -> None:
    """Raise an AssertionError if the base cluster config does not meet default Autopilot module expectations."""
    assert cluster
    assert expected_name
    assert network
    assert subnet
    assert cluster.name == expected_name
    assert (
        cluster.description == expected_description
        if expected_description
        else "Private autopilot GKE cluster for demo"
    )
    assert not cluster.initial_node_count
    assert cluster.logging_service == "logging.googleapis.com/kubernetes"
    assert cluster.monitoring_service == "monitoring.googleapis.com/kubernetes"
    assert cluster.network == network.split("/")[-1:][0]
    assert cluster.subnetwork == subnet.split("/")[-1:][0]
    assert cluster.location == subnet.split("/")[-3:][0]
    assert cluster.default_max_pods_constraint.max_pods_per_node == 110  # noqa: PLR2004
    assert not cluster.enable_tpu
    assert cluster.status in EXPECTED_CLUSTER_STATUSES
    assert not cluster.enable_kubernetes_alpha
    assert not cluster.alpha_cluster_feature_gates


def assert_default_addons_config(addons_config: container_v1.AddonsConfig | None) -> None:
    """Raise an AssertionError if the AddonsConfig object does not meet default Autopilot module expectations."""
    assert addons_config
    assert not addons_config.http_load_balancing.disabled
    assert not addons_config.horizontal_pod_autoscaling.disabled
    assert addons_config.kubernetes_dashboard.disabled
    assert addons_config.network_policy_config.disabled
    assert not addons_config.cloud_run_config
    assert addons_config.dns_cache_config.enabled
    assert not addons_config.config_connector_config.enabled
    assert addons_config.gce_persistent_disk_csi_driver_config.enabled
    assert addons_config.gcp_filestore_csi_driver_config.enabled
    assert not addons_config.gke_backup_agent_config.enabled
    assert addons_config.gcs_fuse_csi_driver_config.enabled
    assert addons_config.stateful_ha_config.enabled
    assert addons_config.parallelstore_csi_driver_config.enabled
    assert not addons_config.ray_operator_config.enabled
    assert not addons_config.ray_operator_config.ray_cluster_logging_config.enabled
    assert not addons_config.ray_operator_config.ray_cluster_monitoring_config.enabled
    assert not addons_config.high_scale_checkpointing_config.enabled
    assert not addons_config.lustre_csi_driver_config.enabled
    assert not addons_config.lustre_csi_driver_config.enable_legacy_lustre_port


def assert_default_cluster_autoscaling(
    cluster_autoscaling: container_v1.ClusterAutoscaling | None,
    service_account: str,
) -> None:
    """Raise an AssertionError if ClusterAutoscaling object does not meet default Autopilot module expectations."""
    assert cluster_autoscaling
    assert cluster_autoscaling.enable_node_autoprovisioning  # pyright: ignore[reportAttributeAccessIssue]
    assert (
        cluster_autoscaling.autoscaling_profile
        == container_v1.ClusterAutoscaling.AutoscalingProfile.OPTIMIZE_UTILIZATION
    )
    assert cluster_autoscaling.autoprovisioning_node_pool_defaults.oauth_scopes == [
        "https://www.googleapis.com/auth/cloud-platform",
    ]
    assert cluster_autoscaling.autoprovisioning_node_pool_defaults.service_account == service_account
    assert not cluster_autoscaling.default_compute_class_config.enabled


def assert_default_network_config(
    network_config: container_v1.NetworkConfig | None,
    network: str,
    subnet: str,
) -> None:
    """Raise an AssertionError if NetworkConfig object does not meet default Autopilot module expectations."""
    assert network_config
    assert network
    assert subnet
    assert network_config.network == "/".join(network.split("/")[-5:])
    assert network_config.subnetwork == "/".join(subnet.split("/")[-6:])
    assert network_config.enable_intra_node_visibility
    assert not network_config.default_snat_status.disabled
    assert network_config.enable_l4ilb_subsetting
    assert network_config.datapath_provider == container_v1.DatapathProvider.ADVANCED_DATAPATH
    assert (
        network_config.private_ipv6_google_access
        == container_v1.PrivateIPv6GoogleAccess.PRIVATE_IPV6_GOOGLE_ACCESS_UNSPECIFIED
    )


def assert_default_dns_config(dns_config: container_v1.DNSConfig | None) -> None:
    """Raise an AssertionError if DNSConfig object does not meet default Autopilot module expectations."""
    assert dns_config is not None
    assert dns_config.cluster_dns == container_v1.DNSConfig.Provider.CLOUD_DNS
    assert dns_config.cluster_dns_scope == container_v1.DNSConfig.DNSScope.CLUSTER_SCOPE
    assert dns_config.cluster_dns_domain == "cluster.local"
    assert not dns_config.additive_vpc_scope_dns_domain


def assert_default_vertical_pod_autoscaling(
    vertical_pod_autoscaling: container_v1.VerticalPodAutoscaling | None,
) -> None:
    """Raise an AssertionError if VerticalPodAutoscaling object does not meet default Autopilot module expectations."""
    assert vertical_pod_autoscaling
    assert vertical_pod_autoscaling.enabled


def assert_default_autopilot(autopilot: container_v1.Autopilot | None) -> None:
    """Raise an AssertionError if Autopilot object does not meet default Autopilot module expectations."""
    assert autopilot is not None
    assert autopilot.enabled
    assert not autopilot.workload_policy_config.allow_net_admin
    assert not autopilot.workload_policy_config.autopilot_compatibility_auditing_enabled


def assert_default_node_pools(node_pools: MutableSequence[container_v1.NodePool] | None) -> None:
    """Raise an AssertionError if NodePool objects do no meet default Autopilot module expectations.

    NOTE: GKE Autopilot nodes are not directly influenced by the module, so just verify there is at least one pool. The
    assert_default_node_pool_autoconfig function has the relevant tests.
    """
    # Only verify the object exists, since the quantity depends on other actions.
    assert node_pools is not None


def assert_default_mesh_certificates(mesh_certificates: container_v1.MeshCertificates | None) -> None:
    """Raise an AssertionError if MeshCertificates object does not meet default Autopilot module expectations."""
    assert mesh_certificates is not None
    assert not mesh_certificates.enable_certificates


def assert_default_node_pool_defaults(node_pool_defaults: container_v1.NodePoolDefaults | None) -> None:
    """Raise an AssertionError if NodePoolDefaults object does not match default Autopilot module expectations."""
    assert node_pool_defaults is not None
    assert node_pool_defaults.node_config_defaults is not None
    assert node_pool_defaults.node_config_defaults.gcfs_config is not None
    assert node_pool_defaults.node_config_defaults.gcfs_config.enabled
    assert node_pool_defaults.node_config_defaults.logging_config is not None
    assert node_pool_defaults.node_config_defaults.logging_config.variant_config is not None
    assert (
        node_pool_defaults.node_config_defaults.logging_config.variant_config.variant
        == container_v1.LoggingVariantConfig.Variant.DEFAULT
    )
    assert node_pool_defaults.node_config_defaults.containerd_config is not None
    assert node_pool_defaults.node_config_defaults.node_kubelet_config is not None


def assert_default_monitoring_config(monitoring_config: container_v1.MonitoringConfig | None) -> None:
    """Raise an AssertionError if MonitoringConfig object does not match default Autopilot module expectations."""
    assert monitoring_config is not None
    assert monitoring_config.component_config is not None
    assert monitoring_config.managed_prometheus_config is not None
    assert monitoring_config.managed_prometheus_config.enabled
    assert monitoring_config.managed_prometheus_config.auto_monitoring_config is not None
    assert (
        monitoring_config.managed_prometheus_config.auto_monitoring_config.scope
        == container_v1.AutoMonitoringConfig.Scope.SCOPE_UNSPECIFIED
    )
    assert monitoring_config.advanced_datapath_observability_config is not None
    assert monitoring_config.advanced_datapath_observability_config.enable_metrics
    assert not monitoring_config.advanced_datapath_observability_config.enable_relay
    assert monitoring_config.advanced_datapath_observability_config.relay_mode is not None
    assert (
        monitoring_config.advanced_datapath_observability_config.relay_mode
        == container_v1.AdvancedDatapathObservabilityConfig.RelayMode.RELAY_MODE_UNSPECIFIED
    )


def assert_default_pod_autoscaling(pod_autoscaling: container_v1.PodAutoscaling | None) -> None:
    """Raise an AssertionError if PodAutoscaling object does not match default Autopilot module expectations."""
    assert pod_autoscaling is not None
    assert pod_autoscaling.hpa_profile == container_v1.PodAutoscaling.HPAProfile.PERFORMANCE


def assert_rbac_binding_config(rbac_binding_config: container_v1.RBACBindingConfig | None) -> None:
    """Raise an AssertionError if RBACBindingConfig object does not match default module expectations."""
    assert rbac_binding_config is not None
    assert not rbac_binding_config.enable_insecure_binding_system_unauthenticated
    assert not rbac_binding_config.enable_insecure_binding_system_authenticated


__all__ = [
    "assert_anonymous_authentication_config",
    "assert_compliance_posture_config",
    "assert_default_addons_config",
    "assert_default_authenticator_groups_config",
    "assert_default_autopilot",
    "assert_default_binary_authorization",
    "assert_default_cluster_autoscaling",
    "assert_default_cluster_config",
    "assert_default_confidential_nodes",
    "assert_default_control_plane_endpoints_config",
    "assert_default_cost_management_config",
    "assert_default_database_encryption",
    "assert_default_dns_config",
    "assert_default_fleet",
    "assert_default_identity_service_config",
    "assert_default_ip_allocation_policy",
    "assert_default_legacy_abac",
    "assert_default_logging_config",
    "assert_default_maintenance_policy",
    "assert_default_master_auth",
    "assert_default_mesh_certificates",
    "assert_default_monitoring_config",
    "assert_default_network_config",
    "assert_default_network_policy",
    "assert_default_node_pool_auto_config",
    "assert_default_node_pool_defaults",
    "assert_default_node_pools",
    "assert_default_notification_config",
    "assert_default_pod_autoscaling",
    "assert_default_release_channel",
    "assert_default_resource_labels",
    "assert_default_resource_usage_export_config",
    "assert_default_security_posture_config",
    "assert_default_shielded_nodes",
    "assert_default_vertical_pod_autoscaling",
    "assert_default_workload_identity_config",
    "assert_enable_k8s_beta_apis",
    "assert_enterprise_config",
    "assert_gke_auto_upgrade_config",
    "assert_rbac_binding_config",
    "assert_secret_manager_config",
    "assert_user_managed_keys_config",
]
