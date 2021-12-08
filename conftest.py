"""configures pytest"""
import pytest
from _pytest.config import Config
from pytest_cov.plugin import CovPlugin


@pytest.mark.tryfirst
def pytest_configure(config: Config) -> None:
    """Setup default pytest options."""
    config.option.newfirst = True
    config.option.failedfirst = True
    config.option.tbstyle = "short"
    config.option.durations = 0
    config.option.durations_min = 1

    config.option.pylint = True
    config.option.black = True
    config.option.isort = True

    config.option.mypy = True
    config.option.mypy_ignore_missing_imports = True
    config.pluginmanager.getplugin("mypy").mypy_argv.extend(
        ["--strict", "--implicit-reexport"]
    )

    config.option.mccabe = True
    config.addinivalue_line("mccabe-complexity", "3")

    config.option.cov_source = ["tools"]
    config.option.cov_fail_under = 100
    config.option.cov_report = {
        "term-missing": None,
        "html": "cov_html",
    }
    config.option.cov_branch = True
    config.pluginmanager.register(
        CovPlugin(config.option, config.pluginmanager), "_cov"
    )
