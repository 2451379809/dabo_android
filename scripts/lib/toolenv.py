#!/usr/bin/env python3
"""
toolenv.py — dabo_android 工具自动探测（零配置，开箱即用）

探测顺序（与 ZCode 官方 android-emulator 插件 sdk.js / spider-king check_reverse_env.py 同一模式）:
  1. 可选环境变量（不设置也能用）:
     DABO_ADB / DABO_JAVA / DABO_FRIDA / DABO_JADX / DABO_APKTOOL / SOFIXER_PATH
     以及标准变量 ANDROID_HOME / ANDROID_SDK_ROOT / JAVA_HOME
  2. PATH 查找（shutil.which，正常安装的工具直接命中）
  3. 各平台常见安装位置（含雷电/MuMu 模拟器自带 adb、jadx 默认安装目录）
  4. toolenv_extra.py 中的自定义候选（可自行编辑/清空，不影响他人）

找不到时: resolve() 返回 None；require() 打印安装提示并以非零码退出。
入口脚本用法:
    import toolenv
    adb = toolenv.require('adb')          # 找不到直接退出并提示
    cmd = toolenv.require_cmd('jadx')     # 返回 argv 前缀（jar 型工具自动展开为 [java, -jar, xx.jar]）
"""

import os
import shutil
import sys
from pathlib import Path

HOME = Path.home()
IS_WIN = os.name == "nt"
_EXE = ".exe" if IS_WIN else ""

# ---------------------------------------------------------------- helpers

def _env(*names):
    for n in names:
        v = os.environ.get(n)
        if v and Path(v).exists():
            return str(Path(v))
    return None


def _which(name):
    return shutil.which(name)


def _first_existing(*paths):
    for p in paths:
        if p and Path(p).exists():
            return str(Path(p))
    return None


def _load_extras():
    """加载同目录 toolenv_extra.py（可选，供本机/个人补充候选路径）。"""
    try:
        import toolenv_extra  # type: ignore
        return toolenv_extra
    except ImportError:
        return None


def _glob_first(pattern):
    """glob 取排序后的最后一个（即版本号最新的那个）。"""
    try:
        p = Path(pattern)
        hits = sorted(p.parent.glob(p.name))
        return str(hits[-1]) if hits else None
    except Exception:
        return None


# ---------------------------------------------------------------- resolvers

def _android_sdk_roots():
    roots = []
    for var in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        v = os.environ.get(var)
        if v:
            roots.append(Path(v))
    roots += [
        HOME / "AppData" / "Local" / "Android" / "Sdk",
        HOME / "Android" / "Sdk",
        HOME / "Library" / "Android" / "sdk",
        Path("/opt/android-sdk"),
        Path("/usr/local/share/android-sdk"),
        # 常见安卓模拟器（国内逆向环境常用，不存在则自动跳过）
        Path(r"D:\leidian\LDPlayer9"),
        Path(r"D:\leidian\LDPlayer"),
        Path(r"D:\MuMuPlayer\nx_main"),
        Path(r"D:\Program Files\Nox\bin"),
    ]
    return roots


def resolve(kind):
    """返回工具可执行文件路径，找不到返回 None。"""
    extra = _load_extras()

    if kind == "adb":
        p = _env("DABO_ADB")
        if p:
            return p
        w = _which("adb")
        if w:
            return w
        cands = []
        for root in _android_sdk_roots():
            cands += [root / "platform-tools" / ("adb" + _EXE), root / ("adb" + _EXE)]
        if extra:
            cands += [Path(x) for x in getattr(extra, "ADB", [])]
        return _first_existing(*cands)

    if kind == "java":
        jh = os.environ.get("JAVA_HOME")
        if jh:
            p = _first_existing(Path(jh) / "bin" / ("java" + _EXE))
            if p:
                return p
        w = _which("java")
        if w:
            return w
        cands = [
            Path(r"C:\Program Files (x86)\Common Files\Oracle\Java\java8path\java.exe"),
        ]
        if IS_WIN:
            g = _glob_first(r"C:\Program Files\Microsoft\jdk-*\bin\java.exe")
            if g:
                cands.insert(0, Path(g))
            g = _glob_first(r"C:\Program Files\Eclipse Adoptium\jdk-*\bin\java.exe")
            if g:
                cands.insert(0, Path(g))
        if extra:
            cands += [Path(x) for x in getattr(extra, "JAVA", [])]
        return _first_existing(*cands)

    if kind in ("frida", "frida-ps"):
        env_key = "DABO_FRIDA" if kind == "frida" else "DABO_FRIDA_PS"
        p = _env(env_key)
        if p:
            return p
        w = _which(kind)
        if w:
            return w
        # frida 通常由 pip 安装: 落在当前 Python 的 Scripts/ 目录
        scripts = Path(sys.prefix) / "Scripts"
        cands = [scripts / (kind + _EXE), scripts / (kind + ".bat")]
        if extra:
            key = "FRIDA" if kind == "frida" else "FRIDA_PS"
            cands += [Path(x) for x in getattr(extra, key, [])]
        return _first_existing(*cands)

    if kind in ("jadx", "apktool"):
        env_key = "DABO_" + kind.upper()
        p = os.environ.get(env_key)
        if p and Path(p).exists():
            return str(Path(p))  # 可以是启动器、目录或 jar
        w = _which(kind)
        if w:
            return w
        if kind == "jadx":
            launcher = _first_existing(HOME / ".local" / "share" / "jadx" / "bin" / "jadx.bat",
                                       HOME / ".local" / "share" / "jadx" / "bin" / "jadx")
            if launcher:
                return launcher
        jar = resolve_jar(kind)
        if jar:
            return jar
        return None

    if kind == "sofixer":
        p = _env("SOFIXER_PATH")
        if p:
            return p
        w = _which("sofixer")
        if w:
            return w
        if extra:
            return _first_existing(*[Path(x) for x in getattr(extra, "SOFIXER", [])])
        return None

    return None


def resolve_jar(name):
    """定位 jar 型工具（apktool/smali/baksmali/d8/jadx）。"""
    extra = _load_extras()
    p = os.environ.get("DABO_" + name.upper() + "_JAR")
    if p and Path(p).exists():
        return str(Path(p))
    cands = [HOME / "apktool" / "apktool.jar"]
    if extra:
        cands += [Path(x) for x in getattr(extra, "JARS", {}).get(name, [])]
    return _first_existing(*cands)


def resolve_cmd(kind):
    """返回工具的 argv 前缀。jar 型工具自动展开为 [java, -jar, xx.jar]。找不到返回 None。"""
    p = resolve(kind)
    if p is None:
        return None
    if p.endswith(".jar"):
        java = resolve("java")
        if java:
            return [java, "-jar", p]
        return None
    return [p]


# ---------------------------------------------------------------- require + hints

INSTALL_HINTS = {
    "adb": "安装 Android platform-tools 并加入 PATH，或设置 ANDROID_HOME\n"
           "  下载: https://developer.android.com/tools/releases/platform-tools\n"
           "  （雷电/MuMu 模拟器用户无需安装，toolenv 会自动探测模拟器自带 adb）",
    "java": "安装 JDK 8/11/17/21 并加入 PATH，或设置 JAVA_HOME\n"
            "  推荐: https://adoptium.net/",
    "frida": "pip install frida-tools （设备端还需运行 frida-server）",
    "frida-ps": "pip install frida-tools",
    "jadx": "下载 jadx 并解压（默认安装到 %%USERPROFILE%%\\.local\\share\\jadx），或加入 PATH\n"
            "  下载: https://github.com/skylot/jadx/releases",
    "apktool": "下载 apktool（wrapper 或 jar），或设置 DABO_APKTOOL_JAR 指向 apktool.jar\n"
               "  下载: https://apktool.org/",
    "sofixer": "（可选）编译/下载 SoFixer 并设置 SOFIXER_PATH，用于修复 dump 出的 SO\n"
               "  https://github.com/F8LEFT/SoFixer",
}


def require(kind):
    """resolve + 找不到时打印安装提示并退出。"""
    p = resolve(kind)
    if p:
        return p
    print("[✗] 未找到工具: %s" % kind)
    print("    " + INSTALL_HINTS.get(kind, "请安装后加入 PATH").replace("\n", "\n    "))
    sys.exit(1)


def require_cmd(kind):
    p = resolve_cmd(kind)
    if p:
        return p
    require(kind)  # 打印提示并退出
    return None


def frida_servers():
    """返回本机可用的 frida-server 设备端二进制列表（可选）。"""
    extra = _load_extras()
    if extra:
        return [x for x in getattr(extra, "FRIDA_SERVERS", []) if Path(x).exists()]
    return []


if __name__ == "__main__":
    # 直接运行时输出探测报告: python toolenv.py
    print("dabo_android toolenv 探测报告")
    for k in ("adb", "java", "frida", "frida-ps", "jadx", "apktool", "sofixer"):
        print("  %-9s %s" % (k, resolve(k) or "-- 未找到 --"))
    servers = frida_servers()
    if servers:
        print("  本机 frida-server 候选:")
        for s in servers:
            print("    -", s)
