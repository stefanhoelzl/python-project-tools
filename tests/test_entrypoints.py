# pylint: disable=missing-module-docstring,missing-function-docstring,unused-argument,redefined-outer-name
import subprocess

import pytest


@pytest.mark.parametrize("entrypoint", ["release", "requirements"])
def test_entrypoints(entrypoint: str) -> None:
    subprocess.run([entrypoint], check=True)
