"""Reusable Kubernetes resource assertions."""

from collections.abc import Callable
from typing import cast

import kubernetes.client
import kubernetes.watch

ACTIONABLE_WATCHER_TYPES = ["ADDED", "MODIFIED"]


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
            cast("kubernetes.client.V1ObjectMeta", obj.metadata)  # pyright: ignore[reportAttributeAccessIssue]
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
        if event["type"] not in ACTIONABLE_WATCHER_TYPES:  # pyright: ignore[reportArgumentType,reportOptionalSubscript]
            continue
        if matcher(event["object"]):  # pyright: ignore[reportArgumentType,reportOptionalSubscript]
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
