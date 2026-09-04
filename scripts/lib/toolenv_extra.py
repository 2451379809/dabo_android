# -*- coding: utf-8 -*-
"""本机（维护者）自定义工具路径候选 — 由 toolenv.py 自动加载，优先级最低。

开源使用者说明：
- 本文件只作为"找不到时的额外候选"，不影响 PATH / 常见安装位置的探测；
- 可以把下面的路径改成你自己机器的，或清空各列表（skill 仍可正常工作）。
"""

ADB = [
    r"D:\leidian\LDPlayer9\adb.exe",
    r"E:\project\data\.tools\android\platform-tools\adb.exe",
    r"D:\MuMuPlayer\nx_main\adb.exe",
]

FRIDA = [r"D:\python3.12\Scripts\frida.exe"]
FRIDA_PS = [r"D:\python3.12\Scripts\frida-ps.exe"]

JAVA = [
    r"C:\Program Files\Microsoft\jdk-21.0.11.10-hotspot\bin\java.exe",
    r"C:\Program Files (x86)\Common Files\Oracle\Java\java8path\java.exe",
]

SOFIXER = []

JARS = {
    "jadx": [r"E:\project\data\.workbuddy\toolchain-downloads\jadx-ai-mcp-6.4.0.jar"],
    "apktool": [r"E:\project\data\.tools\apktool\apktool.jar"],
    "smali": [r"E:\project\data\.tools\smali.jar"],
    "baksmali": [r"E:\project\data\.tools\baksmali.jar"],
    "d8": [r"E:\project\data\.tools\d8.jar"],
}

# 设备端 frida-server 二进制（可选，用于 push 到设备）
FRIDA_SERVERS = [
    r"E:\project\data\tk\tools\frida-server-16.7.19-android-x86_64",
    r"E:\project\data\tk\tools\frida-server-17.2.17-android-x86_64",
]
