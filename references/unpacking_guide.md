# Android应用脱壳完整指南

本文档整合了市面上主流加固方案的脱壳技术和实战流程。

---

## 一、加固识别

### 常见加固特征

| 加固厂商 | 特征文件/字符串 | 识别方法 |
|----------|-----------------|----------|
| **360加固** | `libjiagu*.so` | assets或lib目录 |
| **梆梆加固** | `libsecexe*.so`, `libDexHelper*.so` | lib目录 |
| **腾讯乐固** | `libtup*.so`, `libshella*.so`, `mix.dex` | lib目录和assets |
| **爱加密** | `libexec*.so`, `ijiami.dat` | lib目录和assets |
| **阿里聚安全** | `libmobisec*.so` | lib目录 |
| **梆梆企业版** | `libDexHelper-x.x.x.so` | lib目录，文件名有版本号 |
| **网易易盾** | `libnesec*.so` | lib目录 |

### 快速识别方法

```bash
# 方法1: 解压APK查看
unzip app.apk -d apk_content
ls apk_content/lib/*/
ls apk_content/assets/

# 方法2: 使用查壳工具
# PKID: https://github.com/Martins3024/PKID
# 或在线查壳：https://scan.scan.top

# 方法3: 字符串搜索
strings classes.dex | grep -i "jiagu\|bangcle\|ijiami"
```

---

## 二、脱壳方案选择

### 方案决策树

```
是否为抽取壳（二代壳）？
├─ 是：使用FART/Youpk/BlackDex（需主动调用）
└─ 否：是否为一代壳？
    ├─ 是：使用内存dump方案
    │   ├─ 方案A：frida_dump_dex_memory.js（搜索DEX magic）
    │   ├─ 方案B：frida_dump_dex_classloader.js（Hook加载）
    │   └─ 方案C：Hook OpenCommon/OpenMemory
    └─ 判断不了：都试一遍

如何判断抽取壳？
- jadx打开后method body都是空的
- 或有大量nop指令
```

---

## 三、一代壳脱壳（整体加密）

### 3.1 方案A：内存搜索DEX Magic

**原理**：搜索内存中的 `dex\n035/036/037/038/039` magic头，修复header后导出。

**适用**：360免费版、梆梆标准版、大部分一代壳

**步骤**：

```bash
# 1. 启动Frida Server
adb push frida-server /data/local/tmp/
adb shell chmod 755 /data/local/tmp/frida-server
adb shell su -c "/data/local/tmp/frida-server &"
adb forward tcp:27042 tcp:27042

# 2. 确认设备连接
frida-ps -U

# 3. 先运行反检测脚本（重要！）
frida -U -f com.target.app -l scripts/hook/frida_anti_detection.js

# 4. 重新启动并dump（新终端）
frida -U -f com.target.app -l scripts/unpack/frida/dump_dex_memory.js

# 5. 等待dump完成（脚本会自动搜索并导出）

# 6. 拉取DEX文件
adb shell "su -c 'cp -r /data/data/com.target.app/files/dumped_dex /sdcard/'"
adb pull /sdcard/dumped_dex ./

# 7. 用jadx打开验证
jadx classes_0_*.dex
```

**注意事项**：
- 某些壳会延迟解密，建议在dump前先操作应用触发核心功能
- 如果dump不到，尝试增加延迟时间（脚本中的setTimeout）

---

### 3.2 方案B：Hook ClassLoader

**原理**：Hook DexFile/BaseDexClassLoader/InMemoryDexClassLoader，在DEX加载时导出。

**适用**：动态加载DEX、多DEX、内存加载场景

**步骤**：

```bash
# 类似方案A，但使用不同脚本
frida -U -f com.target.app -l scripts/unpack/frida/dump_dex_classloader.js

# 操作应用，触发DEX加载（如点击登录、进入特定功能）

# 拉取
adb pull /data/data/com.target.app/files/dumped_dex ./
```

**优势**：
- 能捕获运行时动态加载的DEX
- 不依赖内存搜索，更稳定

---

### 3.3 方案C：Hook OpenCommon/OpenMemory

**原理**：Hook `libart.so`中的 `DexFile::OpenCommon` 或 `OpenMemory` 函数，在系统打开DEX时拦截。

**适用**：Android 5.0 - 10（不同版本函数签名不同）

**关键点**：
- Android 5/6：`OpenMemory`
- Android 7+：`OpenCommon`
- Android 8+：需要找正确的重载版本

**符号表参考**（32位 / 64位）：

| Android版本 | 32位符号 | 64位符号 |
|-------------|----------|----------|
| 5.0 | `_ZN3art7DexFile10OpenMemoryEPKhjRKSsPjPS0_` | 同左 |
| 7.0 | `_ZN3art7DexFile10OpenCommonEPKhjS2_jRKNS_10OatDexFileEbbPS0_` | 不同（需查表） |
| 8.0 | `_ZN3art7DexFile10OpenCommonEPKhjS2_jRKNS_10OatDexFileEbbbPS0_NSt3__112basic_stringIcNS6_11char_traitsIcEENS6_9allocatorIcEEEE` | 不同 |

**实现思路**（伪代码）：

```javascript
// 查找符号
var symbols = [
    "_ZN3art7DexFile10OpenCommonE...", // Android 8
    "_ZN3art7DexFile10OpenCommonE...", // Android 7
    // ... 更多版本
];

var openCommon = null;
symbols.forEach(function(sym) {
    var addr = Module.findExportByName("libart.so", sym);
    if (addr) {
        openCommon = addr;
    }
});

if (openCommon) {
    Interceptor.attach(openCommon, {
        onEnter: function(args) {
            // args[1] 是DEX起始地址
            // args[2] 是DEX大小
            this.dexBase = args[1];
            this.dexSize = args[2].toInt32();
        },
        onLeave: function(retval) {
            if (this.dexBase && this.dexSize > 0) {
                // Dump DEX
                var dex = Memory.readByteArray(this.dexBase, this.dexSize);
                // 写入文件...
            }
        }
    });
}
```

---

## 四、二代壳脱壳（抽取壳/指令抽取）

### 特征识别

- jadx打开后method body为空或充满nop
- 代码在运行时才被还原

### 4.1 FART（Function Auto Restore Tool）

**原理**：主动调用所有方法，在执行时dump真实指令，后用dexfixer还原。

**环境要求**：
- 需刷入FART定制ROM（基于AOSP 8.1/10）
- 支持真机刷机（如Pixel系列）

**步骤**：

1. **刷入FART ROM**
   ```bash
   # 下载FART ROM
   # https://github.com/hanbinglengyue/FART
   
   # 解锁Bootloader
   fastboot flashing unlock
   
   # 刷入
   fastboot flash boot FART_boot.img
   fastboot flash system FART_system.img
   fastboot reboot
   ```

2. **安装目标应用**
   ```bash
   adb install target.apk
   ```

3. **触发dump**
   ```bash
   # 方法1：重启应用（推荐）
   adb shell am force-stop com.target.app
   adb shell am start -n com.target.app/.MainActivity
   
   # 方法2：发送特定广播
   adb shell am broadcast -a com.fart.dump
   ```

4. **等待dump完成**
   - dump文件位于 `/data/data/com.target.app/`
   - 包含 `.dex` 和 `_ins.bin`（指令文件）

5. **拉取文件**
   ```bash
   adb pull /data/data/com.target.app/fart ./fart_dump/
   ```

6. **修复DEX**
   ```bash
   # 使用dexfixer
   python dexfixer.py fart_dump/classes.dex fart_dump/classes_ins.bin
   
   # 输出 classes_fixed.dex
   ```

7. **反编译验证**
   ```bash
   jadx classes_fixed.dex
   ```

**注意事项**：
- FART需要等待所有方法都被调用一次，操作应用触发所有功能
- 某些壳会检测FART特征，需要修改ROM去特征

---

### 4.2 BlackDex（免Root方案）

**优势**：不需要Root，适用于Android 5.0 - 13

**原理**：通过辅助功能服务（AccessibilityService）注入目标应用，主动调用并dump。

**步骤**：

1. **安装BlackDex**
   ```bash
   # 下载BlackDex APK
   adb install BlackDex.apk
   ```

2. **开启无障碍服务**
   - 设置 → 无障碍 → BlackDex → 开启

3. **添加目标应用**
   - 打开BlackDex
   - 点击"+"添加目标应用包名

4. **触发dump**
   - 启动目标应用
   - BlackDex会自动注入并dump
   - dump完成后通知栏会提示

5. **导出DEX**
   - BlackDex → 已dump列表 → 点击应用 → 导出
   - 文件保存在 `/sdcard/BlackDex/`

6. **反编译**
   ```bash
   adb pull /sdcard/BlackDex/com.target.app_*.dex ./
   jadx *.dex
   ```

---

## 五、SO库脱壳

### 5.1 加密SO导出

**适用场景**：
- SO被VMP/Ollvm混淆
- Unity IL2CPP游戏
- Native加固

**方法**：使用 `frida_dump_so.js`

```bash
# 运行SO dump脚本
frida -U -f com.target.app -l scripts/unpack/frida/dump_so.js

# 操作应用触发SO加载

# 拉取
adb pull /data/local/tmp/*_dumped_*.so ./
```

### 5.2 SO修复

dump后的SO可能需要修复ELF header。

**工具**：SoFixer / so-fix

```bash
# SoFixer用法
./SoFixer input.so output.so baseaddr

# baseaddr从IDA或logcat中获取
```

---

## 六、完整脱壳流程示例

### 案例：某银行App（梆梆企业版）

**步骤**：

1. **查壳**
   ```bash
   unzip bank.apk -d bank_apk
   ls bank_apk/lib/arm64-v8a/
   # 发现 libDexHelper-x.x.x.so → 梆梆加固
   ```

2. **反检测**
   ```bash
   frida -U -f com.bank.app -l frida_anti_detection.js --no-pause
   ```

3. **内存Dump**
   ```bash
   # 新终端
   frida -U -f com.bank.app -l frida_dump_dex_memory.js --no-pause
   
   # 操作App：登录 → 首页 → 转账界面（触发核心逻辑）
   ```

4. **拉取DEX**
   ```bash
   adb shell "su -c 'cp -r /data/data/com.bank.app/files/dumped_dex /sdcard/'"
   adb pull /sdcard/dumped_dex ./bank_dex/
   ```

5. **反编译**
   ```bash
   jadx bank_dex/classes_0_*.dex
   ```

6. **验证**
   - 检查MainActivity是否有完整代码
   - 搜索关键字（encrypt/sign/api）
   - 如果代码为空 → 可能是二代壳 → 改用FART

---

## 七、常见问题与解决

### Q1: dump不到DEX
**原因**：
- 壳检测到Frida
- DEX还未解密
- 搜索范围不够

**解决**：
1. 先运行反检测脚本
2. 增加dump延迟时间
3. 操作应用触发核心功能
4. 尝试不同dump方案

### Q2: dump后的DEX用jadx打开报错
**原因**：
- DEX header损坏
- 不是完整DEX

**解决**：
1. 检查文件是否以 `dex\n035` 开头
2. 使用十六进制编辑器查看header
3. 尝试用dexfixer修复

### Q3: FART dump后指令仍为空
**原因**：
- 方法未被调用
- 壳检测到FART环境

**解决**：
1. 操作应用触发所有功能
2. 修改FART ROM去特征
3. 使用BlackDex作为替代

### Q4: SO dump后IDA打开报错
**原因**：
- ELF header损坏
- 不完整的SO

**解决**：
1. 使用SoFixer修复
2. 确认dump时机（在SO完全加载后）
3. 检查dump的大小是否合理

---

## 八、脚本使用总结

| 脚本 | 适用场景 | 使用时机 |
|------|----------|----------|
| `frida_anti_detection.js` | 所有场景 | 第一步必须运行 |
| `frida_dump_dex_memory.js` | 一代壳 | 应用启动3秒后自动dump |
| `frida_dump_dex_classloader.js` | 动态加载DEX | 操作应用触发加载 |
| `frida_dump_so.js` | Native加固 | 应用启动5秒后自动dump |
| `frida_crypto_hook.js` | 分析加密逻辑 | 需要时手动运行 |

---

## 九、工具链完整清单

```
必备工具：
├── ADB (Platform Tools)
├── Frida + frida-server
├── jadx / jadx-gui
├── apktool
└── 十六进制编辑器（HxD / 010 Editor）

脱壳工具：
├── frida_dump_dex_memory.js      ← 本项目
├── frida_dump_dex_classloader.js ← 本项目
├── frida_dump_so.js               ← 本项目
├── FART ROM（二代壳）
├── BlackDex（免Root）
└── dexfixer.py（修复工具）

SO修复：
└── SoFixer / so-fix

查壳：
└── PKID / 在线查壳
```

---

**最后提醒**：
- 所有脱壳操作仅用于授权测试、学术研究、安全分析
- 请勿用于破解商业软件或非法用途
- 遵守当地法律法规

---

**版本**: v1.0  
**更新日期**: 2026-08-26
