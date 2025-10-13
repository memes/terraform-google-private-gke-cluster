"""Google Kubernetes Engine resource assertions for Standard deployments.

NOTE: This module imports and re-exports assertions from the set common to Standard and Autopilot deployments.
"""

from collections import Counter
from collections.abc import MutableSequence
from typing import Any

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
    """Raise an AssertionError if the base cluster config does not meet default Standard module expectations."""
    assert cluster
    assert expected_name
    assert network
    assert subnet
    assert cluster.name == expected_name
    assert (
        cluster.description == expected_description
        if expected_description
        else f"Private standard GKE cluster {expected_name}"
    )
    assert cluster.initial_node_count == 1
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
    """Raise an AssertionError if the AddonsConfig object does not meet default Standard module expectations."""
    assert addons_config
    assert not addons_config.http_load_balancing.disabled
    assert not addons_config.horizontal_pod_autoscaling.disabled
    assert addons_config.kubernetes_dashboard.disabled
    assert addons_config.network_policy_config.disabled
    assert addons_config.cloud_run_config.disabled
    assert (
        addons_config.cloud_run_config.load_balancer_type
        == container_v1.CloudRunConfig.LoadBalancerType.LOAD_BALANCER_TYPE_EXTERNAL
    )
    assert not addons_config.dns_cache_config.enabled
    assert not addons_config.config_connector_config.enabled
    assert not addons_config.gce_persistent_disk_csi_driver_config.enabled
    assert not addons_config.gcp_filestore_csi_driver_config.enabled
    assert not addons_config.gke_backup_agent_config.enabled
    assert not addons_config.gcs_fuse_csi_driver_config.enabled
    assert not addons_config.stateful_ha_config.enabled
    assert not addons_config.parallelstore_csi_driver_config.enabled
    assert not addons_config.ray_operator_config.enabled
    assert not addons_config.ray_operator_config.ray_cluster_logging_config.enabled
    assert not addons_config.ray_operator_config.ray_cluster_monitoring_config.enabled
    assert not addons_config.high_scale_checkpointing_config.enabled
    assert not addons_config.lustre_csi_driver_config.enabled
    assert not addons_config.lustre_csi_driver_config.enable_legacy_lustre_port


def assert_default_cluster_autoscaling(
    cluster_autoscaling: container_v1.ClusterAutoscaling | None,
    service_account: str,  # noqa: ARG001
) -> None:
    """Raise an AssertionError if ClusterAutoscaling object does not meet default Standard module expectations."""
    assert cluster_autoscaling
    assert not cluster_autoscaling.enable_node_autoprovisioning  # pyright: ignore[reportAttributeAccessIssue]
    assert cluster_autoscaling.autoscaling_profile == container_v1.ClusterAutoscaling.AutoscalingProfile.BALANCED
    assert len(cluster_autoscaling.autoprovisioning_node_pool_defaults.oauth_scopes) == 0
    assert not cluster_autoscaling.autoprovisioning_node_pool_defaults.service_account
    assert not cluster_autoscaling.default_compute_class_config.enabled


def assert_default_network_config(
    network_config: container_v1.NetworkConfig | None,
    network: str,
    subnet: str,
) -> None:
    """Raise an AssertionError if NetworkConfig object does not meet default Standard module expectations."""
    assert network_config
    assert network
    assert subnet
    assert network_config.network == "/".join(network.split("/")[-5:])
    assert network_config.subnetwork == "/".join(subnet.split("/")[-6:])
    assert not network_config.enable_intra_node_visibility
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
    assert dns_config.cluster_dns == container_v1.DNSConfig.Provider.PROVIDER_UNSPECIFIED
    assert dns_config.cluster_dns_scope == container_v1.DNSConfig.DNSScope.DNS_SCOPE_UNSPECIFIED
    assert not dns_config.cluster_dns_domain
    assert not dns_config.additive_vpc_scope_dns_domain


def assert_default_vertical_pod_autoscaling(
    vertical_pod_autoscaling: container_v1.VerticalPodAutoscaling | None,
) -> None:
    """Raise an AssertionError if VerticalPodAutoscaling object does not meet default Standard module expectations."""
    assert not vertical_pod_autoscaling


def assert_default_autopilot(autopilot: container_v1.Autopilot | None) -> None:
    """Raise an AssertionError if Autopilot object does not meet default Standard module expectations."""
    assert autopilot is not None
    assert not autopilot.enabled
    assert not autopilot.workload_policy_config.allow_net_admin
    assert not autopilot.workload_policy_config.autopilot_compatibility_auditing_enabled


def assert_default_node_pools(node_pools: MutableSequence[container_v1.NodePool] | None) -> None:
    """Raise an AssertionError if NodePool objects do no meet default Standard module expectations.

    NOTE: Default vars result in a GKE Standard cluster with 0 node pools after initial node pool is destroyed.
    """
    assert node_pools is not None
    assert len(node_pools) == 0


def assert_default_mesh_certificates(mesh_certificates: container_v1.MeshCertificates | None) -> None:
    """Raise an AssertionError if MeshCertificates object does not meet default Standard module expectations."""
    assert mesh_certificates
    assert mesh_certificates.enable_certificates


def assert_default_node_pool_defaults(node_pool_defaults: container_v1.NodePoolDefaults | None) -> None:
    """Raise an AssertionError if NodePoolDefaults object does not match default Standard module expectations."""
    assert node_pool_defaults is not None
    assert node_pool_defaults.node_config_defaults is not None
    assert node_pool_defaults.node_config_defaults.gcfs_config is not None
    assert not node_pool_defaults.node_config_defaults.gcfs_config.enabled
    assert node_pool_defaults.node_config_defaults.logging_config is not None
    assert node_pool_defaults.node_config_defaults.logging_config.variant_config is not None
    assert (
        node_pool_defaults.node_config_defaults.logging_config.variant_config.variant
        == container_v1.LoggingVariantConfig.Variant.DEFAULT
    )
    assert node_pool_defaults.node_config_defaults.containerd_config is not None
    assert node_pool_defaults.node_config_defaults.node_kubelet_config is not None


def assert_default_monitoring_config(monitoring_config: container_v1.MonitoringConfig | None) -> None:
    """Raise an AssertionError if MonitoringConfig object does not match default Standard module expectations."""
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
    assert not monitoring_config.advanced_datapath_observability_config.enable_metrics
    assert not monitoring_config.advanced_datapath_observability_config.enable_relay
    assert monitoring_config.advanced_datapath_observability_config.relay_mode is not None
    assert (
        monitoring_config.advanced_datapath_observability_config.relay_mode
        == container_v1.AdvancedDatapathObservabilityConfig.RelayMode.RELAY_MODE_UNSPECIFIED
    )


def assert_default_pod_autoscaling(pod_autoscaling: container_v1.PodAutoscaling | None) -> None:
    """Raise an AssertionError if PodAutoscaling object does not match default Standard module expectations."""
    assert pod_autoscaling is not None
    assert pod_autoscaling.hpa_profile == container_v1.PodAutoscaling.HPAProfile.HPA_PROFILE_UNSPECIFIED


def assert_rbac_binding_config(rbac_binding_config: container_v1.RBACBindingConfig | None) -> None:
    """Raise an AssertionError if RBACBindingConfig object does not match default Standard module expectations."""
    assert rbac_binding_config is not None
    assert rbac_binding_config.enable_insecure_binding_system_unauthenticated
    assert rbac_binding_config.enable_insecure_binding_system_authenticated


def assert_node_config(config: container_v1.NodeConfig, settings: dict[str, Any]) -> None:
    """Raise an AssertionError if the NodeConfig object does not match expectations from settings dict."""
    assert config is not None
    assert config.machine_type == settings["machine_type"]
    assert config.disk_size_gb == settings["disk_size"]
    assert config.oauth_scopes == [
        "https://www.googleapis.com/auth/cloud-platform",
    ]
    metadata = config.metadata
    assert metadata is not None
    expected_metadata = settings["metadata"] if "metadata" in settings and settings.get("metadata") is not None else {}
    assert all(item in metadata.items() for item in expected_metadata.items())
    assert config.image_type == settings["image_type"]
    labels = config.labels
    assert labels is not None
    expected_labels = settings["labels"] if "labels" in settings and settings.get("labels") is not None else {}
    assert all(item in labels.items() for item in expected_labels.items())
    assert config.local_ssd_count == settings["local_ssd_count"]
    expected_tags = settings["tags"] if "tags" in settings and settings.get("tags") is not None else []
    assert Counter(config.tags) == Counter(expected_tags)
    assert config.preemptible
    assert config.accelerators is not None
    expected_accelerators = (
        [container_v1.AcceleratorConfig() for gpu in settings["gpu"]]
        if "gpu" in settings and settings.get("gpus") is not None
        else []
    )
    assert len(config.accelerators) == len(expected_accelerators)
    for _accelerator in config.accelerators:
        raise NotImplementedError
    assert config.disk_type == settings["disk_type"]
    if "min_cpu_platform" in settings and settings.get("min_cpu_platform") is not None:
        assert config.min_cpu_platform == settings["min_cpu_platform"]
    assert config.workload_metadata_config is not None
    assert config.workload_metadata_config.mode == container_v1.WorkloadMetadataConfig.Mode.GKE_METADATA
    taints = config.taints
    assert taints is not None
    expected_taints = (
        [container_v1.NodeTaint(mapping=taint) for taint in settings["taints"]]
        if "taints" in settings and settings["taints"] is not None
        else []
    )
    assert Counter(config.taints) == Counter(expected_taints)
    assert config.shielded_instance_config is not None
    assert config.shielded_instance_config.enable_secure_boot == settings.get("enable_secure_boot", False)
    assert config.shielded_instance_config.enable_integrity_monitoring == settings.get(
        "enable_integrity_monitoring",
        False,
    )
    assert config.linux_node_config is not None
    sysctls = config.linux_node_config.sysctls
    assert sysctls is not None
    expected_sysctls = settings.get("sysctls") or {}
    assert all(item in sysctls.items() for item in expected_sysctls.items())
    expected_boot_disk_kms_key = settings.get("boot_disk_kms_key", "") or ""
    assert config.boot_disk_kms_key == expected_boot_disk_kms_key


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
    "assert_node_config",
    "assert_rbac_binding_config",
    "assert_secret_manager_config",
    "assert_user_managed_keys_config",
]
