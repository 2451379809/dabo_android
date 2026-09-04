#!/usr/bin/env python3
"""
SO Unpacking Tool — dabo_android
Frida SO dump 包装器: 加载 scripts/unpack/frida/dump_so.js 导出内存中的SO，
退出后自动从 /data/local/tmp 拉取 *_dumped_*.so 并校验 ELF 魔数，
若本机可找到 SoFixer（SOFIXER_PATH）则自动做 ELF 修复。

用法:
    python dump_so.py com.example.app
    python dump_so.py com.example.app --output ./dumped_so
    python dump_so.py com.example.app --attach          # 附加到已运行的应用
    python dump_so.py com.example.app --no-pull         # 只跑frida, 手动拉取

流程:
    1. 环境检查 (adb / frida 由 toolenv 自动探测)
    2. frida 加载 dump_so.js (spawn 或 attach), 在应用内操作触发目标SO加载
    3. frida 退出后自动 adb pull /data/local/tmp/*_dumped_*.so
    4. ELF 魔数校验 (\x7fELF), 可选 SoFixer 修复
"""

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "lib"))
import toolenv  # noqa: E402

FRIDA_SCRIPT = SCRIPT_DIR / "frida" / "dump_so.js"
REMOTE_DIR = "/data/local/tmp"


def check_env():
    adb = toolenv.resolve("adb")
    frida = toolenv.resolve("frida")
    missing = [k for k in (adb, frida) if not k]
    if missing:
        print("[✗] 环境不完整，运行探测报告: python %s" % (SCRIPT_DIR.parent / "lib" / "toolenv.py"))
        toolenv.require("adb" if not adb else "frida")
    return adb, frida


def run_frida(frida, package, attach):
    cmd = [frida, "-U"]
    cmd += [package] if attach else ["-f", package]
    cmd += ["-l", str(FRIDA_SCRIPT)]

    print("[*] Command: " + " ".join(cmd))
    print("[*] 应用启动后请操作触发目标SO加载; dump_so.js 会自动导出到 " + REMOTE_DIR)
    print("[*] 完成后在 frida 会话中按 Ctrl+D (或输入 exit) 退出\n")
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n[*] 已中断 frida 会话")


def pull_dumped(adb, output, so_filter):
    """从设备拉取 *_dumped_*.so 文件"""
    out_dir = Path(output)
    out_dir.mkdir(parents=True, exist_ok=True)

    result = subprocess.run([adb, "shell", "ls", REMOTE_DIR],
                            capture_output=True, text=True, timeout=15)
    names = [n.strip() for n in result.stdout.split()
             if "_dumped_" in n and n.strip().endswith(".so")]
    if so_filter:
        names = [n for n in names if so_filter.lower() in n.lower()]

    if not names:
        print("[!] 设备上没有找到 *_dumped_*.so（可能尚未触发SO加载，或已被清理）")
        print("    手动查看: adb shell ls " + REMOTE_DIR)
        return []

    pulled = []
    for name in names:
        target = out_dir / name
        r = subprocess.run([adb, "pull", REMOTE_DIR + "/" + name, str(target)],
                           capture_output=True, text=True, timeout=60)
        if target.exists():
            pulled.append(target)
            print("[✓] 已拉取: " + str(target))
        else:
            print("[✗] 拉取失败: " + name + " " + (r.stderr or "").strip()[:80])

    return pulled


def validate_elf(path):
    try:
        with open(path, "rb") as f:
            return f.read(4) == b"\x7fELF"
    except OSError:
        return False


def try_sofixer(files):
    sof = toolenv.resolve("sofixer")
    if not sof:
        print("[!] 未找到 SoFixer（可选）。dump 出的SO如无法在IDA加载，"
              "设置 SOFIXER_PATH 后重跑可自动修复")
        return files
    fixed = []
    for p in files:
        out = p.with_name(p.stem + "_fix.so")
        r = subprocess.run([sof, "-s", str(p), "-o", str(out)],
                           capture_output=True, text=True, timeout=120)
        if out.exists():
            print("[✓] SoFixer 修复: " + str(out))
            fixed.append(out)
        else:
            print("[!] SoFixer 修复失败: " + p.name + " " + (r.stderr or r.stdout or "").strip()[:80])
            fixed.append(p)
    return fixed


def main():
    parser = argparse.ArgumentParser(
        description="SO Unpacking Tool (frida dump_so.js wrapper)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("流程:")[0])
    parser.add_argument("package", help="目标包名, 如 com.example.app")
    parser.add_argument("--so", default=None, help="只拉取名称包含该子串的SO (如 libgame)")
    parser.add_argument("-o", "--output", default="./dumped_so", help="输出目录 (默认 ./dumped_so)")
    parser.add_argument("-a", "--attach", action="store_true", help="attach模式（应用需已运行）")
    parser.add_argument("--no-pull", action="store_true", help="只运行frida，不自动拉取")
    parser.add_argument("--skip-check", action="store_true", help="跳过环境检查")
    args = parser.parse_args()

    print("=" * 60)
    print("SO Unpacking Tool")
    print("=" * 60)

    if not FRIDA_SCRIPT.exists():
        print("[✗] 缺少 frida 脚本: " + str(FRIDA_SCRIPT))
        sys.exit(1)

    if not args.skip_check:
        adb, frida = check_env()
    else:
        adb, frida = toolenv.resolve("adb"), toolenv.resolve("frida")

    run_frida(frida, args.package, args.attach)

    if args.no_pull:
        print("\n[*] 手动拉取: adb pull " + REMOTE_DIR + "/*_dumped_*.so ./")
        sys.exit(0)

    print()
    print("[*] 拉取 dump 结果...")
    files = pull_dumped(adb, args.output, args.so)
    if not files:
        sys.exit(1)

    print()
    print("[*] ELF 校验...")
    ok = 0
    for p in files:
        valid = validate_elf(p)
        print("  [%s] %s" % ("✓" if valid else "✗", p.name))
        ok += valid

    print()
    files = try_sofixer(files)

    print("[*] 完成: %d 个文件, %d 个ELF校验通过, 输出目录: %s" % (len(files), ok, args.output))
    print("[*] 下一步: 用 IDA/Ghidra 打开 *_fix.so 分析; 模块基址见 frida 会话日志")


if __name__ == "__main__":
    main()
