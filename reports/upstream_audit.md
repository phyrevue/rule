# Upstream Audit

对 blackmatrix7/ios_rule_script 的 Clash 细分规则做精确集合比对。

| 分类 | 上游细分 | 状态 | 上游规则 | 已覆盖 | 未覆盖 | 备注 |
| --- | --- | --- | ---: | ---: | ---: | --- |
| YouTube | YouTubeMusic | included | 1 | 1 | 0 | 已合入配置 |
| Google | GoogleDrive | included | 6 | 6 | 0 | 已合入配置 |
| Google | GoogleFCM | included | 41 | 41 | 0 | 已合入配置 |
| Google | GoogleVoice | included | 1 | 1 | 0 | 已合入配置 |
| Google | GoogleSearch | included | 1 | 1 | 0 | 已合入配置 |
| Google | GoogleEarth | included | 16 | 16 | 0 | 已合入配置 |
| Telegram | TelegramSG | included | 3 | 3 | 0 | 已合入配置 |
| Telegram | TelegramNL | included | 5 | 5 | 0 | 已合入配置 |
| Telegram | TelegramUS | included | 2 | 2 | 0 | 已合入配置 |
| Direct | ChinaDNS | included | 4 | 4 | 0 | 已合入配置 |
| Direct | ChinaMaxNoIP | included | 112019 | 112019 | 0 | 已合入配置 |
| Direct | ChinaIPs | intentional | 22754 | 1 | 22753 | 未合入完整 ChinaIPs。建议在 Clash/Mihomo 配置末尾使用 `GEOIP,CN,DIRECT` 覆盖中国大陆 IP，避免 rule-provider 过大。 |

说明：这里是规则文本的精确比对，不做 CIDR 包含关系推断。
例如较大的网段已经覆盖较小网段时，仍可能在表格里显示为未覆盖。
