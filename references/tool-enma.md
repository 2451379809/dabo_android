# enma - Frida-based Android Runtime Analysis Toolkit

## Overview

**enma** is a comprehensive Android security research toolkit powered by Frida. It provides 25 specialized agents for extracting and analyzing runtime artifacts including DEX files, IL2CPP binaries, Unity assets, crypto keys, network traffic, and game engine internals.

**Key Features**:
- Python 3.12+ CLI with structured workflow
- 25 JavaScript agents organized by category
- Automated dump → analyze → report pipeline
- Game engine support (Unity IL2CPP, Mono, Unreal Engine 4)
- Network protocol analysis (HTTP, WebSocket, Protobuf)
- Security bypass capabilities (SSL pinning, SafetyNet, anti-detect)
- Interactive memory scanning and patching

**Intended Use**: Penetration testing, CTF challenges, security research, reverse engineering of apps you own or have explicit permission to analyze.

---

## Installation

### Prerequisites
- Python 3.12 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- ADB in PATH
- Rooted Android device or emulator
- Frida server on device

### Setup Steps

```bash
# Clone repository
git clone https://github.com/ykus4/enma
cd enma

# Install dependencies with uv
uv sync

# Push frida-server to device (enma includes this command)
uv run enma setup

# Verify installation
uv run enma --help
```

---

## CLI Workflow

enma follows a sequential pipeline from dump to report:

```
setup → list → dump → analyze → report
```

### 1. Setup Frida Server

```bash
uv run enma setup
# Pushes frida-server to /data/local/tmp/ and starts it
# Use --serial <device-id> for multiple devices
# Use --force to overwrite existing server
```

### 2. List Target Applications

```bash
uv run enma list
# Shows all installed packages with their identifiers
# Use --serial <device-id> for specific device
```

### 3. Dump Runtime Artifacts

```bash
# Dump with all default agents (20 agents)
uv run enma dump com.example.game -o ./dump

# Dump with specific agents only
uv run enma dump com.example.game -o ./dump -t dex -t il2cpp -t crypto

# Spawn mode (start app fresh)
uv run enma dump com.example.game -o ./dump --spawn

# Attach mode (app must already be running)
uv run enma dump com.example.game -o ./dump

# Watch mode (wait for app to start)
uv run enma dump com.example.game -o ./dump --watch
```

**Output Structure**:
```
./dump/
├── dex/              # Dumped DEX files
├── il2cpp/           # IL2CPP metadata and binaries
├── assets/           # Unity AssetBundles
├── heap/             # Heap dumps
├── crypto/           # Crypto keys and algorithms
├── network/          # HTTP/WebSocket/Protobuf captures
├── storage/          # SQLite, file I/O logs
├── jni/              # JNI call traces
└── ... (other agent outputs)
```

### 4. Analyze Dump

```bash
uv run enma analyze ./dump
# Post-processing: extracts metadata, correlates artifacts
# Generates analysis.json with structured findings

# Custom output path
uv run enma analyze ./dump -o ./analysis_results.json
```

### 5. Generate Report

```bash
# HTML report (default)
uv run enma report ./dump
# → ./dump/report.html

# Custom output
uv run enma report ./dump -o ./custom_report.html

# JSON output (machine-readable)
uv run enma report ./dump --json -o ./report.json
```

---

## 25 Agents Catalog

enma agents are organized into 7 categories:

### Dump Agents (5 agents)
Extract core runtime artifacts

| Agent | File | Purpose | Output |
|-------|------|---------|--------|
| **dex** | `dump/dex_agent.js` | Dump DEX files from memory (ClassLoader hook + memory search) | `dex/*.dex` |
| **il2cpp** | `dump/il2cpp_agent.js` | Dump IL2CPP metadata and global-metadata.dat | `il2cpp/metadata.dat`, `il2cpp/libil2cpp.so` |
| **assets** | `dump/assets_agent.js` | Extract Unity AssetBundles | `assets/*.bundle` |
| **mono** | `dump/mono_agent.js` | Dump Mono assemblies and images | `mono/*.dll` |
| **heap** | `dump/heap_agent.js` | Capture heap snapshots | `heap/*.hprof` |

### Bypass Agents (5 agents)
Defeat security mechanisms

| Agent | File | Purpose | Output |
|-------|------|---------|--------|
| **ssl** | `bypass/ssl_agent.js` | Bypass SSL pinning (OkHttp3, TrustManager, Cronet) | `network/ssl_bypass.log` |
| **crypto** | `bypass/crypto_agent.js` | Hook crypto APIs (Cipher, MessageDigest, Mac, SecretKey) | `crypto/keys.json`, `crypto/operations.log` |
| **anti_detect** | `bypass/anti_detect_agent.js` | Bypass root/Frida/emulator detection | `bypass/detections.log` |
| **anti_tamper** | `bypass/anti_tamper_agent.js` | Bypass integrity checks (signature, CRC, file hash) | `bypass/tamper.log` |
| **safetynet** | `bypass/safetynet_agent.js` | Bypass Google SafetyNet attestation | `bypass/safetynet.log` |

### Network Agents (4 agents)
Capture and analyze network protocols

| Agent | File | Purpose | Output |
|-------|------|---------|--------|
| **http** | `network/http_agent.js` | Hook HTTP libraries (OkHttp, HttpURLConnection, Retrofit) | `network/http_requests.jsonl` |
| **websocket** | `network/websocket_agent.js` | Capture WebSocket frames (OkHttp, Java-WebSocket) | `network/websocket.jsonl` |
| **protobuf** | `network/protobuf_agent.js` | Dump Protobuf messages and schemas | `network/protobuf/*.proto`, `network/protobuf_messages.jsonl` |
| **binder** | `network/binder_agent.js` | Trace Android Binder IPC calls | `network/binder.log` |

### Storage Agents (3 agents)
Monitor file and database operations

| Agent | File | Purpose | Output |
|-------|------|---------|--------|
| **sqlite** | `storage/sqlite_agent.js` | Log SQLite queries and results | `storage/sqlite_queries.log` |
| **fileio** | `storage/fileio_agent.js` | Trace file read/write/open/close | `storage/file_operations.log` |
| **dlopen** | `storage/dlopen_agent.js` | Hook dlopen/dlsym for SO loading | `storage/dlopen.log` |

### Analysis Agents (3 agents)
Dynamic code analysis and tracing

| Agent | File | Purpose | Output |
|-------|------|---------|--------|
| **jni** | `analysis/jni_agent.js` | Trace JNI calls between Java and Native | `jni/calls.log` |
| **coverage** | `analysis/coverage_agent.js` | Track code coverage (basic block execution) | `analysis/coverage.json` |
| **tracer** | `analysis/tracer_agent.js` | Generic function call tracer | `analysis/trace.log` |

### UE4 Agents (3 agents)
Unreal Engine 4 game reverse engineering

| Agent | File | Purpose | Output |
|-------|------|---------|--------|
| **ue4_sdk** | `ue4/ue4_sdk_agent.js` | Dump UE4 SDK structures (UObject, UFunction, FName) | `ue4/sdk/*.json` |
| **ue4_pak** | `ue4/ue4_pak_agent.js` | Extract .pak archives | `ue4/pak/*.pak` |
| **ue4_blueprint** | `ue4/ue4_blueprint_agent.js` | Decompile Blueprint scripts | `ue4/blueprints/*.json` |

### Memory Agents (2 agents)
Interactive memory operations (RPC-only, not included in default dump)

| Agent | File | Purpose | Usage |
|-------|------|---------|-------|
| **memscan** | `mem/memscan_agent.js` | Search memory for patterns/values | `uv run enma memscan <target> --pattern <hex>` |
| **mempatch** | `mem/mempatch_agent.js` | Patch memory at runtime | `uv run enma mempatch <target> --address <addr> --value <val>` |

---

## Advanced CLI Commands

### Repack APK (Frida Gadget Injection)

```bash
# Inject Frida Gadget for non-root analysis
uv run enma repack app.apk -o app_gadget.apk --arch arm64-v8a

# Keep intermediate workdir for debugging
uv run enma repack app.apk -o app_gadget.apk --keep-workdir
```

### Unity AssetBundle Extraction

```bash
# After dump, extract Unity bundles to readable format
uv run enma unity ./dump -o ./unity_assets
# Uses UnityPy to parse .bundle files
```

### UE4 Operations

```bash
# Dump UE4 SDK only
uv run enma ue4 com.example.ue4game --sdk -o ./ue4_dump

# Extract .pak files
uv run enma ue4 com.example.ue4game --pak -o ./ue4_dump

# Dump blueprints
uv run enma ue4 com.example.ue4game --blueprint -o ./ue4_dump
```

### Memory Operations

```bash
# Scan memory for hex pattern
uv run enma memscan com.example.app --pattern "DEADBEEF" --serial emulator-5554

# Patch memory (int32 at address)
uv run enma mempatch com.example.app --address 0x12345678 --value 999 --type int32

# Supported types: int8/16/32/64, uint8/16/32/64, float, double
```

---

## Integration with dabo_android

### When to Use enma vs Existing Tools

| Scenario | Recommended Tool | Reason |
|----------|------------------|--------|
| Quick DEX dump | `scripts/unpack/dump_dex.py` | Faster, single-purpose |
| Unity game (IL2CPP) | **enma** | Dedicated IL2CPP + assets agents |
| UE4 game | **enma** | Only tool with UE4 SDK/pak/blueprint support |
| Comprehensive audit | **enma** | 25 agents cover all surfaces in one run |
| Crypto algorithm analysis | Both | enma for keys, existing `frida_crypto_hook.js` for detailed traces |
| SSL pinning bypass | `frida_universal_ssl_unpin.js` | Simpler for quick HTTPS interception |
| Network protocol analysis | **enma** | Structured HTTP/WebSocket/Protobuf capture |
| Memory forensics | **enma** | Interactive memscan/mempatch |

### Workflow Integration Example

```bash
# 1. Environment check (dabo_android)
python C:\Users\LT3843\.zcode\skills\dabo_android\scripts\check\check_android_env.py

# 2. Quick APK analysis (dabo_android)
python C:\Users\LT3843\.zcode\skills\dabo_android\scripts\analyze\quick_analyze_apk.py com.example.game

# 3. If game uses Unity/UE4, use enma for runtime dump
cd E:\project\enma_workspace
uv run enma dump com.example.game -o ./game_dump

# 4. Analyze and generate report
uv run enma analyze ./game_dump
uv run enma report ./game_dump

# 5. For specific Native analysis, extract SO and use IDA
# SO files are in game_dump/il2cpp/libil2cpp.so or APK lib/ folder
```

---

## Comparison with Other Tools

| Feature | enma | frida-dexdump | BlackDex | FART |
|---------|------|---------------|----------|------|
| **DEX dump** | ✅ | ✅ | ✅ | ✅ |
| **IL2CPP support** | ✅ | ❌ | ❌ | ❌ |
| **Unity assets** | ✅ | ❌ | ❌ | ❌ |
| **UE4 support** | ✅ | ❌ | ❌ | ❌ |
| **Network capture** | ✅ | ❌ | ❌ | ❌ |
| **Crypto hooks** | ✅ | ❌ | ❌ | ❌ |
| **Requires Frida** | ✅ | ✅ | ❌ | ❌ (kernel mod) |
| **Python API** | ✅ | ❌ | ❌ | ❌ |
| **HTML reports** | ✅ | ❌ | ❌ | ❌ |
| **Best for** | Games, comprehensive audits | Pure Java apps | Non-root DEX dump | Instruction-level dump |

---

## Output Files Reference

### Core Dump Files

```
dump/
├── dex/
│   ├── classes.dex
│   ├── classes2.dex
│   └── dynamic_*.dex
├── il2cpp/
│   ├── global-metadata.dat
│   ├── libil2cpp.so
│   └── metadata.json
├── assets/
│   └── *.bundle (Unity AssetBundles)
├── heap/
│   └── heap_snapshot.hprof
```

### Analysis Files

```
dump/
├── crypto/
│   ├── keys.json              # Extracted crypto keys (AES, RSA, HMAC)
│   └── operations.log         # Cipher.init/doFinal traces
├── network/
│   ├── http_requests.jsonl    # One JSON object per line
│   ├── websocket.jsonl
│   └── protobuf/
│       ├── *.proto
│       └── protobuf_messages.jsonl
├── jni/
│   └── calls.log              # Java ↔ Native boundary traces
├── storage/
│   ├── sqlite_queries.log
│   └── file_operations.log
```

### Generated Reports

```
dump/
├── analysis.json              # Machine-readable findings
├── report.html                # Human-readable HTML report
└── report.json                # Structured JSON report
```

---

## Environment Configuration

### Python Environment (uv)

enma uses `uv` for dependency management. No manual venv creation needed.

```bash
# Install uv (if not present)
pip install uv

# Sync dependencies
cd enma
uv sync

# Run without installation
uv run enma <command>

# Or install editable
uv pip install -e .
enma <command>
```

### Frida Server Management

```bash
# Auto-push frida-server (enma includes binaries)
uv run enma setup

# Manual frida-server (if needed)
# 1. Download frida-server from https://github.com/frida/frida/releases
# 2. Push to device:
adb push frida-server-16.x.x-android-arm64 /data/local/tmp/frida-server
adb shell "chmod 755 /data/local/tmp/frida-server"
adb shell "su -c '/data/local/tmp/frida-server &'"
```

### Multiple Devices

```bash
# List devices
adb devices

# Use --serial flag
uv run enma setup --serial emulator-5554
uv run enma list --serial emulator-5554
uv run enma dump com.example.app --serial emulator-5554 -o ./dump
```

---

## Practical Examples

### Example 1: Unity Game DEX + IL2CPP Dump

```bash
# Setup
uv run enma setup

# Dump (default agents include dex + il2cpp + assets)
uv run enma dump com.mihoyo.genshin -o ./genshin_dump --spawn

# Analyze IL2CPP metadata
uv run enma analyze ./genshin_dump

# Extract Unity assets
uv run enma unity ./genshin_dump -o ./genshin_assets

# Generate report
uv run enma report ./genshin_dump
# Open genshin_dump/report.html in browser
```

### Example 2: Capture Crypto Keys and Network Traffic

```bash
# Dump with specific agents
uv run enma dump com.example.app -o ./app_dump -t crypto -t http -t ssl

# Crypto keys are in: app_dump/crypto/keys.json
# HTTP requests: app_dump/network/http_requests.jsonl

# Generate report to see key usage
uv run enma report ./app_dump
```

### Example 3: Bypass SafetyNet and Dump

```bash
# Use anti-detect + safetynet agents
uv run enma dump com.banking.app -o ./bank_dump -t anti_detect -t safetynet -t dex

# Check bypass logs
type bank_dump\bypass\safetynet.log
```

### Example 4: UE4 Game Analysis

```bash
# Dump UE4 SDK structures
uv run enma ue4 com.pubg.mobile --sdk -o ./pubg_ue4

# Extract .pak files
uv run enma ue4 com.pubg.mobile --pak -o ./pubg_ue4

# Dump blueprints
uv run enma ue4 com.pubg.mobile --blueprint -o ./pubg_ue4
```

### Example 5: Interactive Memory Patching

```bash
# 1. Find value in memory
uv run enma memscan com.game.app --pattern "00000064" --type uint32
# → Found at 0x12340000

# 2. Patch value
uv run enma mempatch com.game.app --address 0x12340000 --value 999 --type uint32
# → Value changed from 100 to 999
```

---

## Troubleshooting

### enma setup fails

```bash
# Check ADB connection
adb devices

# Check root access
adb shell su -c "id"
# Should show uid=0(root)

# Manually push frida-server
adb push frida-server /data/local/tmp/
adb shell "chmod 755 /data/local/tmp/frida-server"
adb shell "su -c '/data/local/tmp/frida-server &'"
```

### No output in dump directory

- Ensure app is running (use `--spawn` or start app manually with `--watch`)
- Check agent logs in console output
- Verify Frida connection: `frida-ps -U`

### Python version mismatch

```bash
# enma requires Python 3.12+
python --version

# Install Python 3.12 if needed
# Then recreate uv environment
cd enma
uv sync --python 3.12
```

### IL2CPP dump incomplete

- IL2CPP agent requires app to fully initialize
- Use `--spawn` and wait 10-15 seconds before triggering dump
- Check if `libil2cpp.so` exists in APK `lib/` folder

---

## Resources

### Official Documentation
- GitHub: https://github.com/ykus4/enma
- Full docs: https://ykus4.github.io/enma
- Agent Reference: https://ykus4.github.io/enma/agents/
- Architecture: https://ykus4.github.io/enma/architecture/

### Related Tools
- Frida: https://frida.re
- UnityPy: https://github.com/K0lb3/UnityPy (used by enma for Unity extraction)
- uv: https://docs.astral.sh/uv/

### Disclaimer

Use enma only against apps you own or have explicit written authorization to analyze. Dumped files may contain sensitive cryptographic material — handle with care. Licensed under MIT License.

---

**Document Version**: 1.0  
**Last Updated**: 2026-08-26  
**Maintained by**: dabo_android skill
