"""
Everything needed to create new releases.
"""
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Generator, Iterable, List, NamedTuple, Optional

import fire
import toml
from semver import VersionInfo

CategoryKeywords = {
    "Features": "feature",
    "Bugfixes": "bugfix",
    "Internal": "internal",
    "Tooling": "tooling",
    "Documentation": "docs",
}
ChangelogCategories = ["Features", "Bugfixes", "Internal"]
CommitMessageRegex = re.compile(
    rf"\[(?P<category>{'|'.join(CategoryKeywords.values())})\] (?P<message>.*)"
)


class Config(NamedTuple):
    """Global Configuration"""

    @classmethod
    def load(cls) -> "Config":
        """Loads a configuration from pyproject.toml"""
        config_file = Path("pyproject.toml")
        if config_file.is_file():
            config_dict = (
                toml.loads(config_file.read_text(encoding="utf-8"))
                .get("tool", {})
                .get("python-project-tools", {})
            )
            return cls(
                **{key.replace("-", "_"): value for key, value in config_dict.items()}
            )
        return cls()

    start_commit: Optional[str] = None


def release_candidate() -> None:
    """
    Sets the release-candidate tag and pushes it to the default branch
    to trigger a new release.
    """
    print(_git("fetch"))

    match = re.search(
        "HEAD branch: (.*)", _git("remote", "show", "origin", check=False)
    )
    if match is None:
        raise RuntimeError("could not determine default branch")

    print(_git("diff", "--exit-code", f"origin/{match.group(1)}"))
    print(_git("tag", "--force", "release-candidate"))
    print(_git("push", "origin", "release-candidate"))


def check_commit_messages() -> Generator[str, None, None]:
    """Checks if the all commit messages in the log are valid."""
    invalid_messages = _commits_by_category(_commits_since(commit_hash=None)).get(
        None, []
    )
    yield from (f"Invalid commit message: {msg}" for msg in invalid_messages)
    if invalid_messages:
        sys.exit(1)


def changelog() -> Generator[str, None, None]:
    """Creates a changelog from git history."""
    yield from _formatted_commits_by_category(
        _commits_by_category(_commits_since(_latest_version().commit_hash))
    )


def version() -> str:
    """Generates version from git history."""
    latest_version = _latest_version()
    commit_categories = _commits_by_category(
        _commits_since(latest_version.commit_hash)
    ).keys()
    new_version = latest_version.version.next_version(
        "minor" if "feature" in commit_categories else "patch"
    )
    current_commit_hash = _git("log", "--pretty=%h", "--max-count=1")
    dev_version_postfix = (
        f"+{current_commit_hash}"
        if os.environ.get("GITHUB_REF") != "refs/tags/release-candidate"
        else ""
    )
    return f"{new_version}{dev_version_postfix}"


_CommitsByCategory = Dict[Optional[str], List[str]]


class _VersionTag(NamedTuple):
    version: VersionInfo
    commit_hash: Optional[str]


def _git(*args: str, check: bool = True) -> str:
    return (
        subprocess.run(["git", *args], stdout=subprocess.PIPE, check=check)
        .stdout.decode("utf-8")
        .strip()
    )


def _versions() -> Dict[VersionInfo, str]:
    return {
        VersionInfo.parse(tag.lstrip("v")): commit
        for tag, commit in map(
            lambda l: l.split(";"),
            filter(
                bool,
                _git("tag", "--list", "v*", "--format=%(refname:strip=2);%(objectname)")
                .strip()
                .split("\n"),
            ),
        )
    }


def _latest_version() -> _VersionTag:
    versions = _versions()
    latest_version = max(versions) if versions else VersionInfo.parse("0.0.0")
    return _VersionTag(version=latest_version, commit_hash=versions.get(latest_version))


def _commits_since(commit_hash: Optional[str]) -> Iterable[str]:
    commit_hash = commit_hash or Config.load().start_commit
    cmd = ["log", "--pretty=%s"]
    if commit_hash:
        cmd.append(f"HEAD...{commit_hash}")
    return reversed(_git(*cmd).split("\n"))


def _commits_by_category(commits: Iterable[str]) -> _CommitsByCategory:
    commits_by_category: _CommitsByCategory = defaultdict(list)
    for msg in commits:
        match = re.match(CommitMessageRegex, msg)
        if match:
            commits_by_category[match.group("category")].append(match.group("message"))
        else:
            commits_by_category[None].append(msg)
    return commits_by_category


def _formatted_commits_by_category(
    commits_by_category: _CommitsByCategory,
) -> Generator[str, None, None]:
    for category, keyword in CategoryKeywords.items():
        if category in ChangelogCategories and len(commits_by_category[keyword]) > 0:
            yield from _formatted_category(category, commits_by_category[keyword])


def _formatted_category(
    category: str, commits: List[str]
) -> Generator[str, None, None]:
    yield f"* {category}"
    for message in commits:
        yield f"  * {message}"


def main() -> None:
    """console entrypoint"""
    fire.Fire()
