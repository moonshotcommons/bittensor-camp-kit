"""
AI 结构化情报提取竞技场 —— 任务协议与验证者评分规则（v4）

传输方式：普通 HTTP POST /extract，请求体为 JSON，用 bt.http_auth（btauth/1）对请求签名。
这与 bittensor SDK v11 的官方做法一致：v11 已移除 Axon/Dendrite/Synapse，链上只记录矿工的 ip:port。

请求体（验证者 → 矿工）：
    {"task_id": str, "raw_text": str, "required_fields": [str, ...], "timeout": float}
响应体（矿工 → 验证者）：
    {"task_id": str, "extracted_data": {字段: 值}, "evidence_quotes": {字段: 原文原句}, "engine": str}

空值约定：原文里没有的字段，值填 ""，依据也填 ""。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

ACCURACY_WEIGHT = 0.70
SPEED_WEIGHT = 0.30


def evaluate_miner_response(
    raw_text: str,
    required_fields: List[str],
    ground_truth: Dict[str, str],
    extracted_data: Optional[Dict[str, Any]],
    evidence_quotes: Optional[Dict[str, Any]],
    latency_sec: float,
    timeout_sec: float = 3.0,
) -> Tuple[float, Dict[str, Any]]:
    """
    评分 = 关卡通过 × (0.70 × 字段准确率 + 0.30 × 速度分)

    第一关（不通过直接 0 分）：
      1. 未超时；2. 两个字典都在且覆盖全部字段；
      3. 每个非空字段的依据必须是原文中一字不差的片段，并且包含提取出的值（防编造）。
    第二关：字段准确率。原文没有的字段，正确答案是空字符串。
    第三关：速度分 = max(0, 1 - 耗时 / 超时)。

    说明：这是教学用的简化评分规则，用于演示“格式合格、内容正确、有原文依据”的区别，
    不代表任何真实子网的评分实现。
    """
    detail: Dict[str, Any] = {
        "gate_passed": False,
        "reason": "",
        "accuracy": 0.0,
        "speed": 0.0,
        "score": 0.0,
    }

    if latency_sec > timeout_sec:
        detail["reason"] = f"超时：{latency_sec:.2f}s > {timeout_sec:.1f}s"
        return 0.0, detail

    if not isinstance(extracted_data, dict) or not isinstance(evidence_quotes, dict):
        detail["reason"] = "响应缺少 extracted_data 或 evidence_quotes"
        return 0.0, detail

    for f in required_fields:
        if f not in extracted_data or f not in evidence_quotes:
            detail["reason"] = f"缺少字段：{f}"
            return 0.0, detail

    for f in required_fields:
        val = str(extracted_data.get(f) or "").strip()
        quote = str(evidence_quotes.get(f) or "").strip()
        if not val:
            continue  # 空值不需要依据
        if quote not in raw_text or len(quote) < 4:
            detail["reason"] = f"依据不在原文中：[{f}]『{quote}』"
            return 0.0, detail
        if val not in quote:
            detail["reason"] = f"依据里找不到提取值：[{f}]『{val}』"
            return 0.0, detail

    detail["gate_passed"] = True

    correct = 0
    for f in required_fields:
        expected = str(ground_truth.get(f, "")).replace(" ", "").lower()
        actual = str(extracted_data.get(f) or "").replace(" ", "").lower()
        if expected == actual:
            correct += 1
    acc = correct / len(required_fields) if required_fields else 0.0
    speed = max(0.0, 1.0 - latency_sec / timeout_sec)
    score = round(ACCURACY_WEIGHT * acc + SPEED_WEIGHT * speed, 4)

    detail.update(accuracy=round(acc, 4), speed=round(speed, 4), score=score)
    detail["reason"] = f"通过（字段正确 {correct}/{len(required_fields)}）"
    return score, detail
