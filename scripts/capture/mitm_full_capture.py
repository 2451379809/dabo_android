"""mitm_full_capture.py — mitmproxy全量抓取addon (通用版)

用法: 由 mitm_run_full.py 加载; 也可 mitmdump -s mitm_full_capture.py
配置: 修改下方 OUT_DIR/INTEREST 常量

记录内容:
- 命中INTEREST关键词的请求: 完整headers(含cookie) + body前600B
- 命中INTEREST关键词的响应: status/ct/len/body前1KB
- 所有响应的Set-Cookie: 汇总到独立jsonl (逆向设备级cookie必备)
"""
import json
import os
import time

# 输出目录: 默认落在脚本旁的 capture_out/，可按需修改
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "capture_out")
os.makedirs(OUT_DIR, exist_ok=True)
LOG = os.path.join(OUT_DIR, "full_capture.jsonl")
CJ = os.path.join(OUT_DIR, "setcookies.jsonl")
INTEREST = ("aweme", "detail", "feed", "passport", "login", "token", "user", "search")


class FullCapture:
    def _log(self, path, obj):
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    def request(self, flow):
        p = flow.request.path
        if any(k in p for k in INTEREST):
            try:
                body = flow.request.raw_content
                body_s = body[:600].decode("utf-8", "replace") if body else ""
            except Exception:
                body_s = ""
            self._log(LOG, {
                "t": time.time(), "kind": "req",
                "method": flow.request.method,
                "host": flow.request.host, "path": p,
                "headers": dict(flow.request.headers), "body": body_s,
            })

    def response(self, flow):
        try:
            sc = flow.response.headers.get_all("set-cookie")
        except Exception:
            sc = []
        if sc:
            self._log(CJ, {"t": time.time(), "host": flow.request.host,
                           "path": flow.request.path[:80],
                           "set_cookie": [str(x)[:300] for x in sc]})
        p = flow.request.path
        if any(k in p for k in INTEREST):
            try:
                body = flow.response.raw_content or b""
                body_s = body[:1000].decode("utf-8", "replace")
            except Exception:
                body_s = ""
            self._log(LOG, {
                "t": time.time(), "kind": "resp",
                "method": flow.request.method,
                "host": flow.request.host, "path": p[:150],
                "status": flow.response.status_code,
                "ct": flow.response.headers.get("content-type", ""),
                "len": len(flow.response.raw_content or b""),
                "body": body_s,
            })


addons = [FullCapture()]
