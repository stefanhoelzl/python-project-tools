"""Script to update the requirements"""
from pathlib import Path
from typing import Generator, NamedTuple, Optional

import fire
import requests


class Requirement(NamedTuple):
    """container for requirement informations."""

    name: str
    version: str
    source: Path

    def __str__(self) -> str:
        return f"{self.name}=={self.version} ({str(self.source)})"


class Update(NamedTuple):
    """container for update infomrations."""

    requirement: Requirement
    version: str

    def __str__(self) -> str:
        return f"{self.requirement.name}: {self.requirement.version} => {self.version}"


def update() -> Generator[Update, None, None]:
    """Updates all requirements to its latest versions."""
    for updt in get_updates():
        updt.requirement.source.write_text(
            updt.requirement.source.read_text().replace(
                f"{updt.requirement.name}=={updt.requirement.version}",
                f"{updt.requirement.name}=={updt.version}",
            )
        )
        yield updt


def get_updates() -> Generator[Update, None, None]:
    """Gets all available updates."""
    for requirement in get():
        package_info = requests.get(
            f"https://www.pypi.org/pypi/{requirement.name}/json"
        ).json()
        latest_version = package_info["info"]["version"]
        if latest_version != requirement.version:
            yield Update(requirement, latest_version)


def get(
    requirements_txt: Optional[Path] = None,
) -> Generator[Requirement, None, None]:
    """Gets all defined requirements."""
    requirements_txt = requirements_txt or Path("requirements.txt")
    for requirement in _read_non_empty_lines(requirements_txt):
        if requirement.startswith("-r"):
            _, link = requirement.split(" ")
            yield from get(requirements_txt.parent / link)
        elif not _ignore_requirement(requirement):
            name, version = requirement.split("==", 1)
            yield Requirement(name, version, requirements_txt)


def _read_non_empty_lines(filepath: Path) -> Generator[str, None, None]:
    with open(str(filepath), mode="r", encoding="utf-8") as filehandle:
        for line in filehandle.readlines():
            line = line.strip()
            if line:
                yield line


def _ignore_requirement(requirement: str) -> bool:
    if requirement.startswith("git+"):
        return True
    if requirement.startswith("#"):
        return True
    return False


def main() -> None:
    """console entrypoint"""
    fire.Fire()
