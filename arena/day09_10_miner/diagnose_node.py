#!/usr/bin/env python3
"""
第 10 天：矿工节点健康、链上端点与权限拦截诊断工具 diagnose_node.py

检查四件事：
  1. 本机矿工端口（默认 8091）是否在监听；
  2. 链上元图里该矿工 hotkey 登记的 ip:port 是否与本机局域网 IP 一致；
  3. 系统文件描述符上限（ulimit -n）是否满足高并发连接要求；
  4. （加 --test-403 时）用一个没有验证许可的 hotkey 向矿工发签名请求，验证矿工是否返回 HTTP 403。
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import urllib.error
import urllib.request
from pathlib import Path

try:
    import resource
except ImportError:
    resource = None

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from arena.common.chain import default_netuid, default_network, fetch_metagraph, hotkey_ss58, lan_ip, load_wallet  # noqa: E402


def check_local_port(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        return s.connect_ex((host, port)) == 0


def test_unpermitted_call(target_url: str, target_hotkey: str, caller_wallet_name: str, caller_hotkey_name: str) -> str:
    import bittensor as bt

    caller_wallet = load_wallet(caller_wallet_name, caller_hotkey_name)
    body = json.dumps(
        {"task_id": "auth_probe", "raw_text": "测试无验证许可拦截", "required_fields": ["项目名称"]},
        ensure_ascii=False,
    ).encode()
    headers = bt.http_auth.sign(
        caller_wallet, method="POST", path="/extract", body=body, receiver_ss58=target_hotkey
    )
    headers["Content-Type"] = "application/json"
    req = urllib.request.Request(f"{target_url}/extract", data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=3.0) as r:
            return f"HTTP {r.status}（⚠️ 未拦截无许可请求）"
    except urllib.error.HTTPError as e:
        body_err = e.read().decode("utf-8", errors="ignore")
        if e.code == 403:
            return f"HTTP 403 Forbidden（✅ 成功拦截无验证许可的 hotkey：{body_err}）"
        return f"HTTP {e.code}（{body_err}）"
    except Exception as e:
        return f"请求失败：{e}"


def main():
    ap = argparse.ArgumentParser(description="共学营第 10 天：矿工节点诊断工具")
    ap.add_argument("--wallet", default=os.getenv("CAMP_MINER_WALLET", "miner"))
    ap.add_argument("--hotkey", default=os.getenv("CAMP_MINER_HOTKEY", "default"))
    ap.add_argument("--network", default=default_network())
    ap.add_argument("--netuid", type=int, default=default_netuid())
    ap.add_argument("--port", type=int, default=8091, help="本机矿工监听端口")
    ap.add_argument("--test-403", action="store_true", help="用无验证许可的 hotkey 请求矿工，验证返回 403")
    args = ap.parse_args()

    local_ip = lan_ip()
    expected_axon = f"{local_ip}:{args.port}"
    port_open = check_local_port("127.0.0.1", args.port)

    wallet = load_wallet(args.wallet, args.hotkey)
    my_hk = hotkey_ss58(wallet)
    mg = fetch_metagraph(args.network, args.netuid)
    me = next((n for n in mg.neurons if n.hotkey == my_hk), None)
    chain_axon = me.axon if (me and me.axon) else "未登记"
    axon_match = (chain_axon == expected_axon)

    print("=" * 96)
    print(f"🩺 第 10 天矿工节点诊断报告（网络={args.network}，netuid={args.netuid}，区块=#{mg.block}）")
    print("=" * 96)
    print(
        f"1. 本机端口监听       | 127.0.0.1:{args.port:<20} | "
        f"{'OPEN（监听中）' if port_open else 'CLOSED（未启动）':<22} | "
        f"{'✅ 正常' if port_open else '❌ 请先启动 camp_miner.py'}"
    )
    print(
        f"2. 链上登记端点       | 链上={chain_axon:<24} | 本机={expected_axon:<17} | "
        f"{'✅ 一致（UID ' + str(me.uid) + '）' if axon_match else '⚠️ 不一致，请加 --serve 重新发布'}"
    )

    if resource is not None:
        soft_limit, _ = resource.getrlimit(resource.RLIMIT_NOFILE)
        ulimit_ok = soft_limit >= 4096
        print(
            f"3. 文件描述符上限     | ulimit -n                     | Soft={soft_limit:<17} | "
            f"{'✅ 够用' if ulimit_ok else '⚠️ 偏低（建议 ulimit -n 65535）'}"
        )
    else:
        print("3. 文件描述符上限     | ulimit -n                     | N/A                   | ℹ️ 非 Unix 环境")

    if args.test_403:
        if not port_open:
            print("4. 无验证许可拦截测试 | 跳过：本机矿工未启动")
        else:
            res = test_unpermitted_call(f"http://{local_ip}:{args.port}", my_hk, args.wallet, args.hotkey)
            print(f"4. 无验证许可拦截测试 | caller={args.wallet}/{args.hotkey}（permit=False） | {res}")
    print("=" * 96)


if __name__ == "__main__":
    main()
