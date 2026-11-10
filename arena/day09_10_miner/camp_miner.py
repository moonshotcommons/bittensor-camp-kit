#!/usr/bin/env python3
"""
第 9–10 天：共学营矿工 camp_miner.py（基于 bittensor SDK v11）

它做三件事：
  1. 用本地矿工 hotkey 启动一个 HTTP 服务，路径 POST /extract；
  2. 用 bt.http_auth.verify 校验每个请求的 hotkey 签名，再查链上元图，
     只接受“已注册且有验证许可（validator_permit）”的验证者，其他请求返回 401 / 403；
  3. 从中文材料中提取字段，并为每个字段附上原文原句作为依据。

加 --serve 时，会把本机 ip:port 发布到链上（serve_axon），验证者才能从元图里找到你。
链上会拒绝 127.0.0.1，所以默认发布本机局域网 IP。

第 10 天任务：这个版本里有两个真实的缺陷，会让验证者给你 0 分或收不到结果。
请根据验证者输出的原因和本程序的报错日志，找到并修复它们（提示：看 make_evidence 和 extract_field）。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import threading
import time
import traceback
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, Tuple

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from arena.common.chain import (  # noqa: E402
    default_netuid,
    default_network,
    fetch_metagraph,
    hotkey_ss58,
    lan_ip,
    load_wallet,
)

PATTERNS = {
    "项目名称": [r"生态项目 ([A-Za-z]+) ", r"算力网络 ([A-Za-z]+)（", r"】([A-Za-z]+) 团队"],
    "融资金额": [r"(\d+万美元)"],
    "领投机构": [r"由 (.+?) 领投", r"领投方为 (.+?)，"],
    "子网编号": [r"(\d+号) ?子网"],
}


# ---------------------------------------------------------------- 提取逻辑
def extract_field(field: str, text: str) -> str:
    m = None
    for p in PATTERNS.get(field, []):
        m = re.search(p, text)
        if m:
            break
    return m.group(1).strip()


def make_evidence(field: str, value: str, text: str) -> str:
    return f"{field}：{value}"


def extract_local(text: str, fields: list) -> Tuple[Dict[str, str], Dict[str, str], str]:
    data, quotes = {}, {}
    for f in fields:
        v = extract_field(f, text)
        data[f] = v
        quotes[f] = make_evidence(f, v, text) if v else ""
    return data, quotes, "local-rules"


def extract_chutes(text: str, fields: list) -> Tuple[Dict[str, str], Dict[str, str], str]:
    """可选：调用 Chutes（OpenAI 兼容接口）。需要在 .env 或环境变量里设置 CHUTES_API_KEY。
    模型和地址以 Chutes 控制台为准，下面只是默认值。"""
    base = os.getenv("CHUTES_BASE_URL", "https://llm.chutes.ai/v1").rstrip("/")
    model = os.getenv("CHUTES_MODEL", "")
    if not model:
        raise RuntimeError("请设置 CHUTES_MODEL（在 Chutes 控制台复制可用模型名）")
    prompt = (
        f"从下面的中文材料中提取字段 {fields}。只返回 JSON 对象，含两个键："
        "extracted_data（字段到值）和 evidence_quotes（字段到原文中一字不差的原句）。"
        "原文没有的字段，值和依据都填空字符串。\n材料：" + text
    )
    body = json.dumps(
        {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0}
    ).encode()
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {os.environ['CHUTES_API_KEY']}"},
    )
    with urllib.request.urlopen(req, timeout=2.5) as r:
        content = json.loads(r.read())["choices"][0]["message"]["content"]
    content = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
    out = json.loads(content)
    return out.get("extracted_data", {}), out.get("evidence_quotes", {}), f"chutes:{model}"


# ---------------------------------------------------------------- 验证者白名单
class PermitCache:
    """缓存链上元图，定期刷新，记录哪些 hotkey 有验证许可。"""

    def __init__(self, network: str, netuid: int, ttl: float = 60.0):
        self.network, self.netuid, self.ttl = network, netuid, ttl
        self._permitted: set[str] = set()
        self._at = 0.0
        self._lock = threading.Lock()

    def permitted(self) -> set[str]:
        with self._lock:
            if time.time() - self._at > self.ttl:
                mg = fetch_metagraph(self.network, self.netuid)
                self._permitted = {n.hotkey for n in mg.neurons if n.validator_permit}
                self._at = time.time()
            return self._permitted


# ---------------------------------------------------------------- HTTP 服务
def make_handler(my_hotkey: str, permits: PermitCache, use_chutes: bool):
    import bittensor as bt

    class Handler(BaseHTTPRequestHandler):
        def _send(self, code: int, obj: dict):
            raw = json.dumps(obj, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_POST(self):
            if self.path != "/extract":
                return self._send(404, {"error": "not found"})
            body = self.rfile.read(int(self.headers.get("Content-Length", 0)))

            # 1) 签名校验：证明请求确实来自某个 hotkey、发给我、内容没被改、时间新鲜
            try:
                caller = bt.http_auth.verify(
                    dict(self.headers), body, method="POST", path=self.path, self_hotkey_ss58=my_hotkey
                )
            except bt.http_auth.AuthError as e:
                print(f"🚫 401 签名校验失败：{e}", flush=True)
                return self._send(401, {"error": str(e)})

            # 2) 链上身份校验：只服务有验证许可的验证者
            if caller.hotkey_ss58 not in permits.permitted():
                print(f"🚫 403 拒绝：{caller.hotkey_ss58[:10]}… 没有验证许可", flush=True)
                return self._send(403, {"error": "caller has no validator permit on this subnet"})

            # 3) 干活
            t0 = time.time()
            task: dict = {}
            try:
                task = json.loads(body)
                if use_chutes:
                    data, quotes, engine = extract_chutes(task["raw_text"], task["required_fields"])
                else:
                    data, quotes, engine = extract_local(task["raw_text"], task["required_fields"])
            except Exception:
                print(f"💥 处理 {task.get('task_id', '?')} 时出错：", flush=True)
                traceback.print_exc()
                return self._send(500, {"error": "miner internal error"})

            ms = (time.time() - t0) * 1000
            print(
                f"📥 {task['task_id']} 来自 {caller.hotkey_ss58[:10]}… | {engine} | {ms:.1f}ms | "
                f"{json.dumps(data, ensure_ascii=False)}",
                flush=True,
            )
            self._send(200, {"task_id": task["task_id"], "extracted_data": data, "evidence_quotes": quotes, "engine": engine})

        def log_message(self, *_):
            pass

    return Handler


def serve_axon_on_chain(wallet, network: str, netuid: int, ip: str, port: int):
    import bittensor as bt

    mg = fetch_metagraph(network, netuid)
    me = next((n for n in mg.neurons if n.hotkey == hotkey_ss58(wallet)), None)
    if me is None:
        sys.exit(f"❌ 这个 hotkey 还没有在 netuid {netuid} 注册，先完成第 8 天的注册。")
    if me.axon == f"{ip}:{port}":
        print(f"ℹ️ 链上已登记 {me.axon}（UID {me.uid}），无需重复发布。")
        return
    client = bt.Subtensor(network)
    res = client.execute(bt.ServeAxon(netuid=netuid, ip=ip, port=port), wallet)
    if not res.success:
        sys.exit(f"❌ 发布 Axon 失败：{res.error.code} — {res.error.remediation}")
    print(f"✅ 已把 {ip}:{port} 写上链（UID {me.uid}），区块 {res.block_hash}")


def main():
    ap = argparse.ArgumentParser(description="共学营矿工（bittensor v11 + btauth 签名请求）")
    ap.add_argument("--wallet", default=os.getenv("CAMP_MINER_WALLET", "miner"))
    ap.add_argument("--hotkey", default=os.getenv("CAMP_MINER_HOTKEY", "default"))
    ap.add_argument("--network", default=default_network())
    ap.add_argument("--netuid", type=int, default=default_netuid())
    ap.add_argument("--port", type=int, default=8091)
    ap.add_argument("--external-ip", default="", help="发布到链上的 IP；默认本机局域网 IP（云主机请填公网 IP）")
    ap.add_argument("--serve", action="store_true", help="启动前把 ip:port 发布到链上")
    ap.add_argument("--use-chutes", action="store_true", help="使用 Chutes 大模型接口提取（需设置 CHUTES_API_KEY 与 CHUTES_MODEL）")
    args, _ = ap.parse_known_args()

    wallet = load_wallet(args.wallet, args.hotkey)
    my_hk = hotkey_ss58(wallet)
    ip = args.external_ip or lan_ip()
    if args.serve:
        serve_axon_on_chain(wallet, args.network, args.netuid, ip, args.port)

    use_chutes = args.use_chutes
    permits = PermitCache(args.network, args.netuid)
    server = ThreadingHTTPServer(("0.0.0.0", args.port), make_handler(my_hk, permits, use_chutes))
    print("=" * 72)
    print(f"🚀 矿工已启动  hotkey={my_hk}")
    print(f"   网络={args.network}  netuid={args.netuid}  监听 0.0.0.0:{args.port}  对外 {ip}:{args.port}")
    print(f"   提取引擎={'Chutes' if use_chutes else '本地规则'}")
    print("=" * 72, flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")


def _cli_entry():
    from arena.common.chain import LOCALNET_DIR, ensure_port_free

    ThreadingHTTPServer.allow_reuse_address = True
    port = 8091
    for i, a in enumerate(sys.argv[1:], 1):
        if a == "--port" and i < len(sys.argv):
            port = int(sys.argv[i + 1])
    ensure_port_free(port)
    if "-d" in sys.argv or "--daemon" in sys.argv:
        import subprocess

        ap = argparse.ArgumentParser(add_help=False)
        ap.add_argument("--wallet", default=os.getenv("CAMP_MINER_WALLET", "miner"))
        ap.add_argument("--hotkey", default=os.getenv("CAMP_MINER_HOTKEY", "default"))
        ap.add_argument("--network", default=default_network())
        ap.add_argument("--netuid", type=int, default=default_netuid())
        ap.add_argument("--port", type=int, default=8091)
        ap.add_argument("--external-ip", default="")
        ap.add_argument("--serve", action="store_true")
        ap.add_argument("--use-chutes", action="store_true")
        args, _ = ap.parse_known_args()
        wallet = load_wallet(args.wallet, args.hotkey)
        ip = args.external_ip or lan_ip()
        if args.serve:
            serve_axon_on_chain(wallet, args.network, args.netuid, ip, args.port)
        LOCALNET_DIR.mkdir(exist_ok=True)
        log_file = LOCALNET_DIR / "miner.log"
        cmd = [
            sys.executable, "-u", str(Path(__file__).resolve()),
            "--wallet", args.wallet, "--hotkey", args.hotkey,
            "--network", args.network, "--netuid", str(args.netuid),
            "--port", str(args.port), "--external-ip", ip,
        ]
        if args.use_chutes:
            cmd.append("--use-chutes")
        out = open(log_file, "w", encoding="utf-8")
        proc = subprocess.Popen(cmd, stdout=out, stderr=subprocess.STDOUT, start_new_session=True)
        time.sleep(0.8)
        print(f"🚀 矿工已在后台启动（PID {proc.pid}，监听 {ip}:{args.port}）")
        print(f"📄 实时日志：{log_file}（可执行 tail -f .localnet/miner.log 查看）")
        return
    main()


if __name__ == "__main__":
    _cli_entry()
