# rule

个人 Clash/Mihomo 分流规则集。

规则目前分为：

| 优先级 | 分类 | 说明 |
| ---: | --- | --- |
| 1 | OverseasAI | 海外 AI，直接同步 `viewer12/OverseasAI.list`，优先级最高 |
| 2 | YouTube | YouTube / YouTube Music 及相关视频域名 |
| 3 | Google | Google 通用服务，补充 Drive / FCM / Voice / Search / Earth，放在 OverseasAI 和 YouTube 之后 |
| 5 | OneDrive | OneDrive 及相关存储服务 |
| 7 | Telegram | Telegram 域名、IP、进程规则，补充 SG / NL / US 细分 IP 段 |
| 8 | Direct | 直连规则，合并 `Lan + Direct + China + ChinaDNS + ChinaMaxNoIP` |

> 规则匹配是从上到下的。比如 `gemini.google.com` 同时可能落入 AI/Google 相关域名，但只要把 `OverseasAI` 放在 `Google` 前面，就会优先命中海外 AI。

## 订阅地址

Raw 前缀：

```text
https://raw.githubusercontent.com/phyrevue/rule/main/
```

| 分类 | Clash/Mihomo rule-provider |
| --- | --- |
| OverseasAI | `rule/Clash/OverseasAI/OverseasAI.list` |
| YouTube | `rule/Clash/YouTube/YouTube.list` |
| Google | `rule/Clash/Google/Google.list` |
| OneDrive | `rule/Clash/OneDrive/OneDrive.list` |
| Telegram | `rule/Clash/Telegram/Telegram.list` |
| Direct | `rule/Clash/Direct/Direct.list` |

`OverseasAI` 会过滤上游里的宽泛规则 `DOMAIN-SUFFIX,google.com`，避免普通 Google 流量被 AI 分类抢先匹配；`gemini.google.com` 等具体 AI 域名仍保留在 `OverseasAI`。

## Mihomo 示例

```yaml
rule-providers:
  OverseasAI:
    type: http
    behavior: classical
    format: text
    interval: 86400
    url: https://raw.githubusercontent.com/phyrevue/rule/main/rule/Clash/OverseasAI/OverseasAI.list
    path: ./rule-providers/OverseasAI.list
  YouTube:
    type: http
    behavior: classical
    format: text
    interval: 86400
    url: https://raw.githubusercontent.com/phyrevue/rule/main/rule/Clash/YouTube/YouTube.list
    path: ./rule-providers/YouTube.list
  Google:
    type: http
    behavior: classical
    format: text
    interval: 86400
    url: https://raw.githubusercontent.com/phyrevue/rule/main/rule/Clash/Google/Google.list
    path: ./rule-providers/Google.list
  OneDrive:
    type: http
    behavior: classical
    format: text
    interval: 86400
    url: https://raw.githubusercontent.com/phyrevue/rule/main/rule/Clash/OneDrive/OneDrive.list
    path: ./rule-providers/OneDrive.list
  Telegram:
    type: http
    behavior: classical
    format: text
    interval: 86400
    url: https://raw.githubusercontent.com/phyrevue/rule/main/rule/Clash/Telegram/Telegram.list
    path: ./rule-providers/Telegram.list
  Direct:
    type: http
    behavior: classical
    format: text
    interval: 86400
    url: https://raw.githubusercontent.com/phyrevue/rule/main/rule/Clash/Direct/Direct.list
    path: ./rule-providers/Direct.list

rules:
  - RULE-SET,OverseasAI,AI
  - RULE-SET,YouTube,YouTube
  - RULE-SET,Google,Google
  - RULE-SET,OneDrive,OneDrive
  - RULE-SET,Telegram,Telegram
  - RULE-SET,Direct,DIRECT
  - GEOIP,CN,DIRECT
  - MATCH,Proxy
```

策略组名称可以按你的配置改，比如把 `AI`、`YouTube`、`Google` 全部改成同一个代理组。

## 文件结构

```text
rule
├── config/rulesets.json        # 分类、优先级、上游来源
├── rule/Clash/<Name>/          # Clash/Mihomo 订阅文件
│   ├── <Name>.list             # 合并后的主规则
│   └── <Name>_Custom.list      # 自定义补充规则
├── scripts/sync_rules.py       # 从上游同步并合并规则
├── scripts/check_domains.py    # NXDOMAIN 检查，默认只检查 OverseasAI
└── .github/workflows/          # 每日自动同步
```

## 本地更新

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/sync_rules.py
.venv/bin/python scripts/validate_rules.py
.venv/bin/python scripts/audit_upstream.py
.venv/bin/python scripts/check_domains.py --category OverseasAI
```

自动化每天会同步：

- `viewer12/OverseasAI.list`
- `blackmatrix7/ios_rule_script`
- `reports/upstream_audit.md` 会记录对 blackmatrix7 Clash 细分列表的覆盖审计

`Direct` 使用 `ChinaMaxNoIP` 补齐大量国内域名，但没有合入完整 `ChinaIPs`。推荐保留示例里的 `GEOIP,CN,DIRECT` 来覆盖中国大陆 IP，这样规则文件不会膨胀得太夸张。

## 自定义规则

编辑对应分类的 `_Custom.list`，每行一条 classical 规则：

```text
DOMAIN-SUFFIX,example.com
DOMAIN,api.example.com
IP-CIDR,203.0.113.0/24,no-resolve
```

然后运行：

```bash
.venv/bin/python scripts/sync_rules.py
```

## License

本仓库规则衍生自 `viewer12/OverseasAI.list` 和 `blackmatrix7/ios_rule_script`，按 GPL-2.0 发布。
