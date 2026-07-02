#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from common import (
    build_header,
    count_rules,
    ensure_git_clone,
    load_config,
    parse_rules,
    repo_root,
    sorted_rules,
    utc_now,
    write_list,
)

IOS_REPO = "https://github.com/blackmatrix7/ios_rule_script.git"
AI_REPO = "https://github.com/viewer12/OverseasAI.list.git"


def source_lines_for(category: dict) -> list[str]:
    source = category["source"]
    if source["type"] == "overseas_ai":
        return [
            "# SOURCE: https://github.com/viewer12/OverseasAI.list",
            f"# SOURCE-PATH: {source['path']}",
        ]
    sets = ", ".join(source.get("sets", []))
    return [
        "# SOURCE: https://github.com/blackmatrix7/ios_rule_script (rule/Clash)",
        f"# SOURCE-SETS: {sets}",
    ]


def resolve_upstreams(args: argparse.Namespace) -> tuple[Path, Path]:
    workdir = Path(args.workdir)
    ios_root = Path(args.ios_upstream) if args.ios_upstream else workdir / "ios_rule_script"
    ai_root = Path(args.ai_upstream) if args.ai_upstream else workdir / "OverseasAI.list"

    if not args.ios_upstream:
        ensure_git_clone(IOS_REPO, ios_root)
    if not args.ai_upstream:
        ensure_git_clone(AI_REPO, ai_root)

    return ios_root, ai_root


def load_source_rules(category: dict, ios_root: Path, ai_root: Path) -> list[str]:
    source = category["source"]
    if source["type"] == "overseas_ai":
        source_path = ai_root / source["path"]
        if not source_path.exists():
            raise SystemExit(f"Missing OverseasAI source: {source_path}")
        return parse_rules(source_path)

    if source["type"] == "ios_rule_script":
        rules: list[str] = []
        for name in source["sets"]:
            source_path = ios_root / "rule" / "Clash" / name / f"{name}.list"
            if not source_path.exists():
                raise SystemExit(f"Missing ios_rule_script source: {source_path}")
            rules.extend(parse_rules(source_path))
        return rules

    raise SystemExit(f"Unsupported source type: {source['type']}")


def ensure_custom_file(path: Path, category: dict) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                f"# NAME: {category['name']}_Custom",
                f"# DISPLAY: {category['display_name']} 自定义补充",
                "# Add one rule per line, for example:",
                "# DOMAIN-SUFFIX,example.com",
            ]
        )
        + "\n"
    )


def sync_category(root: Path, category: dict, ios_root: Path, ai_root: Path, updated: str) -> None:
    name = category["name"]
    clash_dir = root / "rule" / "Clash" / name
    custom_path = clash_dir / f"{name}_Custom.list"

    ensure_custom_file(custom_path, category)

    source_rules = load_source_rules(category, ios_root, ai_root)
    custom_rules = parse_rules(custom_path)
    exclude_rules = set(category.get("exclude_rules", []))
    rules = sorted_rules(rule for rule in [*source_rules, *custom_rules] if rule not in exclude_rules)
    counts = count_rules(rules)
    source_lines = source_lines_for(category)
    extra_lines = [f"# CUSTOM: rule/Clash/{name}/{name}_Custom.list"]

    header = build_header(
        name=name,
        display_name=category["display_name"],
        priority=category["priority"],
        updated=updated,
        counts=counts,
        source_lines=source_lines,
        extra_lines=extra_lines,
    )
    write_list(clash_dir / f"{name}.list", header, rules)

    print(f"[Sync] {name}: {sum(counts.values())} rule(s)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ios-upstream", help="Path to blackmatrix7/ios_rule_script")
    parser.add_argument("--ai-upstream", help="Path to viewer12/OverseasAI.list")
    parser.add_argument("--workdir", default="/tmp/rule-upstreams")
    args = parser.parse_args()

    root = repo_root()
    config = load_config(root)
    ios_root, ai_root = resolve_upstreams(args)
    updated = utc_now()

    for category in sorted(config["categories"], key=lambda item: item["priority"]):
        sync_category(root, category, ios_root, ai_root, updated)


if __name__ == "__main__":
    main()
