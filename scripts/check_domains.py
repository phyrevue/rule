#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Iterable

import dns.exception
import dns.resolver

from common import load_config, parse_rules, repo_root

RESOLVERS = ["1.1.1.1", "8.8.8.8"]
THRESHOLD = 3
MAX_WORKERS = 20
RULE_TYPES_CHECK = {"DOMAIN", "DOMAIN-SUFFIX"}


def iter_domains(rules: Iterable[str]) -> list[str]:
    domains: list[str] = []
    for rule in rules:
        parts = rule.split(",")
        if len(parts) < 2 or parts[0] not in RULE_TYPES_CHECK:
            continue
        domains.append(parts[1])
    return sorted(set(domains))


def check_domain(domain: str) -> str:
    ok = False
    unknown = False
    for resolver_ip in RESOLVERS:
        resolver = dns.resolver.Resolver(configure=False)
        resolver.nameservers = [resolver_ip]
        resolver.timeout = 1.5
        resolver.lifetime = 1.5
        for qtype in ("A", "AAAA"):
            try:
                answer = resolver.resolve(domain, qtype, raise_on_no_answer=False)
                if answer.rrset is not None:
                    ok = True
                else:
                    ok = True
            except dns.resolver.NoAnswer:
                ok = True
            except dns.resolver.NXDOMAIN:
                pass
            except (dns.resolver.NoNameservers, dns.resolver.Timeout):
                unknown = True
            except dns.exception.DNSException:
                unknown = True

    if ok:
        return "OK"
    if unknown:
        return "UNKNOWN"
    return "NXDOMAIN"


def load_domains(root: Path, categories: list[str]) -> list[str]:
    domains: list[str] = []
    for name in categories:
        path = root / "rule" / "Clash" / name / f"{name}.list"
        if not path.exists():
            raise SystemExit(f"Missing rules file: {path}")
        domains.extend(iter_domains(parse_rules(path)))
    return sorted(set(domains))


def checked_date(value: str) -> str:
    if not value:
        return ""
    return value.split("T", 1)[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--category",
        action="append",
        help="Category to check. Can be passed more than once. Defaults to OverseasAI.",
    )
    args = parser.parse_args()

    root = repo_root()
    config = load_config(root)
    configured = [category["name"] for category in config["categories"]]
    categories = args.category or ["OverseasAI"]
    unknown_categories = sorted(set(categories) - set(configured))
    if unknown_categories:
        raise SystemExit(f"Unknown category: {', '.join(unknown_categories)}")

    reports_dir = root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    state_path = root / "data" / "nxdomain_state.json"
    state = json.loads(state_path.read_text() or "{}") if state_path.exists() else {}
    domains = load_domains(root, categories)

    results: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {executor.submit(check_domain, domain): domain for domain in domains}
        for future in as_completed(future_map):
            domain = future_map[future]
            try:
                results[domain] = future.result()
            except Exception:
                results[domain] = "UNKNOWN"

    updated_state = {}
    counters = Counter()
    candidates: list[str] = []
    unknowns: list[str] = []

    for domain in domains:
        status = results.get(domain, "UNKNOWN")
        prev = state.get(domain, {"count": 0})
        count = int(prev.get("count", 0))
        now_iso = datetime.utcnow().isoformat() + "Z"
        today = checked_date(now_iso)
        previous_check_date = checked_date(str(prev.get("last_checked", "")))
        same_day_repeat = previous_check_date == today

        if status == "NXDOMAIN":
            if not same_day_repeat or prev.get("last_status") != "NXDOMAIN":
                count += 1
        elif status == "OK":
            count = 0
        else:
            unknowns.append(domain)

        updated_state[domain] = {
            "count": count,
            "last_status": status,
            "last_checked": now_iso,
        }
        counters[status] += 1
        if count >= THRESHOLD:
            candidates.append(domain)

    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(updated_state, indent=2, sort_keys=True) + "\n")

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")
    report_lines = [
        f"# NXDOMAIN Report ({now})",
        "",
        f"Categories: {', '.join(categories)}",
        f"Checked domains: {len(domains)}",
        f"OK: {counters['OK']}",
        f"NXDOMAIN: {counters['NXDOMAIN']}",
        f"UNKNOWN: {counters['UNKNOWN']}",
        "",
        f"Threshold: {THRESHOLD} consecutive NXDOMAIN",
        "",
        "## Candidates",
    ]
    report_lines.extend([f"- {domain}" for domain in sorted(set(candidates))] or ["- (none)"])
    report_lines.append("")
    report_lines.append("## Unknowns")
    report_lines.extend([f"- {domain}" for domain in sorted(set(unknowns))] or ["- (none)"])

    (reports_dir / "nxdomain_report.md").write_text("\n".join(report_lines) + "\n")
    (reports_dir / "nxdomain_candidates.txt").write_text(
        "\n".join(sorted(set(candidates))) + "\n"
    )


if __name__ == "__main__":
    main()
