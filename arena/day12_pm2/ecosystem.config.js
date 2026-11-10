/**
 * 第 12 天配套配置：PM2 进程守护配置 ecosystem.config.js
 * 用途：同时守护共学营矿工（camp-miner）、陪练矿工（camp-bots）与链上监控（camp-monitor）
 *
 * 常用命令（在 camp-kit 根目录执行）：
 * 1. 启动守护：pm2 start arena/day12_pm2/ecosystem.config.js
 * 2. 查看状态：pm2 list   |   查看日志：pm2 logs camp-miner --lines 20
 * 3. 配置日志轮转（单文件最大 50MB，最多保留 10 个历史文件）：
 *    pm2 install pm2-logrotate
 *    pm2 set pm2-logrotate:max_size 50M
 *    pm2 set pm2-logrotate:retain 10
 *    pm2 set pm2-logrotate:compress true
 * 4. 模拟崩溃自愈：kill -9 <camp-miner 的 pid> && sleep 2 && pm2 list
 */

const fs = require("fs");
const path = require("path");

const rootDir = path.resolve(__dirname, "../..");
const venvPython = path.join(rootDir, ".venv", "bin", "python");
const pythonBin = fs.existsSync(venvPython) ? venvPython : "python3";

module.exports = {
  apps: [
    {
      name: "camp-miner",
      cwd: rootDir,
      script: "arena/day09_10_miner/camp_miner.py",
      interpreter: pythonBin,
      args: "--port 8091",
      autorestart: true,
      watch: false,
      max_memory_restart: "1G",
      restart_delay: 2000,
      env: {
        PYTHONUNBUFFERED: "1",
        BT_NETWORK: "local"
      }
    },
    {
      name: "camp-bots",
      cwd: rootDir,
      script: "arena/day09_10_miner/practice_bots.py",
      interpreter: pythonBin,
      autorestart: true,
      watch: false,
      max_memory_restart: "1G",
      restart_delay: 2000,
      env: {
        PYTHONUNBUFFERED: "1",
        BT_NETWORK: "local"
      }
    },
    {
      name: "camp-monitor",
      cwd: rootDir,
      script: "arena/day11_validator/uid_monitor.py",
      interpreter: pythonBin,
      args: "--rounds 0 --interval 12",
      autorestart: true,
      watch: false,
      max_memory_restart: "500M",
      restart_delay: 3000,
      env: {
        PYTHONUNBUFFERED: "1",
        BT_NETWORK: "local"
      }
    }
  ]
};
