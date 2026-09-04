# Tool Paths Configuration


> **工具定位说明（v2.2）**：脚本运行**不依赖**本文档的路径——一切由
> `scripts/lib/toolenv.py` 自动探测（env → PATH → 常见安装位置 → toolenv_extra.py）。
> 下文路径为**维护者机器的参考映射**，供人工核对/复现环境使用。
> 探测报告: `python scripts/lib/toolenv.py`

Complete tool path mapping for dabo_android on Windows x64.

## ADB (Android Debug Bridge)

```yaml
ADB_PATH: E:\project\data\.tools\android\platform-tools\adb.exe
ADB_VERSION: 37.0.0
```

**Usage**:
```powershell
$ADB = "E:\project\data\.tools\android\platform-tools\adb.exe"
& $ADB devices
& $ADB shell pm list packages
```

## Java Environment

```yaml
# Java 8 (for older tools)
JAVA8_PATH: C:\Program Files (x86)\Common Files\Oracle\Java\java8path\java.exe

# Java 21 (recommended)
JAVA21_PATH: C:\Program Files\Microsoft\jdk-21.0.11.10-hotspot\bin\java.exe
JAVA21_HOME: C:\Program Files\Microsoft\jdk-21.0.11.10-hotspot
```

**Usage**:
```powershell
$JAVA = "C:\Program Files\Microsoft\jdk-21.0.11.10-hotspot\bin\java.exe"
& $JAVA -version
```

## APK Analysis Tools

### JADX (DEX to Java decompiler)

```yaml
JADX_JAR: E:\project\data\.workbuddy\toolchain-downloads\jadx-ai-mcp-6.4.0.jar
JADX_VERSION: 6.4.0
```

**Usage**:
```powershell
$JAVA = "C:\Program Files\Microsoft\jdk-21.0.11.10-hotspot\bin\java.exe"
$JADX = "E:\project\data\.workbuddy\toolchain-downloads\jadx-ai-mcp-6.4.0.jar"

# GUI mode
& $JAVA -jar $JADX target.apk

# CLI mode (output to directory)
& $JAVA -jar $JADX -d output_dir target.apk

# Export to single file
& $JAVA -jar $JADX --export-gradle target.apk
```

### ApkTool (APK decompile/recompile)

```yaml
APKTOOL_JAR: E:\project\data\.tools\apktool\apktool.jar
APKTOOL_VERSION: 2.x
```

**Usage**:
```powershell
$JAVA = "C:\Program Files\Microsoft\jdk-21.0.11.10-hotspot\bin\java.exe"
$APKTOOL = "E:\project\data\.tools\apktool\apktool.jar"

# Decompile APK
& $JAVA -jar $APKTOOL d target.apk -o output_dir

# Recompile APK
& $JAVA -jar $APKTOOL b output_dir -o recompiled.apk

# Decompile with resources
& $JAVA -jar $APKTOOL d -r -s target.apk
```

## Smali Tools

```yaml
SMALI_JAR: E:\project\data\.tools\smali.jar
BAKSMALI_JAR: E:\project\data\.tools\baksmali.jar
SMALI_FAT_JAR: E:\project\data\.tools\smali-fat.jar
```

**Usage**:
```powershell
$JAVA = "C:\Program Files\Microsoft\jdk-21.0.11.10-hotspot\bin\java.exe"

# Disassemble DEX to smali
& $JAVA -jar E:\project\data\.tools\baksmali.jar d classes.dex -o smali_output

# Assemble smali to DEX
& $JAVA -jar E:\project\data\.tools\smali.jar a smali_output -o classes.dex
```

## DEX Tools

```yaml
D8_JAR: E:\project\data\.tools\d8.jar
R8_JAR: E:\project\data\.tools\r8.jar
```

**Usage**:
```powershell
$JAVA = "C:\Program Files\Microsoft\jdk-21.0.11.10-hotspot\bin\java.exe"

# Convert JAR to DEX
& $JAVA -jar E:\project\data\.tools\d8.jar --output output.dex input.jar

# Optimize DEX with R8
& $JAVA -jar E:\project\data\.tools\r8.jar --release --output optimized.jar input.jar
```

## Frida

```yaml
# Frida Client
FRIDA_VERSION: 16.7.19 / 17.2.17
FRIDA_INSTALL: pip install frida-tools

# Frida Server (device-side)
FRIDA_SERVER_16: E:\project\data\tk\tools\frida-server-16.7.19-android-x86_64
FRIDA_SERVER_17: E:\project\data\tk\tools\frida-server-17.2.17-android-x86_64
```

**Setup**:
```powershell
# Install Frida client (one-time)
pip install frida-tools==16.7.19

# Push server to device
$ADB = "E:\project\data\.tools\android\platform-tools\adb.exe"
$FRIDA_SERVER = "E:\project\data\tk\tools\frida-server-16.7.19-android-x86_64"

& $ADB push $FRIDA_SERVER /data/local/tmp/frida-server
& $ADB shell "chmod 755 /data/local/tmp/frida-server"
& $ADB shell "su -c '/data/local/tmp/frida-server &'"

# Test connection
frida-ps -U
```

**Usage**:
```powershell
# Spawn mode (start app with Frida)
frida -U -f com.example.app -l script.js --no-pause

# Attach mode (attach to running app)
frida -U com.example.app -l script.js

# List processes
frida-ps -U

# Remote connection (WiFi ADB)
frida -H 192.168.1.100:5555 -f com.example.app -l script.js
```

## Signing Tools

```yaml
UBER_APK_SIGNER: E:\project\data\.tools\uber-apk-signer.jar
ZIPALIGN: E:\project\data\.tools\android\build-tools\35.0.0-rc3\zipalign.exe
APKSIGNER: E:\project\data\.tools\android\build-tools\35.0.0-rc3\apksigner.bat
```

**Usage**:
```powershell
$JAVA = "C:\Program Files\Microsoft\jdk-21.0.11.10-hotspot\bin\java.exe"

# Sign with uber-apk-signer (auto-generates key)
& $JAVA -jar E:\project\data\.tools\uber-apk-signer.jar --apks recompiled.apk

# Manual signing
$ZIPALIGN = "E:\project\data\.tools\android\build-tools\35.0.0-rc3\zipalign.exe"
$APKSIGNER = "E:\project\data\.tools\android\build-tools\35.0.0-rc3\apksigner.bat"

# 1. Align
& $ZIPALIGN -v 4 unaligned.apk aligned.apk

# 2. Sign
& $APKSIGNER sign --ks my-release-key.jks aligned.apk

# 3. Verify
& $APKSIGNER verify aligned.apk
```

## Unpacking Tools

```yaml
# SoFixer (ELF structure repair)
SOFIXER_32: E:\project\data\tk\tools\SoFixer32
SOFIXER_64: E:\project\data\tk\tools\SoFixer64

# FART (instruction extraction)
FART_ROM: Custom Android ROM required
FART_SCRIPTS: E:\project\data\tk\tools\fart\

# BlackDex (root-based unpacking)
BLACKDEX_APK: E:\project\data\tk\tools\BlackDex.apk
```

**SoFixer Usage** (called by dump_so.py):
```powershell
$ADB = "E:\project\data\.tools\android\platform-tools\adb.exe"

# Push SoFixer to device
& $ADB push E:\project\data\tk\tools\SoFixer64 /data/local/tmp/SoFixer
& $ADB shell "chmod +x /data/local/tmp/SoFixer"

# Fix dumped SO
& $ADB shell "/data/local/tmp/SoFixer -m 0x7bd7b81000 -s /data/local/tmp/libgame.so.dump.so -o /data/local/tmp/libgame.so.fix.so"

# Pull fixed SO
& $ADB pull /data/local/tmp/libgame.so.fix.so ./
```

## IDA Pro

```yaml
IDA_PATH: C:\Program Files\IDA Pro 8.4\ida64.exe
IDA_PYTHON: C:\Program Files\IDA Pro 8.4\python\python.exe
```

**Usage**:
```powershell
# Open SO in IDA
& "C:\Program Files\IDA Pro 8.4\ida64.exe" libgame.so

# Batch mode (with script)
& "C:\Program Files\IDA Pro 8.4\ida64.exe" -A -S"analyze_so.py" libgame.so
```

## Python Environment

```yaml
PYTHON_PATH: C:\Python311\python.exe
PYTHON_VERSION: 3.11+
```

**Required packages**:
```powershell
pip install frida-tools==16.7.19
pip install pycryptodome  # For crypto porting
pip install androguard    # For APK parsing
pip install requests      # For protocol testing
pip install colorama      # For colored output
```

---

## Environment Variables

For convenience, add to PowerShell profile (`$PROFILE`):

```powershell
# Add this to: C:\Users\<username>\Documents\PowerShell\Microsoft.PowerShell_profile.ps1

$env:ADB = "E:\project\data\.tools\android\platform-tools\adb.exe"
$env:JAVA_HOME = "C:\Program Files\Microsoft\jdk-21.0.11.10-hotspot"
$env:JAVA = "$env:JAVA_HOME\bin\java.exe"

function jadx { & $env:JAVA -jar "E:\project\data\.workbuddy\toolchain-downloads\jadx-ai-mcp-6.4.0.jar" $args }
function apktool { & $env:JAVA -jar "E:\project\data\.tools\apktool\apktool.jar" $args }
function adb { & $env:ADB $args }
```

Then use directly:
```powershell
adb devices
jadx target.apk
apktool d target.apk
```

---

## Validation Script

Check all tools at once:

```powershell
python scripts\check\check_android_env.py
```

Expected output:
```
[✓] ADB: 37.0.0
[✓] Java: 21.0.11
[✓] JADX: 6.4.0
[✓] ApkTool: 2.x
[✓] Frida Client: 16.7.19
[✓] Device connected: emulator-5554
[✓] Frida Server running: 16.7.19
[✓] Root access: uid=0(root)
```

---

**Last Updated**: 2026-08-26  
**Platform**: Windows 10/11 x64
