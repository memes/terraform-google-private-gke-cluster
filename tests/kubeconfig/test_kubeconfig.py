"""Test fixture for multiple Kubeconfig module tests against the same cluster.

NOTE: The cluster is deployed with public and private endpoints so many variations of the module can be tested.
"""

import base64
import pathlib
import re
import subprocess
import tempfile
from collections.abc import Callable, Generator
from contextlib import _GeneratorContextManager, contextmanager
from typing import Any, cast

import kubernetes.client
import pytest
from google.cloud import compute_v1

from tests import (
    get_private_address,
    get_public_address,
    kubernetes_api_client,
    run_tf_plan_apply_destroy,
    wait_for_forward_proxy,
    watcher,
)

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
def cluster_output(
    autopilot_fixture_dir: Callable[[str], pathlib.Path],
    project_id: str,
    fixture_name: str,
    fixture_labels: dict[str, str],
    subnet_self_link: str,
    sa_fixture_output: dict[str, Any],
    bastion: compute_v1.Instance,
) -> Generator[dict[str, Any], None, None]:
    """Create GKE Autopilot cluster for test case."""
    service_account = cast("str", sa_fixture_output["email"])
    assert service_account
    with run_tf_plan_apply_destroy(
        fixture=autopilot_fixture_dir(f"{FIXTURE_NAME}-auto"),
        tfvars={
            "project_id": project_id,
            "name": fixture_name,
            "service_account": service_account,
            "subnet": {
                "self_link": subnet_self_link,
            },
            "labels": fixture_labels,
            "control_plane_access": {
                "enable_ip_access": True,
                "authorized_cidrs": [
                    {
                        "cidr_block": f"{get_private_address(bastion)}/32",
                        "display_name": "bastion",
                    },
                ],
            },
        },
    ) as output:
        yield output


@pytest.fixture(scope="module")
def cluster_id(
    cluster_output: dict[str, Any],
) -> str:
    """Return the GKE Cluster object matching the fixture output."""
    cluster_id = cast("str", cluster_output["id"])
    assert cluster_id
    return cluster_id


@pytest.fixture(scope="module")
def kubeconfig_builder(
    kubeconfig_fixture_dir: Callable[[str], pathlib.Path],
) -> Callable[[str, dict[str, Any]], _GeneratorContextManager[pathlib.Path, None, None]]:
    """Return a builder of kubeconfig files."""

    @contextmanager
    def _builder(name: str, tfvars: dict[str, Any]) -> Generator[pathlib.Path, None, None]:
        assert name
        assert tfvars
        with run_tf_plan_apply_destroy(
            fixture=kubeconfig_fixture_dir(f"{FIXTURE_NAME}-{name}"),
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


def test_default(
    kubeconfig_builder: Callable[[str, dict[str, Any]], _GeneratorContextManager[pathlib.Path, None, None]],
    cluster_id: str,
) -> None:
    """Create a default Kubeconfig for the cluster, verify that it can be used to connect to cluster."""
    with kubeconfig_builder("def", {"cluster_id": cluster_id}) as kubeconfig:
        exec_kubectl(kubeconfig=kubeconfig)


def test_default_with_proxy_url(
    kubeconfig_builder: Callable[[str, dict[str, Any]], _GeneratorContextManager[pathlib.Path, None, None]],
    cluster_id: str,
    bastion_proxy_url: str,
) -> None:
    """Create a default Kubeconfig for the cluster, verify that it can be used to connect to cluster via bastion."""
    with kubeconfig_builder(
        "def-proxy",
        {
            "cluster_id": cluster_id,
            "proxy_url": bastion_proxy_url,
        },
    ) as kubeconfig:
        exec_kubectl(kubeconfig=kubeconfig)


def test_private_ip_address_with_proxy_url(
    kubeconfig_builder: Callable[[str, dict[str, Any]], _GeneratorContextManager[pathlib.Path, None, None]],
    cluster_id: str,
    bastion_proxy_url: str,
) -> None:
    """Create a default Kubeconfig for the cluster, verify that it can be used to connect to cluster via bastion."""
    with kubeconfig_builder(
        "ip-proxy",
        {
            "cluster_id": cluster_id,
            "proxy_url": bastion_proxy_url,
            "use_private_endpoint": True,
        },
    ) as kubeconfig:
        exec_kubectl(kubeconfig=kubeconfig)


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
        if secret.metadata.name != name:
            return False
        data = cast("str", secret.data)
        return data != ""

    namespace = service_account.metadata.namespace
    core_v1 = kubernetes.client.CoreV1Api(api_client=api_client)
    try:
        secret = core_v1.create_namespaced_secret(
            namespace=namespace,
            body=kubernetes.client.V1Secret(
                metadata=kubernetes.client.V1ObjectMeta(
                    name=name,
                    namespace=namespace,
                    annotations={
                        "kubernetes.io/service-account.name": service_account.metadata.name,
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
                    name=cluster_role.metadata.name,
                ),
                subjects=[
                    kubernetes.client.RbacV1Subject(
                        kind=service_account.kind,
                        name=service_account.metadata.name,
                        namespace=service_account.metadata.namespace,
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
    cluster_output: dict[str, Any],
    bastion_proxy_url: str,
    fixture_name: str,
) -> None:
    """Create a token-based authentication Kubeconfig for a service account in the cluster, verify it.

    This is a common scenario when using F5XC Service Discovery, for example.
    """
    cluster_id = cluster_output["id"]
    assert cluster_id
    endpoint_url = cluster_output["dns_endpoint_url"]
    assert endpoint_url
    ca_cert = cluster_output["ca_cert"]
    assert ca_cert
    name = f"{fixture_name}-sa"
    with (
        kubernetes_api_client(host=endpoint_url) as client,
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
        token = base64.b64decode(secret.data["token"]).decode(encoding="utf-8")
        assert token
        workspace = name
        tfvars = {
            "cluster_id": cluster_id,
            "use_private_endpoint": True,
            "proxy_url": bastion_proxy_url,
            "user": {
                "name": sa.metadata.name,
                "token": token,
            },
        }
        with kubeconfig_builder(workspace, tfvars) as kubeconfig:
            exec_kubectl(kubeconfig=kubeconfig)
