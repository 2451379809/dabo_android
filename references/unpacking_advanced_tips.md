# Android脱壳实战技巧精粹

本文档整合了业界主流脱壳技术的核心要点和实战经验，所有技术均已提炼为原创实现。

---

## 一、脱壳工具对比与选择

### 1.1 主流工具技术对比

| 工具/方案 | 原理 | 适用场景 | 优势 | 劣势 |
|-----------|------|----------|------|------|
| **内存搜索** | 搜索DEX magic头 | 一代壳（整体加密） | 简单快速、兼容性好 | 需要DEX已在内存中 |
| **ClassLoader Hook** | Hook加载函数 | 动态加载、多DEX | 能捕获动态DEX | 需要触发加载时机 |
| **OpenCommon Hook** | Hook底层函数 | Android 5-10 | 在系统层拦截 | 版本适配复杂 |
| **FART** | 主动调用dump | 二代壳（抽取壳） | 能还原抽取指令 | 需要刷ROM |
| **BlackDex** | AccessibilityService | 二代壳，免Root | 无需Root | 兼容性依赖OS版本 |

### 1.2 决策流程图

```
开始分析应用
    ↓
[步骤1] 查壳识别
    ├─ 未加固 → 直接反编译
    ├─ 一代壳 → 继续判断
    └─ 二代壳 → 跳到FART流程
    ↓
[步骤2] 尝试方案优先级（一代壳）
    ①  内存搜索dump（最快）
    ②  ClassLoader Hook（动态）
    ③  OpenCommon Hook（底层）
    ↓
[步骤3] 验证dump结果
    ├─ 代码完整 → 成功✓
    └─ 代码为空 → 二代壳，用FART
```

---

## 二、实战技巧与经验

### 2.1 Frida环境检测绕过

**问题场景**：很多应用检测Frida，导致脱壳失败或应用退出。

**核心检测点**：
1. **进程名检测**：扫描 `/proc/` 目录，查找 `frida-server`
2. **端口检测**：扫描 27042/27043 端口
3. **maps文件**：读取 `/proc/self/maps` 查找 `frida-agent`
4. **ptrace**：使用 `ptrace(PTRACE_TRACEME, 0, 0, 0)` 反调试
5. **D-Bus**：检测 `frida://` 等特征字符串

**绕过策略**：
```javascript
// 1. 重命名frida-server
// 推送前: mv frida-server frida-xxx
adb push frida-xxx /data/local/tmp/

// 2. 修改端口（编译时）
// 或使用 -l 0.0.0.0:端口 参数

// 3. Hook检测函数（已在frida_anti_detection.js实现）
// - strstr/strcmp 字符串检测
// - connect 端口扫描
// - ptrace 反调试
// - fopen /proc/self/maps 读取
```

**高级技巧**：
- MagiskHide隐藏Root
- 修改Frida-gadget特征字符串（重新编译）
- 在内核层面隐藏进程

---

### 2.2 DEX Magic搜索优化

**基础原理**：DEX文件头以 `dex\n03x\0` 开始（x = 5-9）

**优化技巧**：

1. **搜索范围优化**
```javascript
// 只搜索可读内存区域
Process.enumerateRanges('r--').concat(Process.enumerateRanges('rw-'))

// 跳过太小的区域
if (range.size < 0x1000) return;

// 跳过系统内存
if (range.file && range.file.path.startsWith('/system/')) return;
```

2. **Deep Search模式**
```javascript
// 标准搜索：只搜索 "64 65 78 0a 30 33"（dex\n03）
Memory.scan(baseAddr, size, "64 65 78 0a 30 33", {...});

// 深度搜索：搜索每个版本（035/036/037/038/039）
var patterns = [
    "64 65 78 0a 30 33 35 00",  // dex\n035\0
    "64 65 78 0a 30 33 36 00",  // dex\n036\0
    // ...
];
```

3. **DEX完整性验证**
```javascript
// 读取DEX大小（offset 0x20）
var dexSize = Memory.readU32(address.add(0x20));

// 合理性检查
if (dexSize < 0x1000 || dexSize > 100 * 1024 * 1024) {
    return; // 无效DEX
}

// 验证checksum（可选，offset 0x08）
var checksum = Memory.readU32(address.add(0x08));
```

4. **Header修复**
```javascript
// 某些壳会破坏header，需要修复
var dexData = Memory.readByteArray(address, dexSize);
var bytes = new Uint8Array(dexData);

// 修复magic（如果被混淆）
bytes[0] = 0x64; bytes[1] = 0x65; bytes[2] = 0x78;
bytes[3] = 0x0a; bytes[4] = 0x30; bytes[5] = 0x33;
bytes[6] = 0x39; bytes[7] = 0x00; // dex\n039\0

// 重新计算checksum和signature（可选）
```

---

### 2.3 ClassLoader Hook的高级用法

**多ClassLoader场景**：插件化应用、热更新

**枚举所有ClassLoader**：
```javascript
Java.perform(function() {
    Java.enumerateClassLoaders({
        onMatch: function(loader) {
            console.log("[*] 发现ClassLoader:", loader);
            
            // 尝试使用此ClassLoader加载类
            try {
                Java.classFactory.loader = loader;
                var TargetClass = Java.use("com.example.HiddenClass");
                console.log("[+] 在此ClassLoader中找到目标类");
            } catch(e) {}
        },
        onComplete: function() {}
    });
});
```

**指定ClassLoader Hook**：
```javascript
// 保存原ClassLoader
var originalLoader = Java.classFactory.loader;

// 切换到目标ClassLoader
Java.classFactory.loader = targetLoader;

// Hook类
var HiddenClass = Java.use("com.example.HiddenClass");
HiddenClass.method.implementation = function() {...};

// 恢复原ClassLoader
Java.classFactory.loader = originalLoader;
```

---

### 2.4 SO Dump的关键细节

**时机选择**：SO在不同阶段有不同状态
1. **刚加载时**：可能还未解密
2. **运行中**：已解密，是最佳dump时机
3. **卸载后**：内存已清理

**延迟Dump策略**：
```javascript
Interceptor.attach(dlopen_addr, {
    onLeave: function(retval) {
        var soPath = this.soPath;
        
        // 延迟1秒确保SO完全解密
        setTimeout(function() {
            dumpSO(soPath);
        }, 1000);
    }
});
```

**Dump完整性保障**：
```javascript
// 读取SO的段（Segment）信息
var module = Process.findModuleByName(soName);

module.enumerateRanges('r-x').forEach(function(range) {
    console.log("[*] 代码段:", range.base, range.size);
    // dump代码段
});

module.enumerateRanges('rw-').forEach(function(range) {
    console.log("[*] 数据段:", range.base, range.size);
    // dump数据段
});
```

**ELF Header修复**（Dump后）：

常见问题：
- Section header table损坏
- Dynamic段信息丢失
- 重定位信息不完整

修复工具：
```bash
# 使用SoFixer
./SoFixer dumped.so fixed.so 0x基址

# 或手工修复
# 1. 用010 Editor打开
# 2. 修正ELF header中的e_shoff（section header offset）
# 3. 重建.dynsym和.dynstr段
```

---

### 2.5 FART脱壳的关键要点

**环境准备**：
```bash
# 1. 设备要求
- Pixel系列（Google原生Android）
- 或小米（可解锁BL）
- 或一加（开发者友好）

# 2. 刷机前准备
adb reboot bootloader
fastboot flashing unlock
fastboot oem unlock  # 部分设备

# 3. 备份数据
adb backup -apk -shared -all -f backup.ab
```

**FART原理**：
1. 修改 `libart.so`，在方法执行时dump指令
2. dump两个文件：
   - `xxx.dex`：完整DEX（可能有nop）
   - `xxx_ins.bin`：真实指令流
3. 用 `dexfixer.py` 合并修复

**关键配置**：
```bash
# FART会在以下时机dump
# 1. 应用启动时
# 2. 收到特定广播时

# 手动触发dump
adb shell am broadcast -a fart.broadcast.dumpDex --es packageName com.target.app
```

**Dump位置**：
```
/data/data/<包名>/
├── <类名>_<方法名>_ins.bin       # 指令
├── classes.dex                    # 主DEX
└── classes2.dex                   # 多DEX
```

**修复命令**：
```bash
python dexfixer.py classes.dex classes_ins.bin -o fixed.dex
```

**常见问题**：
1. **dump不完整**：未触发所有方法 → 完整操作应用
2. **指令文件缺失**：FART特征被检测 → 修改ROM特征
3. **修复失败**：指令对齐问题 → 手动调整offset

---

## 三、高级脱壳场景

### 3.1 VMP/Ollvm混淆的处理

**特征识别**：
- 大量switch-case（虚拟机dispatcher）
- 控制流平坦化
- 指令替换（add → sub + neg）
- 常量加密

**分析策略**：
1. **不要尝试反混淆**：VMP几乎无法还原
2. **动态追踪**：用Frida Hook关键函数的输入输出
3. **黑盒分析**：把混淆函数当作黑盒，只关心IO

**Hook关键函数**：
```javascript
// 假设VMP保护了加密函数
var baseAddr = Module.findBaseAddress("libnative.so");
var encryptAddr = baseAddr.add(0x12345); // IDA中找到的偏移

Interceptor.attach(encryptAddr, {
    onEnter: function(args) {
        console.log("[VMP] 输入:", hexdump(args[0], {length: 32}));
        this.input = Memory.readByteArray(args[0], 32);
    },
    onLeave: function(retval) {
        console.log("[VMP] 输出:", hexdump(retval, {length: 32}));
        // 收集足够的输入输出对，逆推算法
    }
});
```

---

### 3.2 签名校验绕过

**常见位置**：
1. **Java层**：`PackageManager.getPackageInfo` → `signatures`
2. **Native层**：读取 `/proc/self/maps` 查看APK路径，计算hash

**绕过方法**：

**Java层Hook**：
```javascript
Java.perform(function() {
    var PackageInfo = Java.use('android.content.pm.PackageInfo');
    
    // 替换签名为原始签名
    PackageInfo.signatures.value = [originalSignature];
});
```

**Native层Hook**：
```javascript
// Hook读取signatures的JNI函数
Interceptor.attach(Module.findExportByName("libart.so", "_ZN...GetFieldID"), {
    onEnter: function(args) {
        var fieldName = Memory.readCString(args[2]);
        if (fieldName === "signatures") {
            console.log("[*] 检测到签名读取");
        }
    }
});
```

---

### 3.3 多进程应用的处理

**场景**：应用fork出多个进程，主进程是壳，子进程是真实代码

**识别**：
```bash
adb shell ps | grep com.target.app
# 输出多个进程，看进程名后缀
com.target.app
com.target.app:remote
com.target.app:push
```

**Attach到子进程**：
```bash
# 方法1：Spawn主进程，等待子进程启动后attach
frida -U -f com.target.app --no-pause

# 另一终端
frida-ps -U | grep com.target.app
frida -U -p <子进程PID> -l script.js

# 方法2：使用Frida脚本自动attach子进程
```

```javascript
// 自动attach子进程
Java.perform(function() {
    var Process = Java.use('android.os.Process');
    
    Process.start.implementation = function() {
        console.log("[*] 检测到进程fork");
        var result = this.start.apply(this, arguments);
        
        // TODO: 获取新进程PID并attach
        
        return result;
    };
});
```

---

## 四、Dump后的处理流程

### 4.1 验证Dump结果

**快速检查**：
```bash
# 1. 检查文件大小
ls -lh dumped/*.dex
# 太小（< 1MB）可能有问题

# 2. 检查magic
xxd dumped/classes.dex | head -1
# 应该是：64 65 78 0a 30 33 xx 00

# 3. jadx预览
jadx -d temp dumped/classes.dex
# 打开MainActivity查看是否有代码
```

**完整性验证**：
```python
import struct

def verify_dex(dex_file):
    with open(dex_file, 'rb') as f:
        # 读取header
        magic = f.read(8)
        if not magic.startswith(b'dex\n03'):
            print("❌ Magic错误")
            return False
        
        # 读取checksum
        f.seek(0x08)
        checksum = struct.unpack('<I', f.read(4))[0]
        
        # 读取文件大小
        f.seek(0x20)
        file_size = struct.unpack('<I', f.read(4))[0]
        
        # 验证实际大小
        f.seek(0, 2)  # seek to end
        actual_size = f.tell()
        
        if file_size != actual_size:
            print(f"❌ 大小不匹配: 声称{file_size}, 实际{actual_size}")
            return False
        
        print("✓ DEX基本验证通过")
        return True

verify_dex("dumped/classes.dex")
```

---

### 4.2 多DEX合并

**场景**：dump出多个DEX，需要合并给jadx分析

**方法**：
```bash
# 1. 创建临时APK
mkdir temp_apk
cp dumped/*.dex temp_apk/

# 2. 打包
cd temp_apk
zip -r ../merged.zip .
cd ..
mv merged.zip merged.apk

# 3. jadx打开
jadx merged.apk
```

---

### 4.3 常见错误处理

| 错误现象 | 可能原因 | 解决方法 |
|---------|---------|---------|
| jadx打开报错 | Header损坏 | 用十六进制编辑器修复magic |
| 方法体为空 | 二代壳 | 改用FART |
| 部分类找不到 | 多DEX未全部dump | 延长dump等待时间，操作应用 |
| 代码混淆严重 | ProGuard/R8 | 正常现象，需要结合动态分析 |
| SO加载失败 | ELF损坏 | 使用SoFixer修复 |

---

## 五、实战工作流总结

### 完整脱壳SOP（Standard Operating Procedure）

```
┌─────────────────────────────────────────┐
│ 第1步：环境准备                          │
├─────────────────────────────────────────┤
│ □ Frida-server已启动                    │
│ □ 端口转发已设置                        │
│ □ 反检测脚本已加载                      │
│ □ 设备已Root或使用MagiskHide            │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│ 第2步：查壳识别                          │
├─────────────────────────────────────────┤
│ □ 解压APK查看lib目录                    │
│ □ 使用PKID或在线工具                    │
│ □ 判断壳类型（一代/二代）               │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│ 第3步：选择脱壳方案                      │
├─────────────────────────────────────────┤
│ 一代壳 → 内存dump或ClassLoader Hook    │
│ 二代壳 → FART或BlackDex                │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│ 第4步：执行脱壳                          │
├─────────────────────────────────────────┤
│ □ 启动应用                              │
│ □ 操作触发核心功能                      │
│ □ 等待dump完成                          │
│ □ 拉取文件到电脑                        │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│ 第5步：验证与修复                        │
├─────────────────────────────────────────┤
│ □ 检查文件大小和magic                   │
│ □ jadx预览代码                          │
│ □ 如需修复，使用dexfixer                │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│ 第6步：反编译分析                        │
├─────────────────────────────────────────┤
│ □ jadx查看Java代码                      │
│ □ apktool查看资源和Smali                │
│ □ 搜索关键字                            │
└─────────────────────────────────────────┘
```

---

## 六、常用命令速查

```bash
# === Frida环境 ===
# 启动server
adb push frida-server /data/local/tmp/
adb shell "chmod 755 /data/local/tmp/frida-server"
adb shell "su -c '/data/local/tmp/frida-server &'"
adb forward tcp:27042 tcp:27042

# === 脱壳 ===
# 内存dump
frida -U -f com.target.app -l frida_dump_dex_memory.js --no-pause

# ClassLoader Hook
frida -U -f com.target.app -l frida_dump_dex_classloader.js --no-pause

# SO dump
frida -U -f com.target.app -l frida_dump_so.js --no-pause

# === 拉取文件 ===
# DEX
adb shell "su -c 'cp -r /data/data/com.target.app/files/dumped_dex /sdcard/'"
adb pull /sdcard/dumped_dex ./

# SO
adb pull /data/local/tmp/*_dumped_*.so ./

# === 验证 ===
# 查看DEX header
xxd classes.dex | head -1

# 快速反编译
jadx -d output classes.dex
```

---

**最后提醒**：
- 脱壳前务必先运行反检测脚本
- dump后立即验证，不要等分析时才发现问题
- 保留原始dump文件，修复失败可重试
- 某些壳需要多次尝试不同方案

---

**文档版本**: v1.0  
**更新日期**: 2026-08-26  
**技术来源**: 综合业界主流方案提炼
