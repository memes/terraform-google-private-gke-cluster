"""Google Kubernetes Engine resource assertions that are expected to be the same for Standard and Autopilot deployments.

NOTE: The functions in this file are re-exported through the Autopilot and Standard assertions file; tests should import
from one of those modules specifically rather than this one.
"""

from collections.abc import Mapping, MutableMapping

from google.cloud import container_v1


def assert_default_release_channel(release_channel: container_v1.ReleaseChannel | None) -> None:
    """Raise an AssertionError if the release channel does not meet default module expectations."""
    assert release_channel
    assert release_channel.channel == container_v1.ReleaseChannel.Channel.STABLE


def assert_default_master_auth(master_auth: container_v1.MasterAuth | None) -> None:
    """Raise an AssertionError if the MasterAuth object does not meet default module expectations."""
    assert master_auth
    assert not master_auth.username
    assert not master_auth.password
    assert not master_auth.client_certificate_config.issue_client_certificate
    assert not master_auth.client_certificate
    assert not master_auth.client_key


def assert_default_ip_allocation_policy(
    ip_allocation_policy: container_v1.IPAllocationPolicy | None,
    cluster_range_name: str = "pods",
    services_range_name: str = "services",
) -> None:
    """Raise an AssertionError if the IPAllocationPolicy object does not meet default module expectations."""
    assert ip_allocation_policy
    assert cluster_range_name
    assert services_range_name
    assert ip_allocation_policy.use_ip_aliases
    assert not ip_allocation_policy.create_subnetwork
    assert not ip_allocation_policy.subnetwork_name
    assert ip_allocation_policy.cluster_secondary_range_name == cluster_range_name
    assert ip_allocation_policy.services_secondary_range_name == services_range_name
    assert not ip_allocation_policy.use_routes
    assert ip_allocation_policy.stack_type == container_v1.StackType.IPV4
    assert ip_allocation_policy.ipv6_access_type == container_v1.IPv6AccessType.IPV6_ACCESS_TYPE_UNSPECIFIED


def assert_default_maintenance_policy(maintenance_policy: container_v1.MaintenancePolicy) -> None:
    """Raise an AssertionError if the MaintenancePolicy object does not meet default module expectations."""
    assert maintenance_policy
    assert maintenance_policy.window.daily_maintenance_window
    assert maintenance_policy.window.daily_maintenance_window.start_time == "03:30"


def assert_default_resource_labels(resource_labels: MutableMapping, expected_labels: Mapping) -> None:
    """Raise an AssertionError if resource labels do not meet default module expectations."""
    assert resource_labels
    assert expected_labels
    assert all(item in resource_labels.items() for item in expected_labels.items())


def assert_default_legacy_abac(legacy_abac: container_v1.LegacyAbac | None) -> None:
    """Raise an AssertionError if Legacy ABAC object does not meet default module expectation."""
    assert not legacy_abac


def assert_default_network_policy(network_policy: container_v1.NetworkPolicy | None) -> None:
    """Raise an AssertionError if NetworkPolicy object does not meet default module expectation."""
    assert not network_policy


def assert_default_binary_authorization(
    binary_authorization: container_v1.BinaryAuthorization | None,
) -> None:
    """Raise an AssertionError if BinaryAuthorization object does not meet default module expectation."""
    assert binary_authorization
    assert not binary_authorization.enabled
    assert binary_authorization.evaluation_mode == container_v1.BinaryAuthorization.EvaluationMode.DISABLED


def assert_default_database_encryption(database_encryption: container_v1.DatabaseEncryption | None) -> None:
    """Raise an AssertionError if the DatabaseEncryption object does not meet default module expectations."""
    assert database_encryption
    assert database_encryption.state == container_v1.DatabaseEncryption.State.DECRYPTED
    assert not database_encryption.key_name


def assert_default_resource_usage_export_config(
    resource_usage_config: container_v1.ResourceUsageExportConfig | None,
) -> None:
    """Raise an AssertionError if ResourceUsageExportConfig object does not meet default module expectations."""
    assert not resource_usage_config


def assert_default_authenticator_groups_config(
    authenticator_groups_config: container_v1.AuthenticatorGroupsConfig | None,
) -> None:
    """Raise an AssertionError if AuthenticatorGroupsConfig object does not meet default module expectations."""
    assert not authenticator_groups_config


def assert_default_control_plane_endpoints_config(
    control_plane_endpoints_config: container_v1.ControlPlaneEndpointsConfig | None,
) -> None:
    """Raise an AssertionError if ControlPlaneEndpointsConfig object does not meet default module expectations."""
    assert control_plane_endpoints_config
    assert control_plane_endpoints_config.dns_endpoint_config.endpoint
    assert not control_plane_endpoints_config.dns_endpoint_config.allow_external_traffic
    assert control_plane_endpoints_config.ip_endpoints_config.enabled
    assert not control_plane_endpoints_config.ip_endpoints_config.enable_public_endpoint
    assert control_plane_endpoints_config.ip_endpoints_config.global_access
    assert control_plane_endpoints_config.ip_endpoints_config.private_endpoint
    assert control_plane_endpoints_config.ip_endpoints_config.authorized_networks_config
    assert control_plane_endpoints_config.ip_endpoints_config.authorized_networks_config.cidr_blocks
    assert len(control_plane_endpoints_config.ip_endpoints_config.authorized_networks_config.cidr_blocks) > 0


def assert_default_shielded_nodes(shielded_nodes: container_v1.ShieldedNodes | None) -> None:
    """Raise an AssertionError if ShieldedNodes object does not meet default module expectations."""
    assert shielded_nodes
    assert shielded_nodes.enabled


def assert_default_workload_identity_config(
    workload_identity_config: container_v1.WorkloadIdentityConfig | None,
    project_id: str,
) -> None:
    """Raise an AssertionError if WorkloadIdentityConfig object does not meet default module expectations."""
    assert workload_identity_config
    assert workload_identity_config.workload_pool == f"{project_id}.svc.id.goog"


def assert_default_cost_management_config(cost_management_config: container_v1.CostManagementConfig | None) -> None:
    """Raise an AssertionError if CostManagementConfig object does not meet default module expectations."""
    assert cost_management_config is not None
    assert not cost_management_config.enabled


def assert_default_notification_config(notification_config: container_v1.NotificationConfig | None) -> None:
    """Raise an AssertionError if NotificationConfig object does not meet default module expectations."""
    assert notification_config is not None
    assert notification_config.pubsub is not None
    assert not notification_config.pubsub.enabled


def assert_default_confidential_nodes(confidential_nodes: container_v1.ConfidentialNodes | None) -> None:
    """Raise an AssertionError if ConfidentialNodes object does not meet default module expectations."""
    assert confidential_nodes is not None
    assert not confidential_nodes.enabled


def assert_default_identity_service_config(identity_service_config: container_v1.IdentityServiceConfig) -> None:
    """Raise an AssertionError if IdentityServiceConfig object does not meet default module expectations."""
    assert identity_service_config is not None
    assert not identity_service_config.enabled


def assert_default_logging_config(logging_config: container_v1.LoggingConfig | None) -> None:
    """Raise an AssertionError if LoggingConfig object does not match default module expectations."""
    assert logging_config is not None
    assert logging_config.component_config is not None


def assert_default_node_pool_auto_config(node_pool_auto_config: container_v1.NodePoolAutoConfig | None) -> None:
    """Raise an AssertionError if NodePoolAutoConfig object does not match default module expectations."""
    assert node_pool_auto_config is not None
    assert node_pool_auto_config.network_tags is not None
    assert len(node_pool_auto_config.network_tags.tags) == 0
    assert node_pool_auto_config.resource_manager_tags is not None
    assert len(node_pool_auto_config.resource_manager_tags.tags) == 0
    assert node_pool_auto_config.node_kubelet_config is not None
    assert node_pool_auto_config.linux_node_config is not None


def assert_default_fleet(fleet: container_v1.Fleet | None) -> None:
    """Raise an AssertionError if Fleet object does not match default module expectations."""
    assert fleet is not None
    assert not fleet.project
    assert not fleet.membership
    assert not fleet.pre_registered


def assert_default_security_posture_config(security_posture_config: container_v1.SecurityPostureConfig | None) -> None:
    """Raise an AssertionError if SecurityPostureConfig object does not match default module expectations."""
    assert security_posture_config is not None
    assert security_posture_config.mode == container_v1.SecurityPostureConfig.Mode.BASIC
    assert (
        security_posture_config.vulnerability_mode
        == container_v1.SecurityPostureConfig.VulnerabilityMode.VULNERABILITY_MODE_UNSPECIFIED
    )


def assert_enable_k8s_beta_apis(enable_k8s_beta_apis: container_v1.K8sBetaAPIConfig | None) -> None:
    """Raise an AssertionError if K8sBetaAPIConfig object does not match default module expectations."""
    assert enable_k8s_beta_apis is not None
    assert len(enable_k8s_beta_apis.enabled_apis) == 0


def assert_enterprise_config(enterprise_config: container_v1.EnterpriseConfig | None) -> None:
    """Raise an AssertionError if EnterpriseConfig object does not match default module expectations."""
    assert enterprise_config is not None
    assert enterprise_config.desired_tier == container_v1.EnterpriseConfig.ClusterTier.CLUSTER_TIER_UNSPECIFIED


def assert_secret_manager_config(secret_manager_config: container_v1.SecretManagerConfig | None) -> None:
    """Raise an AssertionError if SecretManagerConfig object does not match default module expectations."""
    assert secret_manager_config is not None
    assert secret_manager_config.enabled


def assert_compliance_posture_config(compliance_posture_config: container_v1.CompliancePostureConfig | None) -> None:
    """Raise an AssertionError if CompliancePostureConfig object does not match default module expectations."""
    assert compliance_posture_config is not None
    assert compliance_posture_config.mode == container_v1.CompliancePostureConfig.Mode.MODE_UNSPECIFIED
    assert len(compliance_posture_config.compliance_standards) == 0


def assert_user_managed_keys_config(user_managed_keys_config: container_v1.UserManagedKeysConfig | None) -> None:
    """Raise an AssertionError if UserManagedKeysConfig object does not match default module expectations."""
    assert user_managed_keys_config is not None


def assert_gke_auto_upgrade_config(gke_auto_upgrade_config: container_v1.GkeAutoUpgradeConfig | None) -> None:
    """Raise an AssertionError if GkeAutoUpgradeConfig object does not match default module expectations."""
    assert gke_auto_upgrade_config is not None
    assert gke_auto_upgrade_config.patch_mode == container_v1.GkeAutoUpgradeConfig.PatchMode.PATCH_MODE_UNSPECIFIED


def assert_anonymous_authentication_config(
    anonymous_authentication_config: container_v1.AnonymousAuthenticationConfig | None,
) -> None:
    """Raise an AssertionError if AnonymousAuthenticationConfig object does not match default module expectations."""
    assert anonymous_authentication_config is not None
    assert anonymous_authentication_config.mode == container_v1.AnonymousAuthenticationConfig.Mode.ENABLED
