"""Tests for repository governance, least privilege, and workflow security (G12)."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
GITHUB_DIR = ROOT / ".github"
WORKFLOWS_DIR = GITHUB_DIR / "workflows"


def test_codeowners_presence_and_coverage() -> None:
    """CODEOWNERS file exists and specifies default repository ownership."""
    codeowners_paths = [ROOT / "CODEOWNERS", GITHUB_DIR / "CODEOWNERS"]
    assert any(p.exists() for p in codeowners_paths), "CODEOWNERS must exist"

    content = (GITHUB_DIR / "CODEOWNERS").read_text(encoding="utf-8")
    assert "* @rehan1020" in content


def test_dependabot_ecosystems() -> None:
    """Dependabot configuration monitors both github-actions and pip."""
    dependabot_file = GITHUB_DIR / "dependabot.yml"
    assert dependabot_file.exists()

    config = yaml.safe_load(dependabot_file.read_text(encoding="utf-8"))
    assert config.get("version") == 2
    ecosystems = [entry.get("package-ecosystem") for entry in config.get("updates", [])]
    assert "github-actions" in ecosystems
    assert "pip" in ecosystems


def test_workflow_permissions_blocks_least_privilege() -> None:
    """All workflow files declare top-level or job-level least-privilege permissions."""
    workflow_files = list(WORKFLOWS_DIR.glob("*.yml"))
    assert len(workflow_files) >= 4

    for wf in workflow_files:
        content = wf.read_text(encoding="utf-8")
        parsed = yaml.safe_load(content)

        # Either top-level permissions or every job defines permissions
        has_top_level_perms = "permissions" in parsed
        if has_top_level_perms:
            perms = parsed["permissions"]
            assert isinstance(perms, dict)
            # Default read-only contents
            assert perms.get("contents") == "read"
        else:
            jobs = parsed.get("jobs", {})
            for job_name, job_def in jobs.items():
                if "uses" in job_def:
                    continue  # Reusable workflow caller inherits or delegates
                assert "permissions" in job_def, (
                    f"Job {job_name} in {wf.name} lacks permissions block"
                )


def test_workflow_actions_sha_pinning() -> None:
    """All external GitHub Action steps are pinned to full 40-character commit SHAs."""
    workflow_files = list(WORKFLOWS_DIR.glob("*.yml"))
    sha_regex = re.compile(r"^[0-9a-f]{40}$")

    for wf in workflow_files:
        content = wf.read_text(encoding="utf-8")
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("uses:") and not stripped.startswith("uses: ./"):
                # Format: uses: actions/checkout@<sha> # v4
                action_ref = stripped.split("uses:")[1].split("#")[0].strip()
                if "@" in action_ref:
                    _, tag_or_sha = action_ref.split("@", 1)
                    assert sha_regex.match(tag_or_sha), (
                        f"Action {action_ref} in {wf.name} is not pinned to a 40-char SHA"
                    )
