# EVAL-V3B-R1 静态报告补表

本文件是从已保存的冻结结果派生的静态报告附表，不是第三轮 scored run，不改变任何 receipt、实验分配、缓存或冻结实现。它补齐逐 text × B4 variant 的响应类别，并更正前期报告中的 case9 分组。机器可复核映射与完整计数见同目录 `reporting_audit.json`。

## 输入与算法

输入为现有 `b4.json`、`b1b3.json`、`live_ledger.jsonl` 以及 ledger 所指的 cache；前置 SHA 清单覆盖全部 13 个 `artifacts/eval_v3/` 文件和 2,442 个 cache 文件。审计使用冻结 `HypothesisProposer` 在内存中重放保存的 response，错误记录按冻结 replay error 类抛出 `CachedProviderError`，再使用冻结 `classify_cache_record` 分类。没有 HTTP、episode runner 或新评估调用。

缓存 finalized request 的 SHA 与 ledger 项及 cache 文件名逐项核验。匹配键为 `(context_sha256, target_id, round(time, 6), ranked_ids, normalized_error, unknown_ids)`，其中归一化错误沿用冻结 `episode.py` 规则。每个 proposal_rank 事件都保存所有候选 request SHA 和类别；要求候选非空且候选类别集合唯一，不要求候选 SHA 唯一。时间精度为六位小数，不使用时间容差。

| 输入 | SHA-256 / 数量 |
|---|---|
| `b4.json` | `e139fee33fa9947b2f653c1506ad456d6d2f6cee4a046cb37c2041e12cbd5562` |
| `b1b3.json` | `39565905eabd4612e90feb8f79d059f1c4935eb2ad11ae8e953dda5cbb340950` |
| `live_ledger.jsonl` | `ba1dd781cbe296bb23709b972fd99d248b61168514d7a5ff7f86d14cf58ec52e` |
| 完整只读 preflight 清单 | `b2beeefcbd80117210e4582e54c1d136fe1e6f97c2488d5f2bca543d7aac22cf`（2,455 个文件项） |
| ledger | 1,523 个不同 request SHA；对应 cache 文件均存在且 finalized request SHA 相符 |

## Proposal response 分类

计数单位是每个 proposal_rank / proposer 调用事件，因此保留跨变体、决策的缓存复用。四类互斥，逐 cell 的总数等于保存的 proposal_rank 事件数和 proposer invocations。

| text | B4 variant | valid | INVALID_PROPOSAL | PROVIDER_ERROR | truncated | 合计 / invocations |
|---|---|---:|---:|---:|---:|---:|
| NO_TEXT_CONTEXT | STRICT | 338 | 0 | 0 | 0 | 338 |
| NO_TEXT_CONTEXT | TIEBREAK | 337 | 0 | 0 | 0 | 337 |
| HELPFUL_TEXT_CONTEXT | STRICT | 333 | 0 | 1 | 4 | 338 |
| HELPFUL_TEXT_CONTEXT | TIEBREAK | 332 | 0 | 1 | 4 | 337 |
| IRRELEVANT_TEXT_CONTEXT | STRICT | 336 | 0 | 0 | 2 | 338 |
| IRRELEVANT_TEXT_CONTEXT | TIEBREAK | 334 | 0 | 1 | 2 | 337 |
| MISLEADING_TEXT_CONTEXT | STRICT | 335 | 0 | 1 | 2 | 338 |
| MISLEADING_TEXT_CONTEXT | TIEBREAK | 334 | 0 | 2 | 1 | 337 |
| **总计** |  | **2,679** | **0** | **6** | **15** | **2,700** |

更正：八格实际 proposal_rank / invocation 合计为 2,700；表中计数按四类相加亦为 2,700。单元值见上表，逐事件检查结果为 0 未匹配、0 类别歧义。候选集合大小：2,624 个事件各有 1 个候选 SHA，76 个事件各有 2 个候选 SHA。每个候选集合内部类别一致；不宣称所有事件 request SHA 一一唯一。

不同口径分别报告：ledger 中有 1,523 个不同 request SHA；B4 receipt 共享的 provider `llm_calls` 为 1,519；四个 text 条件各有 STRICT 338 次和 TIEBREAK 337 次 proposer invocations，跨 text 条件分别合计 1,352 次和 1,348 次、全体 2,700 次。调用事件、共享 provider 调用与 distinct ledger 请求不是同一计数单位。

ledger distinct-cache 分类另计为 valid 1,511、INVALID_PROPOSAL 0、PROVIDER_ERROR 4、truncated 8（合计 1,523）。它是 ledger 请求记录口径，不替代上表逐 cell 的 invocation 口径。

## Gate reason

Gate 统计只来自已保存 `b4.json` metrics，和 response 分类分开。下表列出每个 variant 的 `TEXT_TIEBREAK` 次数及保存的 `TIEBREAK_FALLBACK` 原因分布。冻结结果没有保存的其他 gate 原因不能从此表推定。

| text | B4 variant | `TEXT_TIEBREAK` | `TIEBREAK_FALLBACK` |
|---|---|---:|---|
| NO_TEXT_CONTEXT | STRICT | 0 | none recorded |
| NO_TEXT_CONTEXT | TIEBREAK | 106 | `NO_SAFE_ACTION` 229；`UNKNOWN_ID` 2 |
| HELPFUL_TEXT_CONTEXT | STRICT | 0 | none recorded |
| HELPFUL_TEXT_CONTEXT | TIEBREAK | 106 | `INVALID_PROPOSAL` 4；`NO_SAFE_ACTION` 226；`PROVIDER_ERROR` 1 |
| IRRELEVANT_TEXT_CONTEXT | STRICT | 0 | none recorded |
| IRRELEVANT_TEXT_CONTEXT | TIEBREAK | 105 | `INVALID_PROPOSAL` 2；`NO_SAFE_ACTION` 226；`PROVIDER_ERROR` 1；`UNKNOWN_ID` 3 |
| MISLEADING_TEXT_CONTEXT | STRICT | 0 | none recorded |
| MISLEADING_TEXT_CONTEXT | TIEBREAK | 105 | `INVALID_PROPOSAL` 1；`NO_SAFE_ACTION` 228；`PROVIDER_ERROR` 2；`UNKNOWN_ID` 1 |

## Case 9 分组更正

以 B4 的 `B3_receipt_sha256` 连接 B1/B3 的 `b3_receipt_sha256`，再按明确 case 结构识别 `SPEED_STEP` 与 `ACTUATOR_DELAY`。100 个 B3 receipt 可映射到 case，B4 的 400 行全部匹配；真实 case9 有 5 个物理组。旧报告按排序后的物理组位置 mod 19 选出的 5 组与真实组交集为 0。这里的旧分组只用于量化更正差异，不能作为 case 识别方法。

以下是在真实 case9 五组中，从已保存 B4 score 和 proposer invocation 字段求和的结果；每个 text × mode 均为 5 行：

| text | mode | challenge success | recoverable challenges | wrong disposition | ordinary miss | unsafe action | proposer invocations |
|---|---|---:|---:|---:|---:|---:|---:|
| NO_TEXT_CONTEXT | STRICT | 8 | 48 | 34 | 6 | 0 | 36 |
| NO_TEXT_CONTEXT | TIEBREAK | 8 | 48 | 33 | 7 | 4 | 34 |
| HELPFUL_TEXT_CONTEXT | STRICT | 8 | 48 | 34 | 6 | 0 | 36 |
| HELPFUL_TEXT_CONTEXT | TIEBREAK | 8 | 48 | 33 | 7 | 4 | 34 |
| IRRELEVANT_TEXT_CONTEXT | STRICT | 8 | 48 | 34 | 6 | 0 | 36 |
| IRRELEVANT_TEXT_CONTEXT | TIEBREAK | 8 | 48 | 33 | 7 | 4 | 34 |
| MISLEADING_TEXT_CONTEXT | STRICT | 8 | 48 | 34 | 6 | 0 | 36 |
| MISLEADING_TEXT_CONTEXT | TIEBREAK | 8 | 48 | 33 | 7 | 4 | 34 |

这项更正只涉及前期报告的 case9 派生分组；冻结实现及真实结构分配未变。case 9 在开发期已见，因此不据此主张未见组合泛化。旧 `e4_summary` 和原报告保留；本附表替代其中旧 case9 派生统计。

## 复核边界与产物

逐事件映射只包含 episode 行 ordinal、mode、proposal ordinal、候选 request SHA 和类别，不含 seed、原始 episode、request 或 response 正文。辅助审计脚本与完整 preflight SHA 清单存放在 `_reports/`，不纳入仓库提交。本报告与 JSON 附表不会解除先前审查的 BLOCK；仍须由新会话独立复审，远端操作由所有者处理。


A04 §6.2 的保存 metrics 口径：`TIEBREAK_FALLBACK:INVALID_PROPOSAL` 与 `TIEBREAK_FALLBACK:PROVIDER_ERROR` 合计 11 次 / 1348 次 TIEBREAK proposer invocations = 0.8160%，低于 50% 阈值；该门槛结论独立于上面的 response 分类。

原两轮 scored receipt 与 replay-check receipt 保持为 `538e6b832bf60833e4ac545f096d576f6800eed4b790c1d6bf882af9119e536d`、`aa0297a882ab41cc73586236758d678b5f8b7c31985be4c2585872b07aa8c147`（replay `equal=true`）。

JSON 附表 SHA-256：`4282137d5d1a7ed40444c0d776d83a793270479c6c1c22d94794e414bc548e2c`