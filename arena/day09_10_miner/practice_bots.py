#!/usr/bin/env python3
"""
陪练矿工（助教在本地链上运行）：两个真实注册在教学子网上的 hotkey，作为学员矿工的对手。

  bot_fast：几乎立刻返回，字段大多正确，但依据是编造的总结句 → 应被验证者判 0 分
  bot_slow：依据来自原文，但每次固定慢 2 秒，且从不提取领投机构 → 低分

这两个机器人的行为是刻意设计的教学对照，不代表真实子网中的矿工。
需要先用 scripts/setup_localnet.sh 注册 miner/bot_fast 和 miner/bot_slow 两个 hotkey。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from arena.common.chain import LOCALNET_DIR, default_netuid, default_network, ensure_port_free, fetch_metagraph, hotkey_ss58, lan_ip, load_wallet  # noqa: E402
from arena.day09_10_miner.camp_miner import PATTERNS, PermitCache, serve_axon_on_chain  # noqa: E402


def _value(field, text):
    for p in PATTERNS[field]:
        m = re.search(p, text)
        if m:
            return m.group(1).strip()
    return ""


# --- 3 号陪练 bot_fast 与 4 号陪练 bot_slow 对比实现 ---
def answer_fast(task):
    data = {f: _value(f, task["raw_text"]) for f in task["required_fields"]}
    quotes = {f: ("AI 总结：数据真实可靠" if v else "") for f, v in data.items()}
    return data, quotes


def answer_slow(task):
    time.sleep(2.0)  # 故意慢 2 秒
    data = {f: ("" if f == "领投机构" else _value(f, task["raw_text"])) for f in task["required_fields"]}
    quotes = {}
    for f, v in data.items():
        sents = [s.strip() for s in re.split(r"[。！？]", task["raw_text"]) if v and v in s]
        quotes[f] = sents[0] if sents else ""
    return data, quotes


def run_bot(name, port, answer, network, netuid, ip, lock, skip_serve=False):
    import bittensor as bt

    wallet = load_wallet("miner", name)
    my_hk = hotkey_ss58(wallet)
    if not skip_serve:
        with lock:
            serve_axon_on_chain(wallet, network, netuid, ip, port)
    permits = PermitCache(network, netuid)

    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            try:
                caller = bt.http_auth.verify(dict(self.headers), body, method="POST", path=self.path, self_hotkey_ss58=my_hk)
            except bt.http_auth.AuthError as e:
                self.send_response(401); self.end_headers(); self.wfile.write(str(e).encode()); return
            if caller.hotkey_ss58 not in permits.permitted():
                self.send_response(403); self.end_headers(); return
            task = json.loads(body)
            data, quotes = answer(task)
            raw = json.dumps({"task_id": task["task_id"], "extracted_data": data, "evidence_quotes": quotes, "engine": name}, ensure_ascii=False).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def log_message(self, *_):
            pass

    print(f"🤖 {name} 监听 0.0.0.0:{port}  hotkey={my_hk}", flush=True)
    ThreadingHTTPServer.allow_reuse_address = True
    ThreadingHTTPServer(("0.0.0.0", port), H).serve_forever()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--network", default=default_network())
    ap.add_argument("--netuid", type=int, default=default_netuid())
    ap.add_argument("--external-ip", default="")
    ap.add_argument("-d", "--daemon", action="store_true", help="后台运行（无需另开终端窗口，日志写入 .localnet/bots.log）")
    ap.add_argument("--no-serve", action="store_true", help=argparse.SUPPRESS)
    args = ap.parse_args()
    ip = args.external_ip or lan_ip()
    ensure_port_free(8092)
    ensure_port_free(8093)

    if args.daemon:
        import subprocess

        for name, port in (("bot_fast", 8092), ("bot_slow", 8093)):
            w = load_wallet("miner", name)
            serve_axon_on_chain(w, args.network, args.netuid, ip, port)
        LOCALNET_DIR.mkdir(exist_ok=True)
        log_file = LOCALNET_DIR / "bots.log"
        cmd = [
            sys.executable,
            "-u",
            str(Path(__file__).resolve()),
            "--network",
            args.network,
            "--netuid",
            str(args.netuid),
            "--external-ip",
            ip,
            "--no-serve",
        ]
        out = open(log_file, "w", encoding="utf-8")
        proc = subprocess.Popen(cmd, stdout=out, stderr=subprocess.STDOUT, start_new_session=True)
        time.sleep(0.8)
        print(f"🤖 两个陪练矿工已在后台启动（PID {proc.pid}，监听 {ip}:8092 / 8093）")
        print(f"📄 实时日志：{log_file}（可执行 tail -f .localnet/bots.log 查看）")
        return

    lock = threading.Lock()
    threads = [
        threading.Thread(target=run_bot, args=("bot_fast", 8092, answer_fast, args.network, args.netuid, ip, lock, args.no_serve), daemon=True),
        threading.Thread(target=run_bot, args=("bot_slow", 8093, answer_slow, args.network, args.netuid, ip, lock, args.no_serve), daemon=True),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


if __name__ == "__main__":
    main()
