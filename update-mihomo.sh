#!/bin/bash
# meridian-data 自动更新脚本:抓取 VPNGate → 存活验证 → 更新 mihomo
set -euo pipefail
cd /root/meridian-data

LOG="/root/meridian-data/update.log"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ===== 开始更新 =====" >> "$LOG"

# 1. 抓取(300 请求,够用)
TOTAL_REQUESTS=300 OUTPUT_DIR=/root/meridian-data/public STATE_PATH=/root/meridian-data/public/state/servers.json timeout 300 ./vpn-meridian >> "$LOG" 2>&1 || { echo "抓取失败" >> "$LOG"; exit 1; }

# 2. MaxMind 增强 + mihomo 生成
./vpn-meridian enrich --input public/json/data.json --output public/json/data.maxmind.json --mihomo-output public/mihomo_openvpn.yaml --maxmind-dir maxmind >> "$LOG" 2>&1

# 3. 存活验证(3s 超时,最多 30 个)
./testcheck --tested-data public/json/data.maxmind.json --alive-mihomo public/mihomo_tested_openvpn.yaml --results-json public/json/test_results.json --max-alive 30 --timeout 3 --attempts 1 >> "$LOG" 2>&1 || true

# 4. 生成新 mihomo 配置
NUM_LISTENERS=30 python3 gen_mihomo.py >> "$LOG" 2>&1

# 5. 语法检查
if ! mihomo -t -f /tmp/mihomo_new.yaml >> "$LOG" 2>&1; then
  echo "语法检查失败,跳过更新" >> "$LOG"
  exit 1
fi

# 6. 合并 + 重启 mihomo
python3 merge_mihomo.py >> "$LOG" 2>&1
systemctl restart mihomo
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 更新完成, mihomo 已重启" >> "$LOG"
