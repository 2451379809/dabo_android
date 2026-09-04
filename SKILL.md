---
name: dabo_android
description: Android native reverse engineering skill for APK analysis, DEX/SO unpacking, protocol extraction, and anti-detection bypass on Windows. Use when the user mentions Android reverse, APK analysis, Frida hook, unpacking (DEX/SO), SSL pinning bypass, signature verification bypass, anti-debugging, root detection, emulator detection, crypto algorithm restoration, or protocol analysis. Delivers tool-chain configuration for Windows environments, battle-tested Frida scripts, unpacking workflows, and operational playbooks.
---

# dabo_android

## Mission

Turn Android apps into protocol-transparent targets through systematic native-layer reverse engineering.

This is a Windows-native Android reverse skill with full tool-chain integration. Use static analysis (jadx, apktool) to understand structure, dynamic instrumentation (Frida) to observe runtime, and unpacking workflows (DEX/SO dump) to defeat protection. Deliver reproducible analysis results, reusable Frida scripts, and protocol extraction code.

## Non-Negotiables

- Start every fresh APK with environment validation: ADB connectivity, Frida server status, root/emulator availability.
- Never hardcode device serial, package name, or rotating tokens before proving their scope and refresh mechanism.
- Keep Frida scripts modular and self-contained: SSL unpinning, anti-detection, crypto hooks, and dumpers are separate concerns.
- For unpacking, distinguish first-generation (whole DEX encryption) from second-generation (instruction extraction/VMP) before choosing tools.
- Back every anti-detection claim with evidence: port scan interception, process name spoofing, or maps file hiding must be verified on target.
- Preserve one successful Frida attachment session until cross-app reuse is proven.
- Apply `references/tool-paths.md` for all external tool invocations; never assume tool locations.

## Prerequisites Gate

Before deep analysis, verify:

### 0. Platform
- **OS**: Windows 10/11 x64
- **Shell**: PowerShell 5.1+ or CMD with UTF-8 support
- **Python**: 3.8+ with pip

### 1. ADB Connection
Verify device connectivity:
```powershell
adb devices
# Expected: <serial> device (not offline/unauthorized)
```

All external tools (adb/java/frida/jadx/apktool/SoFixer) are auto-discovered by `scripts/lib/toolenv.py`, in this order: optional env vars (`DABO_ADB`, `ANDROID_HOME`, ...) → PATH → common install locations (incl. LDPlayer/MuMu bundled adb) → `scripts/lib/toolenv_extra.py` (per-machine candidates, editable). Zero configuration for normally-installed tools. Discovery report:
```powershell
python scripts\lib\toolenv.py
```

Declare connection mode:
- `usb`: Direct USB connection (preferred for stability)
- `wifi`: Wireless ADB (port 5555, may disconnect)
- `emulator`: Local emulator (127.0.0.1:5555 or 127.0.0.1:5037)

### 2. Root/Frida Environment
Confirm privilege level:
```powershell
adb shell su -c "id"
# Expected: uid=0(root) gid=0(root)
```

Check Frida server:
```powershell
adb shell "ps | findstr frida-server"
# Expected: frida-server-16.7.19 or frida-server-17.2.17 running
```

If not running:
```powershell
adb push <frida-server-binary> /data/local/tmp/frida-server
adb shell "chmod 755 /data/local/tmp/frida-server"
adb shell "su -c '/data/local/tmp/frida-server &'"
```
`<frida-server-binary>`: download for the device ABI (e.g. frida-server-16.x-android-x86_64), or pick from the local candidates listed by `scripts/check/check_android_env.py` (sourced from `toolenv_extra.py`).

Test Frida client:
```powershell
frida-ps -U
# Expected: List of running processes
```

### 3. Tool Availability
Run environment check:
```powershell
python scripts\check\check_android_env.py
```

Required tools (see `references/tool-paths.md` for full mapping):
- Java 8 or 21 (for jadx, apktool)
- ADB 37.0.0+
- Frida client 16.7.19+
- apktool, jadx, smali/baksmali

## Quick Start Dispatch

Use these labels internally to keep the first move focused.

| Intent | Route |
|--------|-------|
| `quick-recon` | Basic APK info, permissions, components without unpacking |
| `dex-unpack` | DEX layer unpacking (first-gen or second-gen) |
| `so-unpack` | Native library unpacking and ELF restoration |
| `protocol-trace` | Locate crypto/sign logic, extract algorithm |
| `sign-pure` | Pure-algorithm restoration: unidbg oracle → layer diff → pure rewrite (see `references/pure-algorithm-methodology.md`) |
| `anti-detect` | Bypass root/emulator/Frida detection |
| `ssl-unpin` | Disable SSL certificate pinning for traffic capture |
| `full-reverse` | End-to-end analysis from APK to protocol collector |

Default to the smallest route that answers the user. A bare package name or APK path does not authorize full unpacking, live traffic interception, or account login—clarify intent first.

## Standard Workflows

### Workflow 1: Quick Reconnaissance

**Trigger**: User provides package name or APK path, wants basic info.

**Steps**:
1. Extract APK if package name given:
   ```powershell
   adb shell pm path com.example.app
   # Output: package:/data/app/.../base.apk
   adb pull <path> ./target.apk
   ```

2. Run quick analysis:
   ```powershell
   python scripts\analyze\quick_analyze_apk.py com.example.app
   ```

3. Review output:
   - Manifest permissions (INTERNET, READ_PHONE_STATE)
   - Exported components (activities, services, receivers)
   - Native libraries (.so files)
   - Suspicious keywords (encrypt, sign, verify, root, xposed)

**Output**: JSON report with surface area assessment.

**Next decision**:
- If packed → Route to `dex-unpack` or `so-unpack`
- If plain → Route to `protocol-trace`
- If detects root/frida → Route to `anti-detect`

---

### Workflow 2: DEX Unpacking

**Trigger**: APK is packed (DEX encrypted or obfuscated).

**Decision Tree**:
```
Check packer generation and defense level:
├─ First-gen (whole DEX encrypted, e.g., 360, Bangcle, Legu)
│  ├─ Method A: Memory search for DEX magic header
│  │  → scripts/unpack/frida/dump_dex_memory.js
│  ├─ Method B: ClassLoader hook
│  │  → scripts/unpack/frida/dump_dex_classloader.js
│  └─ Quick paths: frida-dexdump (pip install) or BlackDex (no root)
│
├─ Second-gen (instruction extraction, VMP, e.g., Dingxiang)
│  ├─ frida_fart (root + Frida, no custom ROM) → FartFixer repair
│  ├─ FART custom ROM (most complete) → FartFixer/RXjadx repair
│  └─ BlackDex deep mode (no root)
│
└─ Strong anti-Frida / RASP (crashes on attach)
   ├─ dexhound (no injection: /proc/<pid>/mem carving, target sees nothing)
   └─ eBPFDexDumper (eBPF observation: dump/fix/dumpso/fixso)
      ⚠ eBPF cannot actively invoke: extraction packers still need frida_fart/FART
```

Full escalation ladder (L0 quick → L4 VMP) and per-tool usage: `references/unpacking-tools-guide.md` §10-§11.

**Xposed/LSPosed route** (persistent hooks; nop-repair via GetDex, container 2-gen via RDex, SO repair via FunELF, signature bypass via CorePatch):
use ONLY after verifying the framework is installed on the device — run `scripts\check\check_android_env.py` (Xposed probe section) or the adb commands in the Prerequisites Gate. Changes (module enable / scope) require a device reboot (or at least force-stop of the target app) to take effect — never assume hot-apply. Gate and rules: `references/xposed-lsposed-toolchain.md`.

**Execution Example (Method A - Memory Search)**:
```powershell
# Using Python wrapper
python scripts\unpack\dump_dex.py com.example.app --method memory --output ./dumped_dex

# Or direct Frida (frida-tools >= 12 auto-resumes after spawn; older versions append --no-pause)
frida -U -f com.example.app -l scripts\unpack\frida\dump_dex_memory.js
```

**Validation**:
```powershell
# Check dumped DEX
file dumped_dex/*.dex
# Expected: Dalvik dex file version 035

# Load in jadx (auto-discovered by toolenv)
jadx dumped_dex/classes.dex
```

**Reference**: `references/unpacking_guide.md` for detailed packer identification.

---

### Workflow 3: SO Unpacking

**Trigger**: Native library is packed or IDA fails to parse ELF structure.

**Detection**:
```powershell
# Try opening in IDA
# If: "Cannot parse ELF file structure" → Packed
# If: Red code blocks, missing sections → Packed
```

**Steps**:
1. Identify target SO:
   ```powershell
   frida -U -F -l scripts\unpack\frida\list_modules.js
   # Find: libgame.so, libencrypt.so, etc.
   ```

2. Dump from memory:
   ```powershell
   python scripts\unpack\dump_so.py com.example.app libgame.so --output ./dumped_so
   ```

3. Fix ELF structure:
```powershell
# dump_so.py auto-runs SoFixer when SOFIXER_PATH points to it; otherwise it prints a hint.
# Output: libgame.so_0x7bd7b81000_462848_fix.so
```

4. Verify in IDA:
   ```
   Open: libgame.so_*_fix.so
   Check: Functions window populated, F5 decompile works
   ```

**Reference**: `references/unpacking_guide.md` and `references/unpacking_advanced_tips.md` for troubleshooting.

---

### Workflow 4: SSL Pinning Bypass

**Trigger**: HTTPS traffic capture fails (certificate validation error).

**Universal bypass**:
```powershell
frida -U -f com.example.app -l scripts\hook\frida_universal_ssl_unpin.js
```

**Covers**:
- OkHttp3 CertificatePinner
- TrustManager (custom & system)
- HttpsURLConnection
- WebView SSL Error Handler
- Cronet (experimental)
- Apache HTTP Client

**Validation**:
```powershell
# Start proxy (Fiddler, Charles, mitmproxy)
# In app: trigger network request
# Expected: See decrypted HTTPS in proxy

# Console output:
[+] OkHttp3 SSL Pinning bypassed for: api.example.com
[+] TrustManager hooked: accepting all certificates
```

**Troubleshooting**:
- If still fails → Custom native pinning (check `libssl.so`)
- Route to SO analysis for `SSL_CTX_set_verify`, `X509_verify_cert`

---

### Workflow 5: Anti-Detection Bypass

**Trigger**: App crashes, exits, or refuses to run when Frida is attached.

**Detection methods inventory**:
```
Frida Detection:
├─ Port scan (27042, 27043)
├─ Process name (/proc/<pid>/cmdline contains "frida")
├─ Maps file (/proc/<pid>/maps contains "frida" or "gum-js")
├─ D-Bus communication (frida-helper)
├─ Ptrace attach detection
├─ LD_PRELOAD injection detection
└─ Thread count anomaly

Root Detection:
├─ su binary (which su, /system/xbin/su)
├─ Root apps (com.topjohnwu.magisk, eu.chainfire.supersu)
├─ Build properties (ro.build.tags != release-keys)
├─ SELinux status (getenforce == Permissive)
└─ RW mount points (/system, /data)

Emulator Detection:
├─ Build properties (ro.product.model, ro.hardware)
├─ IMEI/IMSI patterns (000000000000000)
├─ Sensor availability (accelerometer, gyroscope)
├─ GPU renderer (llvmpipe, Android Emulator)
└─ Special files (/dev/socket/qemud, /system/lib/libc_malloc_debug_qemu.so)
```

**Universal bypass script**:
```powershell
frida -U -f com.example.app -l scripts\hook\frida_anti_detection.js
```

**What it hooks**:
- File.exists() → Hide su, Magisk APK
- PackageManager.getInstalledApplications() → Hide root apps
- System.getProperty() → Spoof build tags
- Native exit/abort → Prevent process kill
- ptrace → Block anti-debug
- connect → Block port scan (27042/27043)

**Validation**:
```
Console output should show:
[+] 拦截File.exists调用: /system/xbin/su → false
[+] 隐藏已安装应用: com.topjohnwu.magisk
[+] 拦截exit调用
[+] 拦截connect到端口: 27042
```

If custom detection persists:
- Check logcat for native crashes: `adb logcat | findstr "FATAL"`
- Route to SO analysis for native anti-debug code

**Reference**: `references/unpacking_advanced_tips.md` Section: Frida Detection Bypass

---

### Workflow 6: Crypto Algorithm Restoration

**Trigger**: Need to understand encryption/signing logic.

**Steps**:
1. **Identify crypto boundary**:
   ```powershell
   frida -U -f com.example.app -l scripts\hook\frida_crypto_hook.js
   ```

2. **Captured info**:
   - Algorithm: AES/DES/RSA/MD5/SHA256/HMAC
   - Mode: CBC/ECB/GCM
   - Key (hex): `3f4a9b2c...`
   - IV (hex): `00010203...`
   - Input/Output (hex)

3. **Python port**:
   ```python
   from Crypto.Cipher import AES
   from Crypto.Util.Padding import pad
   
   def encrypt_aes_cbc(data, key, iv):
       cipher = AES.new(key, AES.MODE_CBC, iv)
       return cipher.encrypt(pad(data, AES.block_size))
   
   # Test with captured values
   key = bytes.fromhex("3f4a9b2c...")
   iv = bytes.fromhex("00010203...")
   plaintext = b"test data"
   ciphertext = encrypt_aes_cbc(plaintext, key, iv)
   ```

4. **Validation**:
   - Compare Python output with Frida captured output
   - Match on 3-5 different inputs

**Common patterns**:
- API sign: `MD5(params + timestamp + secret_key)`
- Token: `Base64(AES-CBC(user_id + timestamp, key, iv))`
- Body encrypt: `RSA-OAEP(AES_key) + AES-GCM(body, AES_key)`

**Reference**: `scripts/generate/frida_script_generator.py` (`--type trace`) and the crypto hook script header for output format.

---

## Implementation Contract

### Script Organization

```
scripts/
├── lib/                    # Shared library
│   ├── toolenv.py          # Tool auto-discovery (PATH -> common locations -> extras)
│   └── toolenv_extra.py    # Per-machine candidate paths (editable, optional)
├── check/                  # Environment validation
│   └── check_android_env.py
├── analyze/                # Static analysis
│   └── quick_analyze_apk.py
├── unpack/                 # Unpacking tools
│   ├── dump_dex.py         # Python wrapper (DEX)
│   ├── dump_so.py          # Python wrapper (SO dump + adb pull + SoFixer)
│   └── frida/              # Raw Frida scripts
│       ├── dump_dex_memory.js
│       ├── dump_dex_classloader.js
│       ├── dump_so.js
│       └── list_modules.js
├── hook/                   # Runtime hooks
│   ├── frida_universal_ssl_unpin.js
│   ├── frida_anti_detection.js
│   └── frida_crypto_hook.js
├── capture/                # Traffic capture (mitmproxy)
│   ├── mitm_full_capture.py    # Full-capture addon (jsonl output)
│   └── mitm_run_full.py        # DumpMaster driver (adb reverse chain)
└── generate/               # Script generation
    └── frida_script_generator.py
```

### Tool Path Contract

Never hardcode tool paths in scripts or docs. Resolve through `scripts/lib/toolenv.py`:

```python
# Good — auto-discovery, works on any machine
import toolenv
adb = toolenv.require("adb")             # prints install hint and exits if missing
jadx = toolenv.require_cmd("jadx")       # jar tools expand to [java, -jar, x.jar]

# Bad — machine-specific hardcode
adb = r"E:\...\adb.exe"
```

### Output Contract

All analysis outputs follow this structure:
```
analysis/
├── <package_name>/
│   ├── manifest.json      # Parsed AndroidManifest
│   ├── components.json    # Activities, services, receivers
│   ├── permissions.json   # Requested permissions
│   ├── strings.txt        # Extracted strings
│   ├── dumped_dex/        # Unpacked DEX files
│   ├── dumped_so/         # Unpacked SO files
│   └── frida_logs/        # Hook output logs
```

### Session Preservation

For bootstrap-heavy flows (e.g., app requires login before crypto):
- Keep one ADB session alive
- Preserve Frida attachment across analysis steps
- Save intermediate state (cookies, tokens, session IDs)
- Document refresh mechanisms before claiming replayability

---

## Verification Gate

Do not mark complete until:

- [ ] Prerequisites Gate passed (ADB, root, Frida)
- [ ] Target APK or package identified
- [ ] Workflow route selected based on evidence
- [ ] For unpacking: Dumped files validated (file type, IDA load)
- [ ] For hooks: Console shows expected interception messages
- [ ] For crypto: Python port matches Frida captured output (3+ samples)
- [ ] Sensitive artifacts (keys, tokens) are redacted or kept local
- [ ] Output saved in standard structure under `analysis/<package>/`
- [ ] Any anti-detection bypass claims backed by before/after evidence

---

## Reference Router

Load only references that match current evidence:

### Core References
- `references/tool-paths.md` - Tool requirements, discovery order, and maintainer-machine path reference
- `references/unpacking_guide.md` - DEX/SO unpacking decision tree
- `references/unpacking_advanced_tips.md` - Advanced unpacking techniques (incl. Frida detection bypass section)
- `references/unpacking-tools-guide.md` - 9-way unpacker comparison (BlackDex/FART/frida-dexdump/enma/...)

### Playbooks
- `references/pure-algorithm-methodology.md` - Pure-algorithm restoration: unidbg oracle → isolation matrix → layer diff → pure rewrite (battle-tested on TikTok metasec)
- `references/tiktok-metasec-playbook.md` - TikTok/ByteDance signing stack (Gorgon/Ladon/Argus/x-tt-token), host topology, server risk-control semantics, guest access matrix
- `references/network-capture-methods.md` - 5+ capture methods, SocksDroid chain, QUIC blocking, mitm addon usage
- `references/tool-enma.md` - enma toolkit (25 agents) for game/IL2CPP unpacking
- `references/xposed-lsposed-toolchain.md` - Xposed/LSPosed persistent-hook & unpacking route (hard gate: framework must be installed; reboot required to apply changes)

### Knowledge Base
- `references/github_resources.md` - Curated tools and learning resources
- `references/skill-optimization-summary.md` - Historical optimization backlog (proposals; some paths there are design targets, not shipped files)

---

## Troubleshooting Quick Reference

| Symptom | Likely Cause | Fix |
|---------|--------------|------|
| `adb: device offline` | USB authorization | Re-plug device, accept RSA key |
| `frida-ps -U` fails | Frida server not running | Push & start frida-server |
| App crashes on attach | Anti-Frida detection | Use `frida_anti_detection.js` |
| IDA shows red blocks | SO is packed | Use `dump_so.py` workflow |
| jadx shows obfuscated names | First-gen packer | Use DEX dump workflow |
| SSL pinning blocks proxy | Certificate pinning active | Use `frida_universal_ssl_unpin.js` |
| Crypto hook shows nothing | Native crypto (JNI) | Hook native OpenSSL functions |
| `Error: spawn enoent` | Tool path wrong | Check `references/tool-paths.md` |
| HTTP 200 + 0B empty body | Risk control rejection (NOT necessarily bad signature) | Run baseline control request first; see `references/pure-algorithm-methodology.md` §5 |
| App traffic bypasses proxy | QUIC (UDP 443) ignores HTTP proxy | `iptables -I OUTPUT -p udp --dport 443 -j REJECT`; see `references/network-capture-methods.md` 方案6 |
| mitm running but 0 captures | Stale mitm instance still owns the port | `netstat -ano` find all PIDs on port, taskkill, restart |
| Emulator app stuck at splash | ARM translation cold start (3-5 min on x86 emu) | Poll screenshots; second launch is faster (cache) |

For tool/connectivity diagnostics: `python scripts\check\check_android_env.py --verbose`

---

## Example Usage

### Scenario: Analyze unknown APK for protocol extraction

```powershell
# 1. Quick recon
python scripts\analyze\quick_analyze_apk.py com.mystery.app

# Output shows: Native library libcore.so, permission INTERNET
# Decision: Check if SO is packed

# 2. Try loading SO in IDA
# Result: "Cannot parse ELF" → SO is packed

# 3. Dump and fix SO
python scripts\unpack\dump_so.py com.mystery.app libcore.so

# 4. Load fixed SO in IDA, find crypto calls
# Found: AES_encrypt, HMAC_Init

# 5. Hook crypto to capture keys
frida -U -f com.mystery.app -l scripts\hook\frida_crypto_hook.js

# 6. Trigger network request in app
# Console output:
#   模式: ENCRYPT
#   密钥(Hex): 3f4a9b2c8d7e1f0a...
#   IV(Hex): 00010203...
#   输入(Hex): 7465737464617461 (testdata)
#   输出(Hex): a4f3b2c1d5e6...

# 7. Port to Python
# Write encrypt_aes_cbc() function
# Validate with captured vectors
# Deliver: Python protocol collector
```

---

**Skill Version**: 2.2  
**Last Updated**: 2026-09-02 (v2.2: aligned scripts to documented layout, added toolenv auto-discovery, implemented dump_so.py/list_modules.js, removed dead references)  
**Platform**: Windows 10/11 x64 (scripts are cross-platform; tool discovery covers Linux/macOS locations)  
**Frida Version**: 16.x / 17.x (frida-tools >= 12: spawn auto-resumes, no --no-pause)
