#!/usr/bin/env bash
# Bittensor 共学营：启动本地教学链
# 使用官方镜像 ghcr.io/raofoundation/subtensor-localnet:devnet，
# 并传入 False 开启 12 秒出块模式（避免快速出块模式下 MEV 加密交易因区块时代过期而失败）。
set -euo pipefail

IMAGE="ghcr.io/raofoundation/subtensor-localnet:devnet"
CONTAINER_NAME="local_chain"

if docker ps --format '{{.Names}}' | grep -qx "${CONTAINER_NAME}"; then
  echo "ℹ️ 本地链容器 ${CONTAINER_NAME} 已在运行（ws://127.0.0.1:9944）。"
  exit 0
fi

docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true

echo "🚀 启动本地教学链容器 ${CONTAINER_NAME}（12 秒出块模式，端口 9944/9945）……"
docker run -d --rm \
  --name "${CONTAINER_NAME}" \
  -p 9944:9944 \
  -p 9945:9945 \
  "${IMAGE}" False >/dev/null

echo "⏳ 等待本地链 RPC 就绪……"
for _ in $(seq 1 30); do
  if curl -s -H "Content-Type: application/json" \
       -d '{"id":1,"jsonrpc":"2.0","method":"system_health","params":[]}' \
       http://127.0.0.1:9944 >/dev/null 2>&1; then
    echo "✅ 本地教学链已就绪：ws://127.0.0.1:9944"
    exit 0
  fi
  sleep 1
done

echo "❌ 等待超时，请用 docker logs ${CONTAINER_NAME} 查看原因。"
exit 1
