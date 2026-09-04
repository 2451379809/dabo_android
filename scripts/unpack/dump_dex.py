#!/usr/bin/env python3
"""
DEX Unpacking Tool
Wrapper for Frida-based DEX dumping scripts
"""

import subprocess
import argparse
import os
import sys
import time
from pathlib import Path

# 工具自动探测
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
import toolenv

FRIDA_CMD = toolenv.resolve("frida")  # None 时由 check_frida 提示安装
SCRIPT_DIR = Path(__file__).parent / "frida"

DUMP_METHODS = {
    "memory": "dump_dex_memory.js",
    "classloader": "dump_dex_classloader.js",
}

# frida-tools >= 12 (frida 16+) 的 spawn 默认自动 resume，--no-pause 已移除
_NO_PAUSE_NEEDED = False
if FRIDA_CMD:
    try:
        _v = subprocess.run([FRIDA_CMD, "--version"], capture_output=True,
                            text=True, timeout=5).stdout.strip()
        _NO_PAUSE_NEEDED = int(_v.split(".")[0]) < 16
    except Exception:
        _NO_PAUSE_NEEDED = False


def check_frida():
    """Check if Frida is available"""
    if not FRIDA_CMD:
        print("[✗] Frida not found. Install: pip install frida-tools")
        print("    或设置 DABO_FRIDA 指向 frida 可执行文件")
        return False
    try:
        result = subprocess.run([FRIDA_CMD, "--version"],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"[✓] Frida version: {version}")
            return True
        else:
            print(f"[✗] Frida check failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("[✗] Frida command timeout")
        return False


def check_device():
    """通过 frida-ps -U 验证设备连接与 frida-server 状态"""
    frida_ps = toolenv.resolve("frida-ps")
    if not frida_ps:
        print("[✗] frida-ps 不可用，跳过设备检查")
        return True
    try:
        result = subprocess.run([frida_ps, "-U"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("[✓] 设备已连接, frida-server 运行中")
            return True
        print("[✗] 无法连接设备（未连接或 frida-server 未运行）")
        print("    启动: adb shell 'su -c /data/local/tmp/frida-server &'")
        return False
    except Exception:
        print("[✗] No device connected or Frida server not running")
        return False

def dump_dex(package: str, method: str = "memory", output: str = "./dumped_dex", 
             spawn: bool = True, no_pause: bool = True):
    """
    Dump DEX from target package
    
    Args:
        package: Target package name (e.g., com.example.app)
        method: Dump method (memory/classloader/opencommon)
        output: Output directory
        spawn: True=spawn mode, False=attach mode
        no_pause: True=continue execution, False=pause on start
    """
    
    if method not in DUMP_METHODS:
        print(f"[✗] Invalid method: {method}")
        print(f"    Available: {', '.join(DUMP_METHODS.keys())}")
        return False
    
    script_path = SCRIPT_DIR / DUMP_METHODS[method]
    if not script_path.exists():
        print(f"[✗] Script not found: {script_path}")
        return False
    
    # Build Frida command
    cmd = [FRIDA_CMD, "-U"]
    
    if spawn:
        cmd.extend(["-f", package])
    else:
        cmd.append(package)
    
    cmd.extend(["-l", str(script_path)])

    # 仅旧版 frida (<16) 需要显式 --no-pause
    if no_pause and spawn and _NO_PAUSE_NEEDED:
        cmd.append("--no-pause")
    
    print(f"[*] Dumping DEX from: {package}")
    print(f"[*] Method: {method}")
    print(f"[*] Output: {output}")
    print(f"[*] Mode: {'spawn' if spawn else 'attach'}")
    print(f"[*] Script: {script_path.name}")
    print()
    print(f"[*] Command: {' '.join(cmd)}")
    print()
    print("[*] Starting Frida...")
    print("=" * 60)
    
    # Create output directory
    os.makedirs(output, exist_ok=True)
    
    try:
        # Run Frida (interactive mode)
        subprocess.run(cmd)
        
        print()
        print("=" * 60)
        print(f"[✓] Dump complete. Check {output}/ for .dex files")
        return True
        
    except KeyboardInterrupt:
        print()
        print("[*] Interrupted by user")
        return False
    except Exception as e:
        print(f"[✗] Error: {e}")
        return False

def validate_dex(dex_path: str):
    """Validate dumped DEX file"""
    if not os.path.exists(dex_path):
        return False, "File not found"
    
    # Check DEX magic header
    with open(dex_path, "rb") as f:
        header = f.read(8)
    
    # DEX magic: dex\n035\0 or similar
    if header[:4] == b"dex\n":
        version = header[4:7].decode('ascii', errors='ignore')
        return True, f"Valid DEX (version {version})"
    else:
        return False, "Invalid DEX magic header"

def main():
    parser = argparse.ArgumentParser(
        description="DEX Unpacking Tool for Android",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dump using memory search (default)
  python dump_dex.py com.example.app
  
  # Dump using ClassLoader hook
  python dump_dex.py com.example.app --method classloader
  
  # Attach to running process
  python dump_dex.py com.example.app --attach
  
  # Custom output directory
  python dump_dex.py com.example.app --output ./my_dex_dump
        """
    )
    
    parser.add_argument("package", help="Target package name")
    parser.add_argument("-m", "--method", 
                       choices=list(DUMP_METHODS.keys()),
                       default="memory",
                       help="Dump method (default: memory)")
    parser.add_argument("-o", "--output", 
                       default="./dumped_dex",
                       help="Output directory (default: ./dumped_dex)")
    parser.add_argument("-a", "--attach", 
                       action="store_true",
                       help="Attach mode instead of spawn (app must be running)")
    parser.add_argument("-p", "--pause", 
                       action="store_true",
                       help="Pause on start (for manual trigger)")
    parser.add_argument("--skip-check", 
                       action="store_true",
                       help="Skip environment checks")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("DEX Unpacking Tool")
    print("=" * 60)
    print()
    
    # Environment checks
    if not args.skip_check:
        print("[*] Checking environment...")
        if not check_frida():
            sys.exit(1)
        if not check_device():
            sys.exit(1)
        print()
    
    # Dump DEX
    success = dump_dex(
        package=args.package,
        method=args.method,
        output=args.output,
        spawn=not args.attach,
        no_pause=not args.pause
    )
    
    if success:
        # Validate dumped files
        print()
        print("[*] Validating dumped DEX files...")
        dex_files = list(Path(args.output).glob("*.dex"))
        
        if not dex_files:
            print("[!] No .dex files found in output directory")
        else:
            for dex_file in dex_files:
                valid, msg = validate_dex(str(dex_file))
                status = "✓" if valid else "✗"
                print(f"[{status}] {dex_file.name}: {msg}")
        
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
