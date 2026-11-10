# Bittensor 14 天开发者共学营 · 配套实战代码库

[![Bittensor SDK](https://img.shields.io/badge/Bittensor_SDK-%3E%3D11.3.0-000000?style=flat-square)](https://www.bittensor.com/docs)
[![Python](https://img.shields.io/badge/Python-3.10--3.14-3776AB?style=flat-square)](https://www.python.org/)
[![Subtensor Localnet](https://img.shields.io/badge/Localnet-Docker_Subtensor-2496ED?style=flat-square)](https://www.bittensor.com/docs/guides/local-development)
[![Community](https://img.shields.io/badge/HackQuest-Bittensor_中文社区-FFE866?style=flat-square&labelColor=262626)](https://www.hackquest.io/zh-cn/organization/Bittensor/community-organizer/Bittensor-中文社区)

本仓库是 **《Bittensor：从生态入门到角色参与》中文系列课程** 与 **14 天开发者共学营** 的官方配套实战代码库，全面基于 **`bittensor` v11.x**（Python SDK v11 + `btcli` v11）构建。

在两周的实战中，你将完成从**主网链上账本观测、dTAO 经济模型核算、Yuma 共识防刷分推演**（第一周），到**本地教学链子网搭建、矿工签名鉴权与代码排障、验证者 EMA 评分与 Commit-Reveal 权重上链、PM2 进程自愈及 Docker 容器化部署**（第二周）的完整工程闭环。

---

## 📚 课程体系与 14 天实战路线图

| 阶段 | 日程 | 核心课题 | 配套视频课 | 配套代码 / 工具 / 练习 |
| :--- | :--- | :--- | :--- | :--- |
| **第一周**<br>认知规则与链上账本 | **Day 1** | Bittensor 生态全景与四类角色分工 | 第 01 课 | [`docs/02_14天共学营学习计划与每日任务.md`](docs/02_14天共学营学习计划与每日任务.md) |
| | **Day 2** | 钱包体系（Coldkey/Hotkey）与 `btcli` 11.x 操作 | 第 02 课 | [`docs/00_环境安装与版本说明.md`](docs/00_环境安装与版本说明.md) · Notebook `TODO 0` |
| | **Day 3** | dTAO 子网池、注册销毁费（Burn）与新手保护期 | 第 03 课 | Notebook `TODO 1`（`burn` / `immunity_period` 换算） |
| | **Day 4** | 读懂元图（Metagraph）：区分矿工与验证者及日产出估算 | — | Notebook `TODO 2`（元图字段解析与日排放计算） |
| | **Day 5** | Yuma 共识 $\kappa=0.50$ 质押截断与 Commit-Reveal 机制 | 第 08 课（共识篇） | [`tools/day05_yuma_sim.py`](tools/day05_yuma_sim.py) · 生成交互式 `.xlsx` 模拟器 |
| | **Day 6** | 推理类子网（SN64/SN1）与数据类子网（SN13）选型与成本核算 | 第 06 课（上半） | Notebook 主网多子网实时对比查询 |
| | **Day 7** | 第一周复盘与第二周本地链 Docker 环境预检 | — | [`tools/day07_check_env.py`](tools/day07_check_env.py) |
| **第二周**<br>本地链矿工与验证者实战 | **Day 8** | 启动本地教学链、创建子网、注册节点与取得验证许可 | 第 06 课（下半） | [`scripts/start_localnet.sh`](scripts/start_localnet.sh) · [`scripts/setup_localnet.sh`](scripts/setup_localnet.sh) · `TODO 3` |
| | **Day 9** | 启动矿工与陪练节点，完成首次签名请求验证与评测现场复现 | 第 06 课（下半） | [`arena/day09_10_miner/camp_miner.py`](arena/day09_10_miner/camp_miner.py) · [`practice_bots.py`](arena/day09_10_miner/practice_bots.py) |
| | **Day 10** | 矿工端口/端点自检、403 门禁实测与两处代码缺陷修复夺冠 | 第 07 课 | [`arena/day09_10_miner/diagnose_node.py`](arena/day09_10_miner/diagnose_node.py) · [`solutions/DAY10_MINER_FIXES.md`](solutions/DAY10_MINER_FIXES.md) |
| | **Day 11** | 验证者 EMA 权重折算、`SetWeights` 上链、时间锁解密与激励监控 | 第 08 课 | [`arena/day11_validator/camp_validator.py`](arena/day11_validator/camp_validator.py) · [`uid_monitor.py`](arena/day11_validator/uid_monitor.py) · `TODO 4` |
| | **Day 12** | PM2 多进程守护、崩溃自动拉起与日志轮转 | 第 07 课（运维篇） | [`arena/day12_pm2/ecosystem.config.js`](arena/day12_pm2/ecosystem.config.js) |
| | **Day 13** | Docker Compose 容器化封装与热密钥只读挂载（`:ro`） | 第 07 课（运维篇） | [`arena/day13_docker/docker-compose.yml`](arena/day13_docker/docker-compose.yml) · [`Dockerfile`](arena/day13_docker/Dockerfile) |
| | **Day 14** | 全链路闭环链上状态核验与结营总结 | — | Notebook 结营技术验收单 · [`docs/01_矿工日常运营与收支记录模板.md`](docs/01_矿工日常运营与收支记录模板.md) |

---

## 🚀 5 分钟快速开始（Quick Start）

### 1. 环境前置要求
* **操作系统**：macOS 或 Linux（Windows 用户请使用 **WSL 2** 或 Linux 云主机，Bittensor 官方不支持原生 Windows 挖矿与验证）。
* **基础软件**：Python `3.10` – `3.14`；第二周本地链实操需安装并启动 [Docker Desktop](https://www.docker.com/products/docker-desktop/)（或 Docker Engine）。
* **核心包约定**：仅安装 `bittensor>=11.3.0`（已内含 Python SDK、`btcli` 11.x 与钱包模块）。**切勿安装**旧版独立包 `bittensor-cli`（停留在 `9.x`，会覆盖新版 `btcli` 命令）。详见 [`docs/00_环境安装与版本说明.md`](docs/00_环境安装与版本说明.md)。

### 2. 获取代码并创建标准 `.venv` 虚拟环境

在终端执行以下命令克隆仓库（或解压下载的 Release 压缩包），并在项目根目录下创建标准 `.venv` 虚拟环境：

```bash
# 1. 克隆仓库并进入项目根目录（若下载的是 ZIP 压缩包，解压后 cd 进入解压目录即可）
git clone https://github.com/moonshotcommons/bittensor-camp-kit.git
cd bittensor-camp-kit

# 2. 创建并激活标准 .venv 虚拟环境，安装课程依赖
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. 验证 btcli 版本（应显示 11.x）
btcli --version
```

### 3. 选择你的学习方式（二选一）

#### 🌟 方式一（推荐）：一册到底交互式 Jupyter Notebook
我们将 **14 天全部原理导读、分步实验、代码填空（`TODO 0`–`TODO 4`）、矿工热修复排障与后台容器控制** 完整集成在根目录的交互式手册中，无需在多个终端窗口之间来回切换：

👉 **[`Bittensor_14天共学营_交互式实战手册.ipynb`](Bittensor_14天共学营_交互式实战手册.ipynb)**

* **在 VS Code / Cursor 中运行**：
  1. 使用菜单栏 **`File -> Open Folder...` 打开整个项目文件夹**（或在终端执行 `code .`）。
     > ⚠️ **防坑提示**：
     > * **必须打开文件夹**：切勿从 Finder/资源管理器直接双击打开单个 `.ipynb` 文件，否则无工作区路径时 VS Code 不会扫描当前目录的 `.venv`。
     > * **信任工作区（Workspace Trust）**：若首次打开弹窗询问 *"Do you trust the authors of the files in this folder?"*（或左下角状态栏显示 **Restricted Mode**），请点击 **Yes, I trust the authors / Trust**。在未信任的受限模式下，VS Code 会禁用 Python 环境扩展，导致列表里看不到 `.venv`。
  2. 打开 `Bittensor_14天共学营_交互式实战手册.ipynb`，点击右上角 **Select Kernel -> Python Environments...**，选择 **`.venv (Python 3.x)`**。
  3. 从第 1 个代码单元格（`[环境初始化与依赖一键自检]`）开始，依次点击左侧 **▶ (Run)** 向下运行即可。
* **在浏览器 JupyterLab 中运行**：
  ```bash
  source .venv/bin/activate
  jupyter lab Bittensor_14天共学营_交互式实战手册.ipynb
  ```

#### 💻 方式二：终端命令行 + 模块化脚本分步实操
如果你偏好在终端中直接操控节点、分屏观察实时日志，请直接参考下方的 **[分步终端实操指南](#-分步终端实操指南day-2--day-14)**。

---

## 📂 仓库目录结构

```text
bittensor-camp-kit/
├── Bittensor_14天共学营_交互式实战手册.ipynb  # ⭐ 14 天一册到底交互式实战 Notebook（含讲解、实验与自动断言校验）
├── README.md                                 # 项目总览、快速开始与分步终端实操指南
├── requirements.txt                          # Python 依赖清单（bittensor>=11.3.0, rich, openpyxl, jupyterlab）
├── .env.example                              # 可选环境变量模板（Chutes API Key 等）
├── docs/
│   ├── 00_环境安装与版本说明.md              # bittensor v11 安装规范、旧版卸载修复与 v9 -> v11 命令对照表
│   ├── 01_矿工日常运营与收支记录模板.md      # 第 07 课配套：节点基线、评分日志、成本与链上奖励分立账本
│   └── 02_14天共学营学习计划与每日任务.md    # 14 天每日学习目标、配套资料索引与打卡验收题目
├── scripts/
│   ├── start_localnet.sh                     # Day 8：启动 Docker 本地教学链（12 秒标准出块模式）
│   └── setup_localnet.sh                     # Day 8：创建教学子网、配置超参数（tempo=10）、注册身份并质押
├── tools/
│   ├── day05_yuma_sim.py                     # Day 5：Yuma 共识 κ=0.50 质押截断与防刷分模拟器（导出 CSV/XLSX）
│   └── day07_check_env.py                    # Day 7：第二周本地链环境与 Docker 镜像一键预检脚本
├── arena/
│   ├── common/
│   │   ├── chain.py                          # 本地链/钱包加载、SDK 兼容补丁与局域网 IP 探测（过滤虚拟网卡）
│   │   ├── protocol.py                       # 中文结构化提取任务协议与三关评分函数（准确率 70% + 速度 30%）
│   │   └── tasks_bank.py                     # 动态随机生成的中文融资快讯题库（含缺失字段简讯题）
│   ├── day09_10_miner/
│   │   ├── camp_miner.py                     # Day 9–10：学员矿工（HTTP 服务 + sr25519 签名校验 + 验证许可白名单）
│   │   ├── practice_bots.py                  # Day 9–11：两个链上陪练矿工（bot_fast: 8092，bot_slow: 8093）
│   │   └── diagnose_node.py                  # Day 10：端口监听、链上端点一致性、ulimit 与 403 门禁拦截自检
│   ├── day11_validator/
│   │   ├── camp_validator.py                 # Day 9（--score-only）/ Day 11（评分 + EMA + bt.SetWeights 提交上链）
│   │   └── uid_monitor.py                    # Day 11–13：链上元图轮询、Incentive 排名与淘汰风险监控
│   ├── day12_pm2/
│   │   └── ecosystem.config.js               # Day 12：PM2 多进程守护配置
│   └── day13_docker/
│       ├── Dockerfile                        # Day 13：矿工与监控容器镜像构建文件
│       ├── docker-compose.yml                # Day 13：热密钥只读挂载（:ro）与宿主机本地链连接编排
│       └── .dockerignore                     # Day 13：构建上下文安全隔离（排除私钥与本地缓存）
└── solutions/
    └── DAY10_MINER_FIXES.md                  # Day 10：camp_miner.py 两处代码缺陷修复参考解析（卡壳时查阅）
```

---

## 🛠️ 分步终端实操指南（Day 2 – Day 14）

> **前置约定**：以下所有命令均在项目根目录下执行，且每个新打开的终端窗口均需先激活虚拟环境：
> ```bash
> source .venv/bin/activate
> ```

### Day 2：创建命令行钱包并查询主网 64 号子网（第 02 课）

```bash
# 1. 创建教学钱包 camp（包含冷密钥与 default 热密钥）
btcli wallet create -w camp

# 2. 设置默认钱包与默认网络为主网 finney（配置保存在 ~/.bittensor/btcli.json）
btcli config set wallet camp
btcli config set network finney
btcli --version && btcli wallet list && btcli config get

# 3. 查询主网 64 号子网（Chutes）概况：观察 tempo (360)、burn（注册费）与席位数 (256/256)
btcli -n finney subnets show 64
```

### Day 3：查询 dTAO 子网注册销毁费与新手保护期（第 03 课）

```bash
# 1. 查询主网 64 号子网当前注册销毁价格（burn，注册即销毁，退网不退还）
btcli -n finney query burn --netuid 64

# 2. 查询新手保护期区块数（5000 个区块 × 12 秒/块 ≈ 16.7 小时）
btcli -n finney query immunity-period --netuid 64
```

### Day 4：拉取主网元图（Metagraph），区分矿工与验证者

```bash
# 查询 64 号子网实时元图：
# - validator_permit=True 且 dividends>0 的节点为活跃验证者
# - validator_permit=False 且 incentive>0 的节点为纯矿工（单周期 emission × 20 即为预估日产出）
btcli -n finney query metagraph --netuid 64
```

### Day 5：Yuma 共识防刷分模拟与 Commit-Reveal 查询

```bash
# 1. 运行 Yuma 共识模拟器：观察占 20% 质押的 Validator_A 给作弊小号 Miner_5 打 1.00 满分时，
#    如何被 κ=0.50 质押加权中位数截断为 0 分，且自身 vTrust 与分红大幅受损
python tools/day05_yuma_sim.py

# 2. 查询主网 64 号子网是否启用 commit-reveal 权重加密
btcli -n finney query commit-reveal-enabled --netuid 64
```

### Day 7：第二周本地链环境与 Docker 镜像一键自检

```bash
# 请先启动 Docker Desktop，再运行预检（--pull-image 会自动预拉取本地链镜像）
python tools/day07_check_env.py --pull-image
```

---

### Day 8：启动本地教学链、注册节点身份并分配验证许可（第 06 课）

```bash
# 1. 启动本地教学链容器（12 秒标准出块模式，端口 9944）
bash scripts/start_localnet.sh

# 2. 确认出块模式为 12 秒标准模式（is_fast_blocks 应返回 False）
btcli query is-fast-blocks --network local

# 3. 一键创建教学子网、配置超参数（tempo=10, max_allowed_validators=2）、注册 4 个节点并质押
bash scripts/setup_localnet.sh

# 4. 查看本地链教学子网元图（确认 UID 1 验证者持有 validator_permit，UID 2 为你的矿工）
export BT_WALLET_PATH="$PWD/.localnet/wallets" BT_NETWORK=local CAMP_NETUID="$(cat .localnet/netuid)"
btcli query metagraph --netuid "$CAMP_NETUID" --network local
```

### Day 9：启动矿工与陪练节点，复现首次评测现场（第 06 课）

```bash
# 1. 后台启动你的 2 号矿工（监听 8091 并发布链上端点）与两个陪练矿工（8092 / 8093）
python arena/day09_10_miner/camp_miner.py --serve -d
python arena/day09_10_miner/practice_bots.py -d

# 2. 确认链上元图已登记 UID 2、3、4 的 IP:Port 端点，随后运行验证者首次 3 轮评分
export BT_WALLET_PATH="$PWD/.localnet/wallets" BT_NETWORK=local CAMP_NETUID="$(cat .localnet/netuid)"
btcli query metagraph --netuid "$CAMP_NETUID" --network local
python arena/day11_validator/camp_validator.py --score-only --seed 12

# 3. 查看矿工报错日志（观察关卡 1“依据不在原文中”0 分与缺失字段简讯触发的 HTTP 500 崩溃）
cat .localnet/miner.log
```

### Day 10：矿工节点自检、403 门禁测试与代码缺陷修复（第 07 课）

```bash
# 1. 运行节点自检与无验证许可请求 403 拦截测试
python arena/day09_10_miner/diagnose_node.py --test-403

# 2. 打开 arena/day09_10_miner/camp_miner.py 修复 extract_field() 与 make_evidence() 两处缺陷
#    （若遇卡点可参考 solutions/DAY10_MINER_FIXES.md），修复后重启矿工：
python arena/day09_10_miner/camp_miner.py -d

# 3. 在相同题库种子（--seed 12）下复测，确认你的矿工三轮全拿 0.997+ 分并反超夺冠
rm -f .localnet/validator_scores.json
python arena/day11_validator/camp_validator.py --score-only --seed 12
```

### Day 11：验证者提交权重上链、时间锁解密与激励结算监控（第 08 课）

```bash
# 1. 正式运行验证者（发题 -> 评分 -> 更新 EMA -> 调用 bt.SetWeights 提交权重上链）
python arena/day11_validator/camp_validator.py --seed 12

# 2. 提交后立即读取链上权重（因处于 Commit-Reveal 加密期，此时返回空字典 {}）
python arena/day11_validator/camp_validator.py --show-weights

# 3. 等待约 1.5–2 分钟（跨过 Reveal 解密与 Tempo 结算块）后再次查询生效权重与矿工激励排名
python arena/day11_validator/camp_validator.py --show-weights
python arena/day11_validator/uid_monitor.py --rounds 3 --interval 12
```

### Day 12：PM2 进程守护、崩溃自愈与日志轮转

```bash
# 1. 使用 PM2 统一接管矿工、陪练与监控进程
pm2 start arena/day12_pm2/ecosystem.config.js
pm2 list

# 2. 模拟矿工进程意外崩溃 (kill -9)，观察 PM2 自动拉起（重启次数 ↺ +1）
kill -9 $(pm2 pid camp-miner)
sleep 2 && pm2 list
```

### Day 13：Docker Compose 容器化部署与热密钥只读挂载

```bash
# 1. 停止宿主机上的矿工进程，将 8091 端口腾给 Docker 容器（保留宿主机陪练矿工）
pm2 delete camp-miner camp-bots camp-monitor 2>/dev/null || true
python arena/day09_10_miner/practice_bots.py -d

# 2. 构建并启动容器化矿工（热密钥目录以 :ro 只读挂载，完全隔离冷密钥）
docker compose -f arena/day13_docker/docker-compose.yml up -d --build
docker compose -f arena/day13_docker/docker-compose.yml ps

# 3. 运行验证者评分，确认容器内矿工正常响应拿分
python arena/day11_validator/camp_validator.py --score-only --seed 12 --rounds 1
```

---

## ❓ 常见问题与排障速查（FAQ）

| 现象 / 报错 | 原因分析 | 解决方案 |
| :--- | :--- | :--- |
| **VS Code 右上角 `Select Kernel` 里看不到 `.venv`** | ① 直接双击打开了单个 `.ipynb` 文件（无工作区目录，VS Code 跳过相对路径 `.venv` 扫描）；<br>② 文件夹处于 **Restricted Mode（未信任工作区）**，VS Code 自动禁用了 Python 环境扩展。 | 1. 用菜单 **`File -> Open Folder...`** 打开整个项目文件夹；<br>2. 点击弹窗或左下角状态栏的 **`Trust`** 信任文件夹；<br>3. 再点 `Select Kernel -> Python Environments...` 即可选到 `.venv`。 |
| **`btcli --version` 显示 `9.x` 或报 `No such option: --wallet.name`** | 环境中误装了旧版独立包 `bittensor-cli`（最高仅 `9.23.2`）。 | 在激活的 `.venv` 中执行：<br>`pip uninstall -y bittensor-cli bittensor-wallet && pip install -U "bittensor>=11.3.0"` |
| **矿工 `--serve` 发布端点报 `InvalidIpAddress`** | Subtensor 链拒绝登记 `127.0.0.1` 回环地址，或开启代理软件 TUN 模式产生了 `198.18.x.x` 虚拟网卡地址。 | `arena/common/chain.py` 的 `lan_ip()` 已自动过滤 `198.18.x.x`；若仍失败，可用 `--ip <你的局域网IP>` 手动指定。 |
| **Day 11 提交权重后立即 `--show-weights` 显示暂无 `{}`** | 子网默认启用了 `Commit-Reveal` 时间锁加密，当期提交的权重处于加密状态。 | 属于正常防抄权重机制。等待约 1 个 Reveal 周期（本地链约 1–2 分钟）后再次查询即可看到解密后的权重。 |
| **Day 8 运行 `setup_localnet.sh` 报 `AdminActionProhibitedDuringWeightsWindow`** | 本地链区块恰好处于 Tempo 末尾的管理员冻结窗口期。 | 脚本已内置 `sudo_set_admin_freeze_window(0)` 自动解除限制，重新执行一次 `bash scripts/setup_localnet.sh` 即可。 |

---

## 🔗 官方参考资料与社区

* **Bittensor v11 官方文档**：[https://www.bittensor.com/docs](https://www.bittensor.com/docs)
* **Bittensor v11 迁移指南（Migration Guide）**：[https://www.bittensor.com/docs/migration](https://www.bittensor.com/docs/migration)
* **Taostats 链上浏览器与子网列表**：[https://taostats.io/subnets](https://taostats.io/subnets)
* **Dynamic TAO (dTAO) 与 Yuma 共识指南**：[https://docs.learnbittensor.org](https://docs.learnbittensor.org)
* **HackQuest × Bittensor 中文社区**：[点击加入社区交流与答疑](https://www.hackquest.io/zh-cn/organization/Bittensor/community-organizer/Bittensor-中文社区)
