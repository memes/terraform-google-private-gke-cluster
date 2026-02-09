"""Define functions common to all test cases in the tests namespace.

NOTE: This file also defines a common set of GKE and kubernetes assertion functions that can validate GKE deployment
meets default expectations. Individual test cases may need to override these since they are testing non-default
scenarios.
"""

import base64
import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import time
from collections import Counter
from collections.abc import Callable, Generator, Mapping, MutableMapping, MutableSequence
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import google.api_core.extended_operation
import google.api_core.operation
import google.auth
import google.auth.credentials
import google.auth.transport.requests
import kubernetes.client
import kubernetes.watch
import requests
from google.cloud import compute_v1, container_v1

ACTIONABLE_WATCHER_TYPES = ["ADDED", "MODIFIED"]
EXPECTED_CLUSTER_STATUSES = [container_v1.Cluster.Status.RECONCILING, container_v1.Cluster.Status.RUNNING]


def skip_destroy_phase() -> bool:
    """Determine if resource destroy phase should be skipped for successful fixtures."""
    return os.getenv("TEST_SKIP_DESTROY_PHASE", "False").lower() in ["true", "t", "yes", "y", "1"]


def get_tf_command() -> str:
    """Return an explicit command to use for module execution or the first tofu or terraform binary found in PATH.

    NOTE: Preference will be given to the value of environment variable TEST_TF_COMMAND.
    """
    tf_command = os.getenv("TEST_TF_COMMAND") or shutil.which("tofu") or shutil.which("terraform")
    assert tf_command, "A tofu or terraform binary could not be determined"
    return tf_command


@contextmanager
def run_tf_plan_apply_destroy(
    fixture: pathlib.Path,
    tfvars: dict[str, Any] | None,
    workspace: str | None = None,
    tf_command: str | None = None,
) -> Generator[dict[str, Any], None, None]:
    """Execute terraform/tofu fixture lifecycle in an optional workspace, yielding the output post-apply.

    NOTE: Resources will not be destroyed if the test case raises an error.
    """
    if tfvars is None:
        tfvars = {}
    if not tf_command:
        tf_command = get_tf_command()
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
            "-input=false",
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
        # Validate module
        subprocess.run(
            [
                tf_command,
                f"-chdir={fixture!s}",
                "validate",
                "-no-color",
                f"-var-file={tfvar_file.name}",
            ],
            check=True,
            capture_output=True,
        )
        # Execute plan then apply with a common plan file.
        with tempfile.NamedTemporaryFile(
            mode="w+b",
            prefix="tf",
            suffix=".plan",
            delete_on_close=False,
            delete=True,
        ) as plan_file:
            plan_file.close()
            subprocess.run(
                [
                    tf_command,
                    f"-chdir={fixture!s}",
                    "plan",
                    "-no-color",
                    "-input=false",
                    f"-var-file={tfvar_file.name}",
                    f"-out={plan_file.name}",
                ],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                [
                    tf_command,
                    f"-chdir={fixture!s}",
                    "apply",
                    "-no-color",
                    "-input=false",
                    "-auto-approve",
                    plan_file.name,
                ],
                check=True,
                capture_output=True,
            )

        # Run plan again with -detailed-exitcode flag, which will only return an exit code of 0 if there are no further
        # changes. This is to find subtle issues in the Terraform declaration which inadvertently triggers unexpected
        # resource updates or recreations.
        subprocess.run(
            [
                tf_command,
                f"-chdir={fixture!s}",
                "plan",
                "-no-color",
                "-input=false",
                "-detailed-exitcode",
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
                        "-input=false",
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


@contextmanager
def run_tf_test(
    fixture: pathlib.Path,
    tfvars: dict[str, Any] | None = None,
    workspace: str | None = None,
    tf_command: str | None = None,
) -> Generator[list[dict[str, Any]], None, None]:
    """Execute terraform/tofu test lifecycle in an optional workspace, yielding the output as a JSON array."""
    if tfvars is None:
        tfvars = {}
    if not tf_command:
        tf_command = get_tf_command()
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
            "-input=false",
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
        delete=False,
    ) as tfvar_file:
        json.dump(tfvars, tfvar_file, ensure_ascii=False, indent=2)
        tfvar_file.close()
        output = subprocess.run(
            [
                tf_command,
                f"-chdir={fixture!s}",
                "test",
                "-json",
                f"-var-file={tfvar_file.name}",
            ],
            check=False,
            capture_output=True,
        )
        yield [json.loads(line) for line in output.stdout.splitlines()]


def get_public_address(instance: compute_v1.Instance, interface_index: int | None = None) -> str:
    """Extract the public IP address of the instance's interface at index."""
    assert instance.network_interfaces
    if interface_index is None:
        interface_index = 0
    interface = instance.network_interfaces[interface_index]
    assert interface
    assert interface.access_configs
    assert interface.access_configs[0]
    assert interface.access_configs[0].nat_i_p
    return interface.access_configs[0].nat_i_p


def get_private_address(instance: compute_v1.Instance, interface_index: int | None = None) -> str:
    """Extract the private IP address of the instance's interface at index."""
    assert instance.network_interfaces
    if interface_index is None:
        interface_index = 0
    interface = instance.network_interfaces[interface_index]
    assert interface
    assert interface.network_i_p
    return interface.network_i_p


def wait_for_forward_proxy(proxy_url: str, endpoint: str | None = None, timeout: timedelta | None = None) -> None:
    """Wait until the forward-proxy is handling traffic, or raise TimeoutError."""
    if endpoint is None:
        endpoint = "https://f5.com"
    timeout_ts = datetime.now(UTC) + (timeout if timeout is not None else timedelta(seconds=120))
    while not requests.get(endpoint, proxies={"https": proxy_url}).ok:
        if datetime.now(UTC) > timeout_ts:
            raise TimeoutError
        time.sleep(10)


def handle_operation(
    operation: google.api_core.operation.Operation,
    timeout: int = 180,
) -> Any:  # noqa: ANN401
    """Watch the operation and raise an error if it indicates a failure."""
    return operation.result(timeout=timeout)


def handle_extended_operation(
    operation: google.api_core.extended_operation.ExtendedOperation,
    timeout: int = 180,
) -> Any:  # noqa: ANN401
    """Watch the operation and raise an error if it indicates a failure."""
    result = operation.result(timeout=timeout)
    if operation.error_code:
        raise operation.exception() or RuntimeError(operation.error_message)
    return result


@contextmanager
def kubernetes_api_client(
    host: str,
    ca: str | None = None,
    proxy_url: str | None = None,
) -> Generator[kubernetes.client.ApiClient, None, None]:
    """Yield a configured API client built from GKE parameters.

    NOTE: API client expects optional CA certificate to be passed as a file, so this will create a temporary file that
    will be destroyed after the API client is released.
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
        config = kubernetes.client.Configuration(
            host=host,
            api_key_prefix={
                "authorization": "Bearer",
            },
            api_key={
                "authorization": credentials.token,
            },
        )
        if ca:
            ca_cert_file.write(base64.standard_b64decode(ca))
            ca_cert_file.close()
            config.ssl_ca_cert = ca_cert_file.name
        config.verify_ssl = True
        if proxy_url:
            config.proxy = proxy_url
        client = kubernetes.client.ApiClient(configuration=config)
        assert client
        yield client


def assert_default_release_channel(release_channel: container_v1.ReleaseChannel | None) -> None:
    """Raise an AssertionError if the release channel does not meet default module expectations."""
    assert release_channel
    assert release_channel.channel == container_v1.ReleaseChannel.Channel.REGULAR


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
    cluster_range_name: str | None = None,
    services_range_name: str | None = None,
) -> None:
    """Raise an AssertionError if the IPAllocationPolicy object does not meet default module expectations."""
    assert ip_allocation_policy
    if not cluster_range_name:
        cluster_range_name = "pods"
    if not services_range_name:
        services_range_name = "services"
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
    assert control_plane_endpoints_config.dns_endpoint_config.allow_external_traffic
    assert not control_plane_endpoints_config.ip_endpoints_config.enabled
    assert not control_plane_endpoints_config.ip_endpoints_config.enable_public_endpoint
    assert not control_plane_endpoints_config.ip_endpoints_config.global_access
    assert not control_plane_endpoints_config.ip_endpoints_config.private_endpoint
    assert not control_plane_endpoints_config.ip_endpoints_config.authorized_networks_config


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
    assert not cluster_autoscaling.enable_node_autoprovisioning
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


def match_exists(obj: object) -> bool:
    """Return True if obj asserts; use when watched resources having any value is a success."""
    assert obj
    return True


def match_metadata_name(name: str) -> Callable[[object], bool]:
    """Return a function that can be called to test if an object has a metadata property matching name parameter."""
    assert name, "name parameter is required"

    def _matcher(obj: object) -> bool:
        assert obj
        metadata = (
            cast("kubernetes.client.V1ObjectMeta", obj.metadata)
            if hasattr(obj, "metadata")
            else kubernetes.client.V1ObjectMeta()
        )
        assert metadata
        if not metadata.name:
            return False
        return metadata.name == name

    return _matcher


def watcher(lister: Callable, matcher: Callable[[object], bool], **kwargs) -> bool:  # noqa: ANN003
    """Execute a watch for objects returned from call to lister, testing each found object with matcher."""
    found_resource = False
    watcher = kubernetes.watch.Watch()
    for event in watcher.stream(func=lister, **kwargs):
        if event["type"] not in ACTIONABLE_WATCHER_TYPES:
            continue
        if matcher(event["object"]):
            watcher.stop()
            found_resource = True
    return found_resource


def assert_namespace(
    client: kubernetes.client.ApiClient,
    namespace: str,
    timeout_seconds: int = 180,
    request_timeout: int = 10,
) -> None:
    """Raise an AssertionError if the Namespace for the cluster is not found."""
    assert namespace, "namespace parameter is required"
    core_v1 = kubernetes.client.CoreV1Api(api_client=client)
    assert watcher(
        lister=core_v1.list_namespace,
        matcher=match_metadata_name(name=namespace),
        timeout_seconds=timeout_seconds,
        _request_timeout=request_timeout,
    ), f"Namespace {namespace} not found"


def assert_any_labelled_service_exists(
    client: kubernetes.client.ApiClient,
    namespace: str,
    label_selector: str,
    timeout_seconds: int = 180,
    request_timeout: int = 10,
) -> None:
    """Raise an AssertionError if no matching services are found in the namespace."""
    assert namespace, "namespace parameter is required"
    assert label_selector, "label_selector parameter is required"
    core_v1 = kubernetes.client.CoreV1Api(api_client=client)
    assert watcher(
        lister=core_v1.list_namespaced_service,
        matcher=match_exists,
        timeout_seconds=timeout_seconds,
        _request_timeout=request_timeout,
        namespace=namespace,
        label_selector=label_selector,
    ), "Expected at least one service to match label selector, found none"
