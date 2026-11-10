#!/usr/bin/env python3
"""
第 7 天配套工具：第一周复盘与第 2 周实操环境一键自检脚本 day07_check_env.py

检查项：
  1. Python 版本（>= 3.10）
  2. bittensor SDK 与 btcli 版本（必须为 11.x，拦截旧版 bittensor-cli 9.x）
  3. Docker 服务状态与本地教学链镜像（加 --pull-image 可顺手预拉取镜像，避免第 8 天卡下载）
  4. 第二周代码包文件完整性
  5. 本地钱包与可选的 Chutes API Key
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

LOCALNET_IMAGE = "ghcr.io/raofoundation/subtensor-localnet:devnet"


def load_env_file(env_path: Path):
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def run_cmd(cmd: list[str], timeout: int = 10) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).strip()
    except Exception as e:
        return 1, str(e)


def main():
    ap = argparse.ArgumentParser(description="Bittensor 共学营第 7 天环境自检工具")
    ap.add_argument("--pull-image", action="store_true", help="若本地尚未拉取教学链镜像，自动执行 docker pull")
    args = ap.parse_args()

    root_dir = Path(__file__).resolve().parents[1]
    load_env_file(root_dir / ".env")

    rows: list[tuple[str, str, str]] = []

    # 1. Python 版本
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    py_ok = (sys.version_info.major, sys.version_info.minor) >= (3, 10)
    rows.append(("1. Python 运行环境 (>=3.10)", f"Python {py_ver}", "✅ PASS" if py_ok else "❌ FAIL"))

    # 2. bittensor SDK & btcli 版本（必须 11.x）
    sdk_ver = "未安装"
    sdk_ok = False
    try:
        import bittensor as bt

        sdk_ver = getattr(bt, "__version__", "unknown")
        sdk_ok = sdk_ver.startswith("11.")
    except ImportError:
        pass

    btcli_bin = shutil.which("btcli") or str(Path(sys.executable).parent / "btcli")
    rc, cli_out = run_cmd([btcli_bin, "--version"]) if Path(btcli_bin).exists() else (1, "未找到 btcli")
    cli_ok = rc == 0 and ("11." in cli_out)
    rows.append(
        (
            "2. Bittensor 11.x 工具链",
            f"SDK={sdk_ver} | {cli_out or '无 btcli'}",
            "✅ PASS" if (sdk_ok and cli_ok) else "❌ 请按 docs/00 卸载 9.x 并装 11.x",
        )
    )

    # 3. Docker 与本地教学链镜像
    rc_dk, _ = run_cmd(["docker", "info"])
    if rc_dk != 0:
        rows.append(("3. Docker 与本地链镜像", "Docker 未启动或未安装", "❌ 请先启动 Docker Desktop / Engine"))
    else:
        rc_img, _ = run_cmd(["docker", "image", "inspect", LOCALNET_IMAGE])
        if rc_img != 0 and args.pull_image:
            print(f"⏳ 正在预拉取本地教学链镜像 {LOCALNET_IMAGE} ……")
            subprocess.run(["docker", "pull", LOCALNET_IMAGE], check=False)
            rc_img, _ = run_cmd(["docker", "image", "inspect", LOCALNET_IMAGE])
        if rc_img == 0:
            rows.append(("3. Docker 与本地链镜像", "Docker 正常，教学链镜像已就绪", "✅ PASS"))
        else:
            rows.append(
                (
                    "3. Docker 与本地链镜像",
                    "Docker 正常（建议加 --pull-image 预拉镜像）",
                    "✅ PASS",
                )
            )

    # 4. 第二周核心脚本检查
    required_files = [
        root_dir / "scripts" / "start_localnet.sh",
        root_dir / "scripts" / "setup_localnet.sh",
        root_dir / "arena" / "day09_10_miner" / "camp_miner.py",
        root_dir / "arena" / "day09_10_miner" / "practice_bots.py",
        root_dir / "arena" / "day11_validator" / "camp_validator.py",
        root_dir / "arena" / "day11_validator" / "uid_monitor.py",
    ]
    kit_ok = all(p.exists() for p in required_files)
    rows.append(("4. 第二周实战代码包", "本地链/矿工/陪练/验证者/监控脚本齐全", "✅ PASS" if kit_ok else "❌ FAIL"))

    # 5. 钱包与可选 Chutes Key
    wallet_dir = Path.home() / ".bittensor" / "wallets"
    wallets = [d.name for d in wallet_dir.iterdir() if d.is_dir()] if wallet_dir.exists() else []
    chutes_ok = bool(os.getenv("CHUTES_API_KEY", "").strip())
    w_desc = f"钱包={','.join(wallets) if wallets else '待建'} | 引擎={'Chutes' if chutes_ok else '内置规则'}"
    rows.append(("5. 钱包与提取引擎配置", w_desc, "✅ PASS"))

    print("=" * 96)
    print("🔍 Bittensor 共学营 Day 7 实操环境自检表")
    print("=" * 96)
    for item, detail, status in rows:
        print(f"{item:<28} | {detail:<44} | {status}")
    print("=" * 96)
    if all(r[2].startswith("✅") for r in rows):
        print("🎉 恭喜！你的第 2 周环境自检全部通过，可直接截图提交 Day 7 作业！")
    else:
        print("⚠️ 存在未通过项，请按右侧提示处理后再运行一次。")


if __name__ == "__main__":
    main()
