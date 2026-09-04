"""mitm_run_full.py — DumpMaster驱动mitm全量抓取 (通用版)

链路: 模拟器 → adb reverse 127.0.0.1:10814 → 本mitm → upstream xray HTTP入站:10812 → 出境
注意: mitmproxy 12 不支持socks5上游, 中间必须有一层HTTP代理(xray/v2ray HTTP入站)。

配置: 按需改 LISTEN_PORT / UPSTREAM, addon路径与 mitm_full_capture.py 同目录。
用法: python mitm_run_full.py   (后台长跑, jsonl落盘见addon内路径)
"""
import asyncio
import os
import sys

from mitmproxy import options
from mitmproxy.tools.dump import DumpMaster

LISTEN_PORT = 10814
UPSTREAM = "http://127.0.0.1:10812"  # xray/v2ray HTTP入站; 置None则直连出境

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def main():
    mode = [f"upstream:{UPSTREAM}"] if UPSTREAM else ["regular"]
    opts = options.Options(
        listen_host="0.0.0.0", listen_port=LISTEN_PORT,
        mode=mode, ssl_insecure=True,
    )
    master = DumpMaster(opts)
    master.options.flow_detail = 0
    import mitm_full_capture
    master.addons.add(mitm_full_capture)
    print(f"mitm full-capture ready on 0.0.0.0:{LISTEN_PORT} -> {UPSTREAM or 'direct'}", flush=True)
    await master.run()


if __name__ == "__main__":
    asyncio.run(main())
