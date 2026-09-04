#!/usr/bin/env python3
"""
dabo_android - Android Reverse Engineering Toolkit
Main entry point for interactive CLI

所有脚本路径基于本文件所在目录解析（可在任意工作目录运行）;
外部工具（adb/frida/...）由 scripts/lib/toolenv.py 自动探测。
"""

import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
SCRIPTS = SKILL_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS / "lib"))
sys.path.insert(0, str(SCRIPTS))

import toolenv  # noqa: E402

PY = sys.executable


def print_banner():
    banner = r"""
    ____        __                                __           _     __
   / __ \____ _/ /_  ____        ____ _____  ____/ /________  (_)___/ /
  / / / / __ `/ __ \/ __ \______/ __ `/ __ \/ __  / ___/ __ \/ / __  /
 / /_/ / /_/ / /_/ / /_/ /_____/ /_/ / / / / /_/ / /  / /_/ / / /_/ /
/_____/\__,_/_.___/\____/      \__,_/_/ /_/\__,_/_/   \____/_/\__,_/

    Android Reverse Engineering Toolkit v2.2
"""
    print(banner)
    print("=" * 70)
    print()


def run_py(script_rel, *args):
    """以当前 Python 运行 skill 内脚本（绝对路径，不依赖 CWD）"""
    script = SCRIPTS / script_rel
    if not script.exists():
        print(f"[✗] Script not found: {script}")
        return
    subprocess.run([PY, str(script), *args])


def run_frida(script_rel, package, attach=False):
    """加载 skill 内 frida 脚本（spawn/attach）。frida>=16 spawn 后自动 resume。"""
    frida = toolenv.resolve("frida")
    if not frida:
        toolenv.require("frida")
        return
    script = SCRIPTS / script_rel
    if not script.exists():
        print(f"[✗] Script not found: {script}")
        return
    cmd = [frida, "-U"] + ([package] if attach else ["-f", package]) + ["-l", str(script)]
    print(f"[*] Command: {' '.join(cmd)}\n")
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n[*] Interrupted by user")


def print_menu():
    menu = """
Available Functions:

  1. Quick APK Analysis        - Extract APK info, permissions, components
  2. DEX Unpacking             - Dump encrypted DEX files
  3. SO Unpacking              - Dump and pull native libraries
  4. SSL Pinning Bypass        - Disable certificate validation
  5. Anti-Detection Bypass     - Defeat root/emulator/Frida checks
  6. Crypto Algorithm Hook     - Capture encryption keys and algorithms
  7. Generate Frida Script     - Create custom hook scripts
  8. Environment Check         - Validate tools and connections

  0. Exit
    """
    print(menu)


def check_environment():
    print("[*] Checking environment...")
    adb = toolenv.resolve("adb")
    frida = toolenv.resolve("frida")
    print(f"  adb:   {adb or '-- 未找到 (menu 8 查看提示) --'}")
    print(f"  frida: {frida or '-- 未找到 (menu 8 查看提示) --'}")


def quick_analyze():
    print("\n" + "=" * 70 + "\nQuick APK Analysis\n" + "=" * 70 + "\n")
    package = input("Enter package name or APK path: ").strip()
    if not package:
        print("[✗] Package name required")
        return
    run_py(Path("analyze") / "quick_analyze_apk.py", package)


def dex_unpack():
    print("\n" + "=" * 70 + "\nDEX Unpacking\n" + "=" * 70 + "\n")
    package = input("Enter package name: ").strip()
    if not package:
        print("[✗] Package name required")
        return
    print("\nDump methods:")
    print("  1. Memory search (default, works for most first-gen packers)")
    print("  2. ClassLoader hook (requires app initialization)")
    choice = input("\nSelect method (1-2, default=1): ").strip() or "1"
    method = {"1": "memory", "2": "classloader"}.get(choice, "memory")
    output = input("Output directory (default=./dumped_dex): ").strip() or "./dumped_dex"
    run_py(Path("unpack") / "dump_dex.py", package, "--method", method, "--output", output)


def so_unpack():
    print("\n" + "=" * 70 + "\nSO Unpacking\n" + "=" * 70 + "\n")
    package = input("Enter package name: ").strip()
    if not package:
        print("[✗] Package name required")
        return
    so_name = input("SO name filter (e.g. libgame.so, empty=all): ").strip()
    output = input("Output directory (default=./dumped_so): ").strip() or "./dumped_so"
    args = [package, "--output", output]
    if so_name:
        args += ["--so", so_name]
    run_py(Path("unpack") / "dump_so.py", *args)


def ssl_unpin():
    print("\n" + "=" * 70 + "\nSSL Pinning Bypass\n" + "=" * 70 + "\n")
    package = input("Enter package name: ").strip()
    if not package:
        print("[✗] Package name required")
        return
    print("[*] App will start with SSL pinning bypassed")
    print("[*] Check your proxy (Fiddler/Charles/mitmproxy) for decrypted traffic\n")
    run_frida(Path("hook") / "frida_universal_ssl_unpin.js", package)


def anti_detection():
    print("\n" + "=" * 70 + "\nAnti-Detection Bypass\n" + "=" * 70 + "\n")
    package = input("Enter package name: ").strip()
    if not package:
        print("[✗] Package name required")
        return
    print("[*] Bypasses: root detection / frida detection / emulator / anti-debug\n")
    run_frida(Path("hook") / "frida_anti_detection.js", package)


def crypto_hook():
    print("\n" + "=" * 70 + "\nCrypto Algorithm Hook\n" + "=" * 70 + "\n")
    package = input("Enter package name: ").strip()
    if not package:
        print("[✗] Package name required")
        return
    print("[*] Captures: Cipher / MessageDigest / Mac / Base64 with keys, IVs, IO\n")
    run_frida(Path("hook") / "frida_crypto_hook.js", package)


def generate_script():
    print("\n" + "=" * 70 + "\nGenerate Frida Script\n" + "=" * 70 + "\n")
    print("Script templates:")
    print("  1. Hook class methods       (hook-class)")
    print("  2. Hook specific method     (hook-method)")
    print("  3. SSL pinning bypass       (ssl)")
    print("  4. Anti-detection           (anti-detect)")
    print("  5. Trace function calls     (trace)")
    choice = input("\nSelect template (1-5): ").strip()
    templates = {"1": "hook-class", "2": "hook-method", "3": "ssl", "4": "anti-detect", "5": "trace"}
    template = templates.get(choice)
    if not template:
        print("[✗] Invalid choice")
        return
    class_name = input("Class name (e.g. com.example.MainActivity): ").strip()
    output = input("Output file (default=generated_script.js): ").strip() or "generated_script.js"
    args = ["--type", template, "--class", class_name, "--output", output]
    run_py(Path("generate") / "frida_script_generator.py", *args)


def run_env_check():
    print("\n" + "=" * 70 + "\nEnvironment Check\n" + "=" * 70 + "\n")
    run_py(Path("check") / "check_android_env.py")


def main():
    print_banner()
    check_environment()
    while True:
        print_menu()
        choice = input("Select function (0-8): ").strip()
        if choice == "0":
            print("\n[*] Exiting...")
            sys.exit(0)
        elif choice == "1":
            quick_analyze()
        elif choice == "2":
            dex_unpack()
        elif choice == "3":
            so_unpack()
        elif choice == "4":
            ssl_unpin()
        elif choice == "5":
            anti_detection()
        elif choice == "6":
            crypto_hook()
        elif choice == "7":
            generate_script()
        elif choice == "8":
            run_env_check()
        else:
            print("[✗] Invalid choice")

        print("\n" + "=" * 70 + "\n")
        input("Press Enter to continue...")
        print("\n" * 2)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[*] Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n[✗] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
