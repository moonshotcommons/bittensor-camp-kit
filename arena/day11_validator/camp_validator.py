#!/usr/bin/env python3
"""
第 9 天（只评分）/ 第 11 天（评分 + 提交权重）：共学营验证者 camp_validator.py

完整流程，每一步都读写真实的链：
  1. 读链上元图，确认自己的 UID、质押和验证许可（validator_permit）；
  2. 找出所有在链上发布了 ip:port 的矿工，用 bt.http_auth 签名后发出同一道题；
  3. 按教学评分规则打分，并更新本地保存的移动平均分（EMA）；
  4. （去掉 --score-only 时）把归一化后的分数作为权重，用 bt.SetWeights 提交到链上；
  5. 用 --show-weights 读回链上已经生效的权重。

关于 commit-reveal：本子网开启时，SDK 会自动走加密提交路径，链会在 reveal 周期后
自动解密并生效，不需要手动 reveal。所以提交后立即读回，可能还看不到新权重。
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from arena.common.chain import LOCALNET_DIR, default_netuid, default_network, fetch_metagraph, hotkey_ss58, load_wallet  # noqa: E402
from arena.common.protocol import evaluate_miner_response  # noqa: E402
from arena.common.tasks_bank import generate_dynamic_task  # noqa: E402

EMA_ALPHA = 0.3
TIMEOUT = 3.0
STATE_FILE = LOCALNET_DIR / "validator_scores.json"


def query_miner(wallet, neuron, task) -> tuple[dict | None, float, str]:
    import bittensor as bt

    body = json.dumps(
        {k: task[k] for k in ("task_id", "raw_text", "required_fields")} | {"timeout": TIMEOUT}, ensure_ascii=False
    ).encode()
    headers = bt.http_auth.sign(wallet, method="POST", path="/extract", body=body, receiver_ss58=neuron.hotkey)
    headers["Content-Type"] = "application/json"
    req = urllib.request.Request(f"http://{neuron.axon}/extract", data=body, headers=headers, method="POST")
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT + 1) as r:
            return json.loads(r.read()), time.time() - t0, ""
    except urllib.error.HTTPError as e:
        return None, time.time() - t0, f"HTTP {e.code}"
    except Exception as e:  # 连接失败、超时
        return None, time.time() - t0, type(e).__name__


def load_state() -> dict:
    return json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}


def show_weights(network, netuid, my_uid):
    import bittensor as bt

    client = bt.Subtensor(network)
    rows = client.weights.weights(netuid)
    mine = rows.get(my_uid) or {}
    print(f"\n⛓️  链上当前生效的权重（验证者 UID {my_uid}）：", mine if mine else "（暂无，可能还在 reveal 周期内）")
    print(f"   全部验证者的权重行：{rows}")


def main():
    ap = argparse.ArgumentParser(description="共学营验证者（bittensor v11）")
    ap.add_argument("--wallet", default=os.getenv("CAMP_VALIDATOR_WALLET", "validator"))
    ap.add_argument("--hotkey", default="default")
    ap.add_argument("--network", default=default_network())
    ap.add_argument("--netuid", type=int, default=default_netuid())
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--seed", type=int, default=12, help="出题随机种子（默认 12，保证修复前后在同一批题目上对比；传 0 则纯随机）")
    ap.add_argument("--keep-ema", action="store_true", help="沿用上次运行保存在 validator_scores.json 的历史 EMA")
    ap.add_argument("--score-only", action="store_true", help="只评分，不提交权重（第 9–10 天用）")
    ap.add_argument("--show-weights", action="store_true", help="只读取链上已生效的权重")
    args = ap.parse_args()

    import bittensor as bt

    wallet = load_wallet(args.wallet, args.hotkey)
    my_hk = hotkey_ss58(wallet)
    mg = fetch_metagraph(args.network, args.netuid)
    me = next((n for n in mg.neurons if n.hotkey == my_hk), None)

    print("=" * 96)
    if me is None:
        sys.exit(f"❌ 验证者 hotkey {my_hk} 没有在 netuid {args.netuid} 注册。")
    print(f"🔑 第 1 步  验证者 UID {me.uid}  质押 {me.alpha_stake}  验证许可={me.validator_permit}  区块 #{mg.block}")
    if args.show_weights:
        return show_weights(args.network, args.netuid, me.uid)
    if not me.validator_permit:
        print("⚠️ 当前没有验证许可：可以评分，但链会拒绝提交权重。许可在每个 epoch 按质押重新计算。")

    miners = [n for n in mg.neurons if n.axon and n.uid != me.uid]
    if not miners:
        sys.exit("❌ 元图里没有任何矿工发布了 ip:port。请先用 camp_miner.py --serve 启动矿工。")
    print(f"📡 第 2 步  找到 {len(miners)} 个已发布端点的矿工：" + "，".join(f"UID {n.uid}@{n.axon}" for n in miners))

    state = load_state() if args.keep_ema else {}
    rng = random.Random(args.seed) if args.seed else None
    for rnd in range(1, args.rounds + 1):
        task = generate_dynamic_task(rng)
        print(f"\n📝 第 {rnd} 轮  {task['task_id']}：{task['raw_text']}")
        for n in miners:
            resp, lat, err = query_miner(wallet, n, task)
            if resp is None:
                score, reason = 0.0, f"没有拿到结果（{err}）"
            else:
                score, d = evaluate_miner_response(
                    task["raw_text"], task["required_fields"], task["ground_truth"],
                    resp.get("extracted_data"), resp.get("evidence_quotes"), lat, TIMEOUT,
                )
                reason = d["reason"]
            key = str(n.uid)
            prev = state.get(key, 0.0)
            state[key] = round(EMA_ALPHA * score + (1 - EMA_ALPHA) * prev, 4)
            print(f"   UID {n.uid:<3} 耗时 {lat:5.2f}s  本轮 {score:.4f}  EMA {prev:.4f}→{state[key]:.4f}  {reason}")

    LOCALNET_DIR.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))

    uids = [n.uid for n in miners]
    raw = [state.get(str(u), 0.0) for u in uids]
    total = sum(raw)
    weights = [x / total for x in raw] if total > 0 else [0.0] * len(raw)
    print("\n📊 第 3 步  归一化权重（只看比例）：" + "，".join(f"UID {u}={w:.3f}" for u, w in zip(uids, weights)))

    if args.score_only:
        print("\n（--score-only：本次不提交权重）")
        return
    if total == 0:
        sys.exit("⚠️ 所有矿工都是 0 分，不提交全零权重。")

    client = bt.Subtensor(args.network)
    cr = client.subnets.commit_reveal_enabled(args.netuid)
    print(f"⛓️  第 4 步  提交权重（commit-reveal 开启={cr}）……")
    res = client.execute(bt.SetWeights(netuid=args.netuid, uids=uids, weights=weights), wallet)
    if res.success:
        print(f"✅ 链上已接受  区块 {res.block_hash}")
        print("   提示：开启 commit-reveal 时，权重会在 reveal 周期后自动生效；稍后运行 --show-weights 读回。")
    else:
        print(f"❌ 链上拒绝：{res.error.code} — {res.error.remediation}")
        sys.exit(1)


if __name__ == "__main__":
    main()
