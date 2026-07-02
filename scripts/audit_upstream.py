#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from common import ensure_git_clone, load_config, parse_rules, repo_root

IOS_REPO = "https://github.com/blackmatrix7/ios_rule_script.git"

AUDIT_TARGETS = {
    "YouTube": ["YouTubeMusic"],
    "Google": [
        "GoogleDrive",
        "GoogleFCM",
        "GoogleVoice",
        "GoogleSearch",
        "GoogleEarth",
    ],
    "Telegram": ["TelegramSG", "TelegramNL", "TelegramUS"],
    "Direct": ["ChinaDNS", "ChinaMaxNoIP", "ChinaIPs"],
}

INTENTIONAL_GAPS = {
    ("Direct", "ChinaIPs"): (
        "未合入完整 ChinaIPs。建议在 Clash/Mihomo 配置末尾使用 "
        "`GEOIP,CN,DIRECT` 覆盖中国大陆 IP，避免 rule-provider 过大。"
    ),
}


def resolve_ios_upstream(args: argparse.Namespace) -> Path:
    if args.ios_upstream:
        return Path(args.ios_upstream)
    dest = Path(args.workdir) / "ios_rule_script"
    return ensure_git_clone(IOS_REPO, dest)


def source_path(ios_root: Path, name: str) -> Path:
    return ios_root / "rule" / "Clash" / name / f"{name}.list"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ios-upstream", help="Path to blackmatrix7/ios_rule_script")
    parser.add_argument("--workdir", default="/tmp/rule-upstreams")
    args = parser.parse_args()

    root = repo_root()
    ios_root = resolve_ios_upstream(args)
    config = load_config(root)
    configured_sets = {
        category["name"]: category["source"].get("sets", [])
        for category in config["categories"]
        if category["source"]["type"] == "ios_rule_script"
    }

    lines = [
        "# Upstream Audit",
        "",
        "对 blackmatrix7/ios_rule_script 的 Clash 细分规则做精确集合比对。",
        "",
        "| 分类 | 上游细分 | 状态 | 上游规则 | 已覆盖 | 未覆盖 | 备注 |",
        "| --- | --- | --- | ---: | ---: | ---: | --- |",
    ]

    for category, sources in AUDIT_TARGETS.items():
        current_path = root / "rule" / "Clash" / category / f"{category}.list"
        current_rules = set(parse_rules(current_path)) if current_path.exists() else set()
        configured = set(configured_sets.get(category, []))

        for source in sources:
            path = source_path(ios_root, source)
            source_rules = set(parse_rules(path)) if path.exists() else set()
            missing = source_rules - current_rules
            covered = source in configured or not missing
            status = "included" if covered and not missing else "partial"
            note = "已合入配置" if source in configured else ""
            if (category, source) in INTENTIONAL_GAPS:
                status = "intentional"
                note = INTENTIONAL_GAPS[(category, source)]
            elif missing:
                sample = ", ".join(sorted(missing)[:3])
                note = f"示例缺失: `{sample}`"
            lines.append(
                "| {category} | {source} | {status} | {total} | {hit} | {miss} | {note} |".format(
                    category=category,
                    source=source,
                    status=status,
                    total=len(source_rules),
                    hit=len(source_rules & current_rules),
                    miss=len(missing),
                    note=note,
                )
            )

    lines.extend(
        [
            "",
            "说明：这里是规则文本的精确比对，不做 CIDR 包含关系推断。",
            "例如较大的网段已经覆盖较小网段时，仍可能在表格里显示为未覆盖。",
        ]
    )

    reports_dir = root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "upstream_audit.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
