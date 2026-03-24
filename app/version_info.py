"""
Versão exibida na API e no painel: commit Git / tag / CI.

Ordem de resolução:
1. BUILD_VERSION — definido no pipeline (ex.: saída de `git describe --tags --always --dirty`)
2. Repositório local com .git — `git describe --tags --always --dirty`
3. Variáveis de commit comuns em CI (GITHUB_SHA, etc.) — APP_VERSION+sha curto, ou só o sha
4. APP_VERSION do .env (fallback)
"""
from __future__ import annotations

import os
import subprocess
from functools import lru_cache
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _git_output(args: list[str]) -> str | None:
    if not (_PROJECT_ROOT / ".git").exists():
        return None
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=_PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if proc.returncode != 0:
            return None
        out = (proc.stdout or "").strip()
        return out or None
    except (OSError, subprocess.TimeoutExpired):
        return None


def _short_sha(full: str) -> str:
    s = full.strip()
    if len(s) >= 7:
        head = s[:7]
        if all(c in "0123456789abcdefABCDEF" for c in head):
            return head.lower()
    return s[:12] if len(s) > 12 else s


def _sha_from_ci_env() -> str | None:
    for key in (
        "GITHUB_SHA",
        "GIT_COMMIT",
        "SOURCE_COMMIT",
        "COOLIFY_COMMIT_SHA",
        "VERCEL_GIT_COMMIT_SHA",
        "COMMIT_SHA",
        "CI_COMMIT_SHA",
    ):
        raw = os.environ.get(key, "").strip()
        if raw:
            return _short_sha(raw)
    return None


@lru_cache(maxsize=1)
def get_display_version(app_version_fallback: str) -> str:
    """
    Versão mostrada em /health, /branding e no painel.
    `app_version_fallback` vem de Settings.APP_VERSION (.env).
    """
    build_v = os.environ.get("BUILD_VERSION", "").strip()
    if build_v:
        return build_v

    describe = _git_output(["describe", "--tags", "--always", "--dirty"])
    if describe:
        return describe

    sha = _sha_from_ci_env()
    if sha:
        fb = (app_version_fallback or "").strip()
        if fb and fb != "0.0.0":
            return f"{fb}+{sha}"
        return sha

    return (app_version_fallback or "0.0.0").strip() or "0.0.0"
