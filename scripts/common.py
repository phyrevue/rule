#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Iterable

RULE_ORDER = {
    "DOMAIN": 0,
    "DOMAIN-SUFFIX": 1,
    "DOMAIN-KEYWORD": 2,
    "DOMAIN-WILDCARD": 3,
    "DOMAIN-REGEX": 4,
    "IP-CIDR": 5,
    "IP-CIDR6": 6,
    "IP-ASN": 7,
    "PROCESS-NAME": 8,
    "USER-AGENT": 9,
}

COUNT_KEYS = [
    "DOMAIN",
    "DOMAIN-SUFFIX",
    "DOMAIN-KEYWORD",
    "DOMAIN-WILDCARD",
    "DOMAIN-REGEX",
    "IP-CIDR",
    "IP-CIDR6",
    "IP-ASN",
    "PROCESS-NAME",
    "USER-AGENT",
]

SUPPORTED_RULE_TYPES = set(COUNT_KEYS)
IGNORED_RULE_TYPES = {"OR"}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_config(root: Path) -> dict:
    return json.loads((root / "config" / "rulesets.json").read_text())


def utc_now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")


def parse_rules(path: Path) -> list[str]:
    rules: list[str] = []
    for raw in path.read_text(errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        rule_type = line.split(",", 1)[0]
        if rule_type in IGNORED_RULE_TYPES:
            continue
        if rule_type not in SUPPORTED_RULE_TYPES:
            continue
        rules.append(line)
    return rules


def sort_key(rule: str) -> tuple[int, str, str]:
    rule_type, _, rest = rule.partition(",")
    return (RULE_ORDER.get(rule_type, 99), rule_type, rest)


def sorted_rules(rules: Iterable[str]) -> list[str]:
    return sorted(set(rules), key=sort_key)


def count_rules(rules: Iterable[str]) -> Counter:
    return Counter(rule.split(",", 1)[0] for rule in rules)


def build_header(
    *,
    name: str,
    display_name: str,
    priority: int,
    updated: str,
    counts: Counter,
    source_lines: list[str],
    extra_lines: list[str] | None = None,
) -> list[str]:
    header = [
        f"# NAME: {name}",
        f"# DISPLAY: {display_name}",
        "# AUTHOR: phyrevue",
        "# REPO: https://github.com/phyrevue/rule",
        f"# PRIORITY: {priority}",
    ]
    header.extend(source_lines)
    if extra_lines:
        header.extend(extra_lines)
    header.append(f"# UPDATED: {updated}")
    for key in COUNT_KEYS:
        if counts.get(key):
            header.append(f"# {key}: {counts[key]}")
    header.append(f"# TOTAL: {sum(counts.values())}")
    return header


def write_list(path: Path, header: list[str], rules: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(header) + "\n" + "\n".join(rules) + "\n")


def ensure_git_clone(url: str, dest: Path) -> Path:
    if dest.exists():
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "clone", "--depth", "1", url, str(dest)], check=True)
    return dest
