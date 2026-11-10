# Day 10 矿工代码缺陷修复参考解析（卡壳时查阅）

> 💡 **学习建议**：请先独立运行 `python arena/day09_10_miner/diagnose_node.py --test-403`，并结合验证者评分输出与 `.localnet/miner.log` 报错日志排查 `arena/day09_10_miner/camp_miner.py` 中的两处预留缺陷。遇到卡点时再对照以下参考解析。

`camp_miner.py` 初始代码中预留了两处典型缺陷，分别对应验证者三关评分中的**关卡 1（原文依据核验）**与**异常边界处理（缺失字段简讯）**。

## 缺陷 1：依据是编造的总结句

现象：验证者输出 `依据不在原文中：[项目名称]『项目名称：Atlas』`，每轮 0 分。

原因：`make_evidence` 返回的是 `"{字段}：{值}"`，不是原文里的句子。

修复：

```python
def make_evidence(field: str, value: str, text: str) -> str:
    for s in re.split(r"[。！？]", text):
        if value and value in s:
            return s.strip()
    return ""
```

## 缺陷 2：遇到原文缺字段的题目就崩溃

现象：大约三分之一的题目（“未披露投资方”那类）验证者显示 `没有拿到结果（HTTP 500）`；矿工日志出现
`AttributeError: 'NoneType' object has no attribute 'group'`。

原因：`extract_field` 在所有正则都匹配不到时，`m` 为 `None`，直接调用 `m.group(1)`。

修复（同时遵守“缺失字段填空值”的约定）：

```python
def extract_field(field: str, text: str) -> str:
    for p in PATTERNS.get(field, []):
        m = re.search(p, text)
        if m:
            return m.group(1).strip()
    return ""
```

## 验收

修复后重启矿工，运行 `camp_validator.py --score-only --rounds 5`：学员矿工每轮通过关卡，字段正确 4/4，
耗时为毫秒级，EMA 逐轮上升并高于两个陪练矿工。
