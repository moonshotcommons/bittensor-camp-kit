#!/usr/bin/env bash
# Bittensor 共学营：本地教学链一键初始化
# 作用：在本地私有链上准备 owner / validator / miner（含 2 个陪练 hotkey），
#       创建教学子网、调短教学周期（tempo=10）、注册身份、给验证者质押以取得验证许可。
# 前提：已用 scripts/start_localnet.sh 启动本地链（12 秒出块模式，ws://127.0.0.1:9944）。
# 说明：本地链的 Alice 账户和种子是公开的开发用密钥，只能在本地链使用。
set -euo pipefail

KIT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
export BT_WALLET_PATH="${BT_WALLET_PATH:-${KIT_DIR}/.localnet/wallets}"
export BT_NETWORK=local
if [ -z "${BTCLI:-}" ]; then
  if [ -x "${KIT_DIR}/.venv/bin/btcli" ]; then
    BTCLI="${KIT_DIR}/.venv/bin/btcli"
  else
    BTCLI="btcli"
  fi
fi
ALICE_SEED="0xe5be9a5092b81bca64be81d212e7f2f9eba183bb7a90954f7b76361f6edb5c0a"
STAKE_TAO="${STAKE_TAO:-30}"

step() { printf '\n==== %s ====\n' "$1"; }

step "1/8 检查本地链连接（需为 12 秒出块模式，is_fast_blocks: false）"
"${BTCLI}" query is-fast-blocks

step "2/8 准备钱包（alice / owner / validator / miner + 2 个陪练 hotkey）"
[ -d "${BT_WALLET_PATH}/alice" ] || "${BTCLI}" wallet regen-coldkey -w alice --no-password --seed "${ALICE_SEED}" >/dev/null
for w in owner validator miner; do
  [ -d "${BT_WALLET_PATH}/${w}" ] || "${BTCLI}" wallet create -w "${w}" -H default --no-password >/dev/null
done
for hk in bot_fast bot_slow; do
  [ -f "${BT_WALLET_PATH}/miner/hotkeys/${hk}" ] || "${BTCLI}" wallet new-hotkey -w miner -H "${hk}" >/dev/null
done
"${BTCLI}" wallet list

step "3/8 从 Alice 给三个角色转测试 TAO"
"${BTCLI}" tx transfer --dest owner --amount-tao 2000 -w alice -y >/dev/null
"${BTCLI}" tx transfer --dest validator --amount-tao 500 -w alice -y >/dev/null
"${BTCLI}" tx transfer --dest miner --amount-tao 100 -w alice -y >/dev/null
echo "已转账：owner 2000 / validator 500 / miner 100 TAO"

step "4/8 owner 创建教学子网并启动排放"
mkdir -p "${KIT_DIR}/.localnet"
"${BTCLI}" tx register-subnet -w owner -y | tee "${KIT_DIR}/.localnet/register_subnet.txt"
NETUID="$(grep -E '^\s*netuid' "${KIT_DIR}/.localnet/register_subnet.txt" | awk '{print $2}' | head -n1)"
echo "教学子网 netuid = ${NETUID}"
echo "${NETUID}" > "${KIT_DIR}/.localnet/netuid"
"${BTCLI}" tx start-call --netuid "${NETUID}" -w owner -y >/dev/null
echo "已启动 netuid ${NETUID} 的排放"

step "5/8 注册验证者、学员矿工与 2 个陪练矿工"
"${BTCLI}" tx burned-register --netuid "${NETUID}" -w validator -H default -y
"${BTCLI}" tx burned-register --netuid "${NETUID}" -w miner -H default -y
"${BTCLI}" tx burned-register --netuid "${NETUID}" -w miner -H bot_fast -y
"${BTCLI}" tx burned-register --netuid "${NETUID}" -w miner -H bot_slow -y

step "6/8 调短教学子网周期（tempo=10 块≈2分钟，权重间隔=5 块，端点更新间隔=1 块）"
"${BTCLI}" call AdminUtils.sudo_set_admin_freeze_window --args '{"window": 0}' --sudo -w alice -y >/dev/null
"${BTCLI}" call AdminUtils.sudo_set_max_allowed_validators --args "{\"netuid\": ${NETUID}, \"max_allowed_validators\": 2}" --sudo -w alice -y >/dev/null
"${BTCLI}" call AdminUtils.sudo_set_weights_set_rate_limit --args "{\"netuid\": ${NETUID}, \"weights_set_rate_limit\": 5}" --sudo -w alice -y >/dev/null
"${BTCLI}" call AdminUtils.sudo_set_serving_rate_limit --args "{\"netuid\": ${NETUID}, \"serving_rate_limit\": 1}" --sudo -w alice -y >/dev/null
"${BTCLI}" call AdminUtils.sudo_set_tempo --args "{\"netuid\": ${NETUID}, \"tempo\": 10}" --sudo -w alice -y >/dev/null

step "7/8 给验证者质押 ${STAKE_TAO} TAO（用于取得验证许可 validator_permit）"
# 新建本地子网资金池较小，30 TAO 会带来约 3%–8% 的价格滑动，放宽滑点容忍度到 20%。
"${BTCLI}" tx add-stake --netuid "${NETUID}" --amount-tao "${STAKE_TAO}" --rate-tolerance 0.2 -w validator -H default -y

step "8/8 读回链上注册状态"
"${BTCLI}" wallet registrations -w validator
"${BTCLI}" wallet registrations -w miner
echo
echo "完成。教学子网编号已保存在 .localnet/netuid（netuid=${NETUID}）。"
echo "若用 btcli 直接查询本地链，请加："
echo "  export BT_WALLET_PATH=${BT_WALLET_PATH} BT_NETWORK=local CAMP_NETUID=${NETUID}"
