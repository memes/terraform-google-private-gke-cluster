"""Test fixture for multiple Kubeconfig module tests against the same cluster.

NOTE: The cluster is deployed with public and private endpoints so many variations of the module can be tested.
"""

import pathlib
import re
import subprocess
import tempfile
from collections.abc import Callable, Generator
from contextlib import _GeneratorContextManager, contextmanager
from typing import Any, cast

import kubernetes.client
import pytest

from .conftest import kubernetes_api_client, run_tofu_in_workspace
from .kubernetes_assertions import watcher

FIXTURE_NAME = "kubeconfig"
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
        },
    ) as output:
        yield output


@pytest.fixture(scope="module")
def autopilot_fixture_output(
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
    subnet = subnet | {
        "master_cidr": "192.168.0.0/28",
    }
    my_address = vpc_fixture_output["my_address"]
    assert my_address
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
                {
                    "cidr_block": f"{my_address}/32",
                    "display_name": "test host",
                },
            ],
            "labels": fixture_labels,
            "options": {
                "release_channel": "STABLE",
                "master_global_access": True,
                "etcd_kms": None,
                "private_endpoint": False,
                "default_snat": True,
                "deletion_protection": False,
            },
        },
    ) as output:
        yield output


@pytest.fixture(scope="module")
def kubeconfig_builder(
    kubeconfig_fixture_dir: pathlib.Path,
) -> Callable[[str, dict[str, Any]], _GeneratorContextManager[pathlib.Path, None, None]]:
    """Return a builder of kubeconfig files."""

    @contextmanager
    def _builder(workspace: str, tfvars: dict[str, Any]) -> Generator[pathlib.Path, None, None]:
        assert workspace
        assert tfvars
        with run_tofu_in_workspace(
            fixture=kubeconfig_fixture_dir,
            workspace=workspace,
            tfvars=tfvars,
        ) as output:
            assert output
            assert output["kubeconfig"]
            with tempfile.NamedTemporaryFile(
                mode="w+t",
                prefix="kubeconfig",
                suffix=".yaml",
                delete_on_close=False,
                delete=True,
            ) as kubeconfig:
                kubeconfig.write(output["kubeconfig"])
                kubeconfig.close()
                yield pathlib.Path(kubeconfig.name)

    return _builder


def exec_kubectl(kubeconfig: pathlib.Path, cluster_arg: str | None = None, context_arg: str | None = None) -> None:
    """Run the kubectl commands to verify connectivity to cluster.

    Verify the kube-system namespace exists, then look for any cluster services in it.
    """
    watch_namespace_args = [
        "kubectl",
        "--kubeconfig",
        f"{kubeconfig!s}",
        "--request-timeout",
        "10s",
    ]
    if cluster_arg:
        watch_namespace_args.extend(
            [
                "--cluster",
                cluster_arg,
            ],
        )
    if context_arg:
        watch_namespace_args.extend(
            [
                "--context",
                context_arg,
            ],
        )
    watch_services_args = watch_namespace_args[:]
    watch_namespace_args.extend(
        [
            "wait",
            "--for",
            "jsonpath={.status.phase}=Active",
            "namespace",
            "kube-system",
        ],
    )
    watch_services_args.extend(
        [
            "wait",
            "--for",
            "jsonpath={.status.loadBalancer}",
            "services",
            "--namespace",
            "kube-system",
            "--selector",
            "kubernetes.io/cluster-service=true",
        ],
    )
    process = subprocess.run(watch_namespace_args, check=True, capture_output=True)
    assert re.search(pattern=r"^namespace/kube-system condition met", string=process.stdout.decode("utf-8"))
    process = subprocess.run(watch_services_args, check=True, capture_output=True)
    matches = re.search(
        pattern=r"^service/.*condition met",
        string=process.stdout.decode("utf-8"),
        flags=re.MULTILINE,
    )
    assert matches


def test_minimal(
    kubeconfig_builder: Callable[[str, dict[str, Any]], _GeneratorContextManager[pathlib.Path, None, None]],
    autopilot_fixture_output: dict[str, Any],
) -> None:
    """Create a minimal Kubeconfig for the cluster, verify that it cannot be used to connect to cluster."""
    cluster_id = autopilot_fixture_output["id"]
    assert cluster_id
    workspace = f"{FIXTURE_NAME}-min"
    tfvars = {
        "cluster_id": cluster_id,
    }
    with (
        kubeconfig_builder(workspace, tfvars) as kubeconfig,
        pytest.raises(subprocess.CalledProcessError),
    ):
        exec_kubectl(kubeconfig=kubeconfig)


def test_minimal_with_proxy_url(
    kubeconfig_builder: Callable[[str, dict[str, Any]], _GeneratorContextManager[pathlib.Path, None, None]],
    autopilot_fixture_output: dict[str, Any],
    vpc_fixture_output: dict[str, Any],
) -> None:
    """Create a minimal Kubeconfig for the cluster, verify that it cannot be used to connect to cluster."""
    cluster_id = autopilot_fixture_output["id"]
    assert cluster_id
    bastion_public_ip_address = vpc_fixture_output["bastion_public_ip_address"]
    assert bastion_public_ip_address
    workspace = f"{FIXTURE_NAME}-min-proxy"
    tfvars = {
        "cluster_id": cluster_id,
        "proxy_url": f"http://{bastion_public_ip_address}:8888",
    }
    with kubeconfig_builder(workspace, tfvars) as kubeconfig:
        exec_kubectl(kubeconfig=kubeconfig)


def test_public_endpoint(
    kubeconfig_builder: Callable[[str, dict[str, Any]], _GeneratorContextManager[pathlib.Path, None, None]],
    autopilot_fixture_output: dict[str, Any],
) -> None:
    """Create a minimal Kubeconfig for the cluster, verify that it cannot be used to connect to cluster."""
    cluster_id = autopilot_fixture_output["id"]
    assert cluster_id
    workspace = f"{FIXTURE_NAME}-public"
    tfvars = {
        "cluster_id": cluster_id,
        "use_private_endpoint": False,
    }
    with kubeconfig_builder(workspace, tfvars) as kubeconfig:
        exec_kubectl(kubeconfig=kubeconfig)


def test_public_with_cluster_name(
    kubeconfig_builder: Callable[[str, dict[str, Any]], _GeneratorContextManager[pathlib.Path, None, None]],
    autopilot_fixture_output: dict[str, Any],
) -> None:
    """Create a minimal Kubeconfig for the cluster, verify that it can connect to API."""
    cluster_id = autopilot_fixture_output["id"]
    assert cluster_id
    workspace = f"{FIXTURE_NAME}-public-cluster-name"
    tfvars = {
        "cluster_id": cluster_id,
        "use_private_endpoint": False,
        "cluster_name": "test-cluster",
    }
    with kubeconfig_builder(workspace, tfvars) as kubeconfig:
        exec_kubectl(kubeconfig=kubeconfig, cluster_arg="test-cluster")


def test_public_with_context_name(
    kubeconfig_builder: Callable[[str, dict[str, Any]], _GeneratorContextManager[pathlib.Path, None, None]],
    autopilot_fixture_output: dict[str, Any],
) -> None:
    """Create a minimal Kubeconfig for the cluster, verify that it can connect to API."""
    cluster_id = autopilot_fixture_output["id"]
    assert cluster_id
    workspace = f"{FIXTURE_NAME}-public-context-name"
    tfvars = {
        "cluster_id": cluster_id,
        "use_private_endpoint": False,
        "context_name": "test-context",
    }
    with kubeconfig_builder(workspace, tfvars) as kubeconfig:
        exec_kubectl(kubeconfig=kubeconfig, context_arg="test-context")


@contextmanager
def service_account(
    api_client: kubernetes.client.ApiClient,
    name: str,
    namespace: str = "default",
) -> Generator[kubernetes.client.V1ServiceAccount, None, None]:
    """Create a named service account with deletion after use."""
    core_v1 = kubernetes.client.CoreV1Api(api_client=api_client)
    try:
        service_account = core_v1.create_namespaced_service_account(
            namespace="default",
            body=kubernetes.client.V1ServiceAccount(
                metadata=kubernetes.client.V1ObjectMeta(
                    name=name,
                    namespace="default",
                ),
            ),
        )
        assert service_account
        service_account = cast("kubernetes.client.V1ServiceAccount", service_account)
        yield service_account
    finally:
        _ = core_v1.delete_namespaced_service_account(
            name=name,
            namespace=namespace,
        )


@contextmanager
def service_account_token_secret(
    api_client: kubernetes.client.ApiClient,
    name: str,
    service_account: kubernetes.client.V1ServiceAccount,
) -> Generator[kubernetes.client.V1Secret, None, None]:
    """Create a service account token secret with deletion after use."""

    def secret_ready(obj: object) -> bool:
        """Return True if the secret exists and has a value for data field."""
        assert obj
        secret = cast("kubernetes.client.V1Secret", obj)
        if secret.metadata.name != name:  # pyright: ignore[reportOptionalMemberAccess]
            return False
        data = cast("str", secret.data)
        return data != ""

    namespace = service_account.metadata.namespace  # pyright: ignore[reportOptionalMemberAccess]
    core_v1 = kubernetes.client.CoreV1Api(api_client=api_client)
    try:
        secret = core_v1.create_namespaced_secret(
            namespace=namespace,
            body=kubernetes.client.V1Secret(
                metadata=kubernetes.client.V1ObjectMeta(
                    name=name,
                    namespace=namespace,
                    annotations={
                        "kubernetes.io/service-account.name": service_account.metadata.name,  # pyright: ignore[reportOptionalMemberAccess]
                    },
                ),
                type="kubernetes.io/service-account-token",
            ),
        )
        assert secret
        assert watcher(lister=core_v1.list_namespaced_secret, matcher=secret_ready, namespace=namespace)
        secret = core_v1.read_namespaced_secret(
            name=name,
            namespace=namespace,
        )
        assert secret
        secret = cast("kubernetes.client.V1Secret", secret)
        yield secret
    finally:
        _ = core_v1.delete_namespaced_secret(
            name=name,
            namespace=namespace,
        )


@contextmanager
def cluster_role(
    api_client: kubernetes.client.ApiClient,
    name: str,
) -> Generator[kubernetes.client.V1ClusterRole, None, None]:
    """Create a ClusterRole to list namespaces and services with deletion after use."""
    rbac_v1 = kubernetes.client.RbacAuthorizationV1Api(api_client=api_client)
    try:
        cluster_role = rbac_v1.create_cluster_role(
            body=kubernetes.client.V1ClusterRole(
                metadata=kubernetes.client.V1ObjectMeta(
                    name=name,
                ),
                rules=[
                    kubernetes.client.V1PolicyRule(
                        api_groups=[""],
                        resources=[
                            "namespaces",
                            "services",
                        ],
                        verbs=[
                            "get",
                            "list",
                            "watch",
                        ],
                    ),
                ],
            ),
        )
        assert cluster_role
        cluster_role = cast("kubernetes.client.V1ClusterRole", cluster_role)
        yield cluster_role
    finally:
        _ = rbac_v1.delete_cluster_role(
            name=name,
        )


@contextmanager
def cluster_role_binding(
    api_client: kubernetes.client.ApiClient,
    name: str,
    cluster_role: kubernetes.client.V1ClusterRole,
    service_account: kubernetes.client.V1ServiceAccount,
) -> Generator[kubernetes.client.V1ClusterRoleBinding, None, None]:
    """Create a ClusterRoleBinding of ClusterRole to ServiceAccount with deletion after use."""
    rbac_v1 = kubernetes.client.RbacAuthorizationV1Api(api_client=api_client)
    try:
        cluster_role_binding = rbac_v1.create_cluster_role_binding(
            body=kubernetes.client.V1ClusterRoleBinding(
                metadata=kubernetes.client.V1ObjectMeta(
                    name=name,
                ),
                role_ref=kubernetes.client.V1RoleRef(
                    api_group="rbac.authorization.k8s.io",
                    kind=cluster_role.kind,
                    name=cluster_role.metadata.name,  # pyright: ignore[reportOptionalMemberAccess]
                ),
                subjects=[
                    kubernetes.client.RbacV1Subject(
                        kind=service_account.kind,
                        name=service_account.metadata.name,  # pyright: ignore[reportOptionalMemberAccess]
                        namespace=service_account.metadata.namespace,  # pyright: ignore[reportOptionalMemberAccess]
                    ),
                ],
            ),
        )
        assert cluster_role_binding
        cluster_role_binding = cast("kubernetes.client.V1ClusterRoleBinding", cluster_role_binding)
        yield cluster_role_binding
    finally:
        _ = rbac_v1.delete_cluster_role_binding(
            name=name,
        )


def test_sa_access(
    kubeconfig_builder: Callable[[str, dict[str, Any]], _GeneratorContextManager[pathlib.Path, None, None]],
    autopilot_fixture_output: dict[str, Any],
    fixture_name: str,
) -> None:
    """Create a token-based authentication Kubeconfig for a service account in the cluster, verify it.

    This is a common scenario when using F5XC Service Discovery, for example.
    """
    cluster_id = autopilot_fixture_output["id"]
    assert cluster_id
    endpoint_url = autopilot_fixture_output["public_endpoint_url"]
    assert endpoint_url
    ca_cert = autopilot_fixture_output["ca_cert"]
    assert ca_cert
    name = f"{fixture_name}-sa"
    with (
        kubernetes_api_client(host=endpoint_url, ca=ca_cert) as client,
        service_account(api_client=client, name=name) as sa,
        service_account_token_secret(api_client=client, name=name, service_account=sa) as secret,
        cluster_role(api_client=client, name=name) as role,
        cluster_role_binding(
            api_client=client,
            name=name,
            cluster_role=role,
            service_account=sa,
        ) as binding,
    ):
        assert binding
        assert secret
        assert secret.data
        token = secret.data["token"]
        assert token
        workspace = name
        tfvars = {
            "cluster_id": cluster_id,
            "use_private_endpoint": False,
            "user": {
                "name": sa.metadata.name,  # pyright: ignore[reportOptionalMemberAccess]
                "token": token,
            },
        }
        with kubeconfig_builder(workspace, tfvars) as kubeconfig:
            exec_kubectl(kubeconfig=kubeconfig)
