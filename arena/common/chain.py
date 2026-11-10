"""
共学营公共工具：钱包加载、链上元图读取、本机局域网 IP 探测。
基于 bittensor SDK v11（v11 已移除 Axon/Dendrite，节点之间用普通 HTTP + bt.http_auth 签名）。
"""

from __future__ import annotations

import os
import socket
from pathlib import Path
from typing import Optional

KIT_DIR = Path(__file__).resolve().parents[2]
LOCALNET_DIR = KIT_DIR / ".localnet"


def _patch_http_auth_compat() -> None:
    """兼容 bittensor 11.3.0 与 11.3.2+：若新版 verify 要求 expected_crypto_type，默认补齐 sr25519。"""
    try:
        import inspect
        import bittensor as bt

        orig_verify = getattr(bt.http_auth, "verify", None)
        if orig_verify is None or getattr(orig_verify, "_camp_patched", False):
            return
        sig = inspect.signature(orig_verify)
        if "expected_crypto_type" in sig.parameters:
            def _compat_verify(*args, **kwargs):
                kwargs.setdefault("expected_crypto_type", 1)
                return orig_verify(*args, **kwargs)

            _compat_verify._camp_patched = True  # type: ignore[attr-defined]
            bt.http_auth.verify = _compat_verify
    except Exception:
        pass


_patch_http_auth_compat()


def default_wallet_path() -> str:
    """优先用环境变量 BT_WALLET_PATH；本地链练习默认用 camp-kit/.localnet/wallets，不碰你的真实钱包。"""
    env = os.getenv("BT_WALLET_PATH")
    if env:
        return env
    return str(LOCALNET_DIR / "wallets")


def default_network() -> str:
    return os.getenv("BT_NETWORK", "local")


def default_netuid() -> int:
    env = os.getenv("CAMP_NETUID")
    if env:
        return int(env)
    f = LOCALNET_DIR / "netuid"
    if f.exists():
        return int(f.read_text().strip())
    return 2


def load_wallet(name: str, hotkey: str = "default", path: Optional[str] = None):
    from bittensor.wallet import Wallet

    return Wallet(name=name, hotkey=hotkey, path=path or default_wallet_path())


def hotkey_ss58(wallet) -> str:
    return wallet.hotkey.ss58_address


def lan_ip() -> str:
    """
    链上会拒绝 127.0.0.1（InvalidIpAddress），所以发布 Axon 时要用本机局域网 IP 或公网 IP。
    开着代理/VPN（TUN 模式）的电脑，系统默认路由常指向 198.18.x.x 这类虚拟网卡，
    其他机器连不到它，所以这里优先选 192.168.x.x，再选 172.16–31.x.x、10.x.x.x。
    也可以用环境变量 CAMP_EXTERNAL_IP 直接指定。
    """
    import ipaddress

    if os.getenv("CAMP_EXTERNAL_IP"):
        return os.environ["CAMP_EXTERNAL_IP"]
    candidates = []
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        candidates.append(s.getsockname()[0])
    except OSError:
        pass
    finally:
        s.close()
    try:
        candidates += socket.gethostbyname_ex(socket.gethostname())[2]
    except OSError:
        pass
    fake = ipaddress.ip_network("198.18.0.0/15")
    usable = []
    for c in candidates:
        ip = ipaddress.ip_address(c)
        if ip.is_loopback or ip in fake or not ip.is_private:
            continue
        usable.append(c)

    def rank(c: str) -> int:
        if c.startswith("192.168."):
            return 0
        if ipaddress.ip_address(c) in ipaddress.ip_network("172.16.0.0/12"):
            return 1
        return 2

    return sorted(dict.fromkeys(usable), key=rank)[0] if usable else "127.0.0.1"


def fetch_metagraph(network: str, netuid: int):
    """同步读取一次子网元图（返回 bt.Metagraph，neurons 列表中每项是 bt.MetagraphNeuron）。"""
    import bittensor as bt

    client = bt.Subtensor(network)
    return client.subnets.metagraph(netuid)


def ensure_port_free(port: int) -> None:
    """
    若目标端口已被之前后台运行的旧矿工/陪练进程占用（例如从 Jupyter 切换到终端，
    或上次未完全退出），自动清理残留进程并释放端口，避免报 Address already in use。
    """
    import signal
    import subprocess
    import time

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        if s.connect_ex(("127.0.0.1", port)) != 0:
            return

    my_pid = os.getpid()
    killed_pids = []
    try:
        out = subprocess.check_output(
            ["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN", "-t"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        for line in out.splitlines():
            line = line.strip()
            if not line.isdigit():
                continue
            pid = int(line)
            if pid == my_pid:
                continue
            try:
                comm = subprocess.check_output(
                    ["ps", "-p", str(pid), "-o", "comm="],
                    stderr=subprocess.DEVNULL,
                    text=True,
                ).strip().lower()
                if any(k in comm for k in ("docker", "vpnkit", "orbstack", "limactl", "qemu")):
                    subprocess.run(
                        ["docker", "rm", "-f", "bittensor-camp-miner", "bittensor-camp-monitor"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    continue
            except Exception:
                pass
            try:
                os.kill(pid, signal.SIGTERM)
                killed_pids.append(pid)
            except OSError:
                pass
    except Exception:
        pass

    if killed_pids:
        for _ in range(15):
            time.sleep(0.1)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.2)
                if s.connect_ex(("127.0.0.1", port)) != 0:
                    break
        else:
            for pid in killed_pids:
                try:
                    os.kill(pid, signal.SIGKILL)
                except OSError:
                    pass
            time.sleep(0.2)
        print(f"ℹ️ 端口 {port} 被上次残留的后台进程（PID {','.join(map(str, killed_pids))}）占用，已自动停止旧进程并释放端口。")
