#!/usr/bin/env python3
"""
Android Reverse Engineering Environment Checker
基于 toolenv 自动探测（零配置），验证工具与设备连接状态。

用法:
    python check_android_env.py
    python check_android_env.py --verbose   # 显示每个工具的安装提示
"""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
import toolenv  # noqa: E402


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")


def print_check(name, status, message=""):
    symbol = f"{Colors.GREEN}✓{Colors.RESET}" if status else f"{Colors.RED}✗{Colors.RESET}"
    msg_part = f": {message}" if message else ""
    print(f"[{symbol}] {name}{msg_part}")


def run_cmd(cmd, timeout=10):
    """运行命令，返回 (ok, 首行输出)"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        output = (result.stdout.strip() or result.stderr.strip())
        first_line = output.split('\n')[0] if output else "OK"
        return result.returncode == 0, first_line
    except FileNotFoundError:
        return False, "Not found"
    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)[:50]


def check_adb():
    """ADB 与设备连接"""
    print_header("ADB & Device Connection")
    results = {}
    adb = toolenv.resolve("adb")
    print_check("ADB", bool(adb), adb or "未找到")
    results['adb'] = bool(adb)
    if not adb:
        results['device'] = False
        results['root'] = False
        return results

    ok, ver = run_cmd([adb, "version"])
    print_check("ADB version", ok, ver)
    results['adb_version'] = ok

    result = subprocess.run([adb, "devices"], capture_output=True, text=True, timeout=10)
    devices = [line for line in result.stdout.split('\n') if '\tdevice' in line]
    print_check("Device connected", bool(devices), f"{len(devices)} device(s)")
    results['device'] = bool(devices)

    if devices:
        r = subprocess.run([adb, "shell", "su", "-c", "id"],
                           capture_output=True, text=True, timeout=8)
        rooted = "uid=0" in r.stdout
        print_check("Root access", rooted, "uid=0(root)" if rooted else "No root / denied")
        results['root'] = rooted
    else:
        results['root'] = False
    return results


def check_frida():
    """Frida 客户端与设备端 server"""
    print_header("Frida Environment")
    results = {}
    frida = toolenv.resolve("frida")
    frida_ps = toolenv.resolve("frida-ps")
    print_check("Frida client", bool(frida), frida or "未找到")
    results['frida_client'] = bool(frida)

    if frida_ps:
        r = subprocess.run([frida_ps, "-U"], capture_output=True, text=True, timeout=15)
        if r.returncode == 0:
            n = len([l for l in r.stdout.split('\n') if l.strip() and not l.startswith('PID')])
            print_check("Frida server (device)", True, f"{n} processes listed")
            results['frida_server'] = True
        else:
            print_check("Frida server (device)", False,
                        "无法连接（设备未连接或 frida-server 未运行）")
            results['frida_server'] = False
    else:
        print_check("Frida server (device)", False, "frida-ps 不可用")
        results['frida_server'] = False

    servers = toolenv.frida_servers()
    if servers:
        for s in servers:
            print_check("frida-server binary", True, s)
    results['frida_servers'] = len(servers)
    return results


def check_java():
    print_header("Java Environment")
    java = toolenv.resolve("java")
    ok, ver = run_cmd([java, "-version"]) if java else (False, "未找到")
    print_check("Java", ok, f"{java} — {ver}" if java else ver)
    return {'java': ok}


def check_analysis_tools():
    """静态分析工具（jadx 必需，其余可选）"""
    print_header("Analysis Tools")
    results = {}
    jadx = toolenv.resolve_cmd("jadx")
    print_check("jadx", bool(jadx), " ".join(jadx) if jadx else "未找到")
    results['jadx'] = bool(jadx)

    apktool = toolenv.resolve_cmd("apktool")
    print_check("apktool", bool(apktool), " ".join(apktool) if apktool else "未找到")
    results['apktool'] = bool(apktool)

    for jar in ("smali", "baksmali", "d8"):
        p = toolenv.resolve_jar(jar)
        print_check(f"{jar} (optional)", bool(p), p or "未找到")
        results[jar] = bool(p)

    sof = toolenv.resolve("sofixer")
    print_check("SoFixer (optional)", bool(sof), sof or "未找到")
    results['sofixer'] = bool(sof)
    return results


def check_python_packages():
    print_header("Python Packages")
    results = {}
    required = ["frida", "frida-tools"]
    optional = ["frida-dexdump", "mitmproxy", "androguard", "pycryptodome", "requests"]
    for pkg in required + optional:
        ok, ver = run_cmd([sys.executable, "-m", "pip", "show", pkg], timeout=8)
        version = ""
        if ok:
            # pip show 的 Name: 行之后取 Version
            r = subprocess.run([sys.executable, "-m", "pip", "show", pkg],
                               capture_output=True, text=True, timeout=8)
            for line in r.stdout.split('\n'):
                if line.startswith('Version:'):
                    version = line.split(':', 1)[1].strip()
                    break
        tag = "" if pkg in required else " (optional)"
        print_check(pkg + tag, ok, f"v{version}" if version else ("OK" if ok else "Not installed"))
        results[pkg] = ok
    return results


def check_optional_disasm():
    print_header("Disassemblers (Optional)")
    results = {}
    import shutil
    ida = shutil.which("ida64") or shutil.which("ida")
    ghidra = __import__("os").environ.get("GHIDRA_INSTALL_DIR")
    print_check("IDA Pro", bool(ida), ida or "未找到（可选，用 Ghidra 替代）")
    print_check("Ghidra", bool(ghidra), ghidra or "未设置 GHIDRA_INSTALL_DIR（可选）")
    results['ida'] = bool(ida)
    results['ghidra'] = bool(ghidra)
    return results


def check_xposed():
    """Xposed/LSPosed 框架探测（可选路线：未安装则 Xposed 系策略全部不可用）"""
    print_header("Xposed / LSPosed (Optional)")
    results = {}
    adb = toolenv.resolve("adb")
    if not adb:
        print_check("framework probe", False, "adb 不可用，跳过")
        results['xposed_framework'] = False
        return results

    found = None
    # root 下查 LSPosed 数据目录（最可靠；Manager 可能被隐藏）
    try:
        r = subprocess.run([adb, "shell", "su", "-c", "ls /data/adb/lspd"],
                           capture_output=True, text=True, timeout=8)
        if r.returncode == 0 and r.stdout.strip():
            found = "/data/adb/lspd"
            print_check("LSPosed framework", True, "/data/adb/lspd (root)")
    except Exception:
        pass

    managers = [
        ("org.lsposed.manager", "LSPosed manager"),
        ("org.meowcat.edxposed.manager", "EdXposed manager"),
        ("de.robv.android.xposed.installer", "Xposed manager (legacy)"),
    ]
    for pkg, label in managers:
        try:
            r = subprocess.run([adb, "shell", "pm", "path", pkg],
                               capture_output=True, text=True, timeout=8)
            has = "package:" in (r.stdout or "")
        except Exception:
            has = False
        note = "未安装" if not has else pkg
        if not has and "LSPosed" in label and not found:
            note += "（隐藏模式下 pm 探测不到，以 root 目录探测为准）"
        print_check(label, has, note)
        if has:
            found = found or pkg

    results['xposed_framework'] = bool(found)
    if not found:
        print(f"{Colors.YELLOW}    -> 未检测到 Xposed 系框架：Xposed/LSPosed 路线不可用，请走 Frida 路线{Colors.RESET}")
        print("    （该路线需设备预装框架，且模块/作用域变更后重启生效）")
    return results


def main():
    verbose = "--verbose" in sys.argv
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("=" * 60)
    print("Android Reverse Engineering Environment Check")
    print("(tools are auto-discovered via toolenv: PATH -> common locations)")
    print("=" * 60)
    print(Colors.RESET)

    all_results = {}
    all_results['adb'] = check_adb()
    all_results['frida'] = check_frida()
    all_results['java'] = check_java()
    all_results['tools'] = check_analysis_tools()
    all_results['python'] = check_python_packages()
    all_results['disasm'] = check_optional_disasm()
    all_results['xposed'] = check_xposed()

    print_header("Summary")
    critical = [
        ('adb', ['adb', 'device']),
        ('frida', ['frida_client', 'frida_server']),
        ('java', ['java']),
        ('tools', ['jadx', 'apktool']),
    ]
    failures = []
    total = passed = 0
    for cat, keys in critical:
        for k in keys:
            v = all_results.get(cat, {}).get(k)
            if v is None:
                continue
            total += 1
            passed += bool(v)
            if not v:
                failures.append(f"{cat}.{k}")

    print(f"Critical checks: {passed}/{total} passed")
    if failures:
        print(f"\n{Colors.RED}Critical failures:{Colors.RESET}")
        for f in failures:
            print(f"  - {f}")
        if verbose:
            print()
            toolenv.main() if hasattr(toolenv, "main") else None
        print(f"\n{Colors.YELLOW}安装提示:{Colors.RESET}")
        for f in failures:
            kind = f.split('.')[-1]
            kind = {'device': 'adb', 'frida_client': 'frida',
                    'frida_server': 'frida', 'java': 'java'}.get(kind, kind)
            hint = toolenv.INSTALL_HINTS.get(kind)
            if hint:
                print(f"  [{kind}] " + hint.replace("\n", "\n         "))
        sys.exit(1)
    else:
        print(f"{Colors.GREEN}✓ All critical checks passed!{Colors.RESET}")
        print("环境就绪。root/frida-server 为运行时可选能力，按需启动。")
        sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
