#!/usr/bin/env python3
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from common import COUNT_KEYS, load_config, repo_root

FORBIDDEN_RULES = {
    "OverseasAI": {
        "DOMAIN-SUFFIX,google.com": "too broad; use specific Gemini/Bard/Google AI rules instead",
    }
}

EXPECTED_DOMAIN_MATCHES = {
    "chatgpt.com": "OverseasAI",
    "ab.chatgpt.com": "OverseasAI",
    "gemini.google.com": "OverseasAI",
    "gemini.gstatic.com": "OverseasAI",
    "aistudio.google.com": "OverseasAI",
    "generativelanguage.googleapis.com": "OverseasAI",
    "cloud.google.com": "OverseasAI",
    "deepmind.google": "OverseasAI",
    "www.google.com": "Google",
    "blogspot.am": "Google",
    "music.youtube.com": "YouTube",
    "drive.google.com": "Google",
    "sharepoint.com": "OneDrive",
    "telegram.org": "Telegram",
}


def read_rule_file(path: Path) -> tuple[list[str], list[str]]:
    header: list[str] = []
    rules: list[str] = []
    for raw in path.read_text(errors="ignore").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            header.append(line)
        else:
            rules.append(line)
    return header, rules


def parse_header_counts(header: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for line in header:
        match = re.match(r"# ([A-Z0-9-]+): (\d+)$", line)
        if match:
            counts[match.group(1)] = int(match.group(2))
    return counts


def domain_matches_rule(domain: str, rule: str) -> bool:
    parts = rule.split(",", 2)
    if len(parts) < 2:
        return False
    rule_type, value = parts[0], parts[1]
    if rule_type == "DOMAIN":
        return domain == value
    if rule_type == "DOMAIN-SUFFIX":
        return domain == value or domain.endswith(f".{value}")
    if rule_type == "DOMAIN-KEYWORD":
        return value in domain
    return False


def first_domain_match(domain: str, categories: list[str], rules_by_category: dict[str, set[str]]) -> str | None:
    for category in categories:
        if any(domain_matches_rule(domain, rule) for rule in rules_by_category.get(category, set())):
            return category
    return None


def main() -> None:
    root = repo_root()
    config = load_config(root)
    errors: list[str] = []
    rules_by_category: dict[str, set[str]] = {}

    for category in sorted(config["categories"], key=lambda item: item["priority"]):
        name = category["name"]
        path = root / "rule" / "Clash" / name / f"{name}.list"
        if not path.exists():
            errors.append(f"{name}: missing {path}")
            continue

        header, rules = read_rule_file(path)
        header_counts = parse_header_counts(header)
        actual_counts = Counter(rule.split(",", 1)[0] for rule in rules)
        duplicate_count = len(rules) - len(set(rules))
        unsupported_types = sorted(set(actual_counts) - set(COUNT_KEYS))
        if unsupported_types:
            errors.append(f"{name}: unsupported rule type(s): {', '.join(unsupported_types)}")

        for key in COUNT_KEYS:
            if actual_counts.get(key) and header_counts.get(key) != actual_counts[key]:
                errors.append(
                    f"{name}: header {key}={header_counts.get(key)} actual={actual_counts[key]}"
                )
        if header_counts.get("TOTAL") != len(rules):
            errors.append(f"{name}: header TOTAL={header_counts.get('TOTAL')} actual={len(rules)}")
        if duplicate_count:
            errors.append(f"{name}: {duplicate_count} duplicate rule(s)")

        for rule, reason in FORBIDDEN_RULES.get(name, {}).items():
            if rule in rules:
                errors.append(f"{name}: forbidden rule {rule} ({reason})")

        rules_by_category[name] = set(rules)

    exact_overlaps: dict[tuple[str, str], int] = {}
    categories = [category["name"] for category in sorted(config["categories"], key=lambda item: item["priority"])]
    for index, name in enumerate(categories):
        for other in categories[index + 1 :]:
            overlap = rules_by_category.get(name, set()) & rules_by_category.get(other, set())
            if overlap:
                exact_overlaps[(name, other)] = len(overlap)

    if exact_overlaps:
        print("Exact cross-category overlaps:")
        for (name, other), count in exact_overlaps.items():
            print(f"- {name} / {other}: {count}")

    for domain, expected_category in EXPECTED_DOMAIN_MATCHES.items():
        actual_category = first_domain_match(domain, categories, rules_by_category)
        if actual_category != expected_category:
            errors.append(
                f"{domain}: expected first match {expected_category}, got {actual_category or 'none'}"
            )

    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print("Validation passed.")


if __name__ == "__main__":
    main()
