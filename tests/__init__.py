"""Define functions common to all test cases in the tests namespace."""

import json
import os
import pathlib
import shutil
import subprocess
import tempfile
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any, cast

import google.api_core.extended_operation
import google.api_core.operation


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
def run_tf_in_workspace(
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


def handle_extended_operation(
    operation: google.api_core.operation.Operation | google.api_core.extended_operation.ExtendedOperation,
    timeout: int = 180,
) -> Any:  # noqa: ANN401
    """Watch the operation and raise an error if it indicates a failure."""
    result = operation.result(timeout=timeout)
    if isinstance(operation, google.api_core.extended_operation.ExtendedOperation):
        operation = cast("google.api_core.extended_operation.ExtendedOperation", operation)
        if operation.error_code:
            raise operation.exception() or RuntimeError(operation.error_message)
    return result
