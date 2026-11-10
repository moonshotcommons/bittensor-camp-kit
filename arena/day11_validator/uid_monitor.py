#!/usr/bin/env python3
"""
第 11 天：链上节点监控 uid_monitor.py—— 每次都读真实的链，不使用演示数据。

默认监控本地链练习矿工（miner/default）。在测试网或主网上，用 --network 和 --hotkey（或 --uid）指定你自己的节点。

告警规则（教学用）：
  - 排名按 incentive 从高到低计算，落入后 10% 且已经过了新手保护期 → 打印淘汰风险告警；
  - 链上没有登记 ip:port → 提示验证者找不到你。
注意：链上真正的淘汰依据是 pruning_score（基于排放），这里同时打印出来，方便对照。
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from arena.common.chain import default_netuid, default_network, fetch_metagraph, hotkey_ss58, load_wallet  # noqa: E402


def immunity_period(network: str, netuid: int) -> int:
    import bittensor as bt

    hp = bt.Subtensor(network).subnets.subnet_hyperparameters(netuid)
    return int(hp.get("immunity_period", 0))


def check_deregistration_risk(rank: int, total: int, immune: bool) -> bool:
    """第 11 天练习：读懂这条规则。排名落入后 10% 且不在保护期时返回 True。"""
    return (not immune) and rank > int(total * 0.9)


def snapshot(network: str, netuid: int, hotkey: str, uid: int | None, imm: int) -> str:
    mg = fetch_metagraph(network, netuid)
    if uid is not None:
        me = next((n for n in mg.neurons if n.uid == uid), None)
    else:
        me = next((n for n in mg.neurons if n.hotkey == hotkey), None)
    if me is None:
        target = f"UID {uid}" if uid is not None else f"hotkey {hotkey[:10]}…"
        return f"区块 #{mg.block}  ❌ {target} 不在 netuid {netuid}（未注册或已被淘汰）"
    ranked = sorted(mg.neurons, key=lambda n: n.incentive, reverse=True)
    rank = [n.uid for n in ranked].index(me.uid) + 1
    age = mg.block - me.block_at_registration
    immune = age < imm
    epochs_per_day = 7200 / mg.tempo if mg.tempo else 0
    warn = []
    if check_deregistration_risk(rank, mg.num_uids, immune):
        warn.append("⚠️ 排名在后 10% 且已过保护期，有淘汰风险")
    if not me.axon:
        warn.append("⚠️ 链上没有登记 ip:port，验证者找不到你")
    return (
        f"区块 #{mg.block}  UID {me.uid}  排名 {rank}/{mg.num_uids}  "
        f"incentive {me.incentive:.4f}  trust {me.trust:.4f}  pruning_score {me.pruning_score:.4f}  "
        f"上个 epoch 排放 {me.emission}  tempo {mg.tempo}（约每天 {epochs_per_day:.0f} 个 epoch）  "
        f"保护期 {'剩 ' + str(imm - age) + ' 块' if immune else '已过'}  axon {me.axon or '未发布'}  "
        + ("  ".join(warn) if warn else "✅ 正常")
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--network", default=default_network())
    ap.add_argument("--netuid", type=int, default=default_netuid())
    ap.add_argument("--hotkey", default="", help="要监控的 hotkey ss58；默认读取本地 miner/default")
    ap.add_argument("--uid", type=int, default=None, help="按 UID 监控（可选，优先于 --hotkey）")
    ap.add_argument("--rounds", type=int, default=3, help="轮询次数；0 表示一直运行（配合 PM2 / Docker）")
    ap.add_argument("--interval", type=float, default=12.0, help="轮询间隔秒数")
    args = ap.parse_args()

    hk = ""
    if args.uid is None:
        hk = args.hotkey or hotkey_ss58(load_wallet(os.getenv("CAMP_MINER_WALLET", "miner"), os.getenv("CAMP_MINER_HOTKEY", "default")))
    imm = immunity_period(args.network, args.netuid)
    target_desc = f"UID {args.uid}" if args.uid is not None else hk
    print(f"📡 监控 {target_desc}  网络 {args.network}  netuid {args.netuid}  保护期 {imm} 块", flush=True)
    i = 0
    while args.rounds == 0 or i < args.rounds:
        i += 1
        try:
            print(f"[{i}] " + snapshot(args.network, args.netuid, hk, args.uid, imm), flush=True)
        except Exception as e:  # 网络抖动时不退出，方便守护进程长期运行
            print(f"[{i}] 读取失败：{e}", flush=True)
        if args.rounds == 0 or i < args.rounds:
            time.sleep(args.interval)


if __name__ == "__main__":
    main()
