#!/usr/bin/env python3
"""从 meridian-data 结果生成 mihomo 配置:筛存活节点,前 N 个接入 listeners"""
import json
import os
import re
import sys

# 配置
RESULTS = 'public/json/test_results.json'
FULL_MIHOMO = 'public/mihomo_openvpn.yaml'     # meridian-data 完整生成(格式正确)
OUT_MIHOMO = '/tmp/mihomo_new.yaml'            # 输出
NUM_LISTENERS = int(os.environ.get('NUM_LISTENERS', '30'))  # SOCKS5 端口数

# 1. 读存活节点
with open(RESULTS) as f:
    results = json.load(f)['results']

alive = [r['name'] for r in results if r.get('alive')]
print(f"存活节点: {len(alive)} 个")
print("存活列表:", alive[:15], "..." if len(alive) > 15 else "")

if len(alive) < NUM_LISTENERS:
    print(f"警告: 存活节点({len(alive)})少于所需端口数({NUM_LISTENERS})")

# 2. 从完整 mihomo YAML 提取节点(按 name)
# 用简单的块解析:每个 proxy 是 "  - name: ..." 开始的块
with open(FULL_MIHOMO) as f:
    content = f.read()

# 按 "  - name:" 分割
blocks = re.split(r'(?=^  - name:)', content, flags=re.M)
proxies = []
for b in blocks:
    m = re.match(r'  - name: "([^"]+)"', b)
    if m:
        proxies.append((m.group(1), b))

print(f"完整 YAML 节点: {len(proxies)} 个")

# 3. 选前 N 个存活节点
alive_set = set(alive)
chosen = [(name, block) for name, block in proxies if name in alive_set][:NUM_LISTENERS]
print(f"选用 {len(chosen)} 个节点")

# 4. 生成新配置:proxies + listeners
out = ["proxies:"]
for name, block in chosen:
    out.append(block.rstrip('\n'))

out.append("")
out.append("listeners:")
for i, (name, _) in enumerate(chosen, 1):
    out.append(f"  - name: socks-{i}")
    out.append(f"    type: socks")
    out.append(f"    port: {7890 + i}")   # 7891-7900,保持与 opencode2api 兼容
    out.append(f"    listen: 127.0.0.1")
    out.append(f"    proxy: \"{name}\"")
    out.append(f"    udp: false")

with open(OUT_MIHOMO, 'w') as f:
    f.write('\n'.join(out) + '\n')

print(f"已生成: {OUT_MIHOMO}")
print(f"监听端口: 7891-{7890 + len(chosen)}")
