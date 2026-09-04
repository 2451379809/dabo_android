# Android DEX/SO Unpacking Tools Comprehensive Guide

本文档涵盖主流Android脱壳与dump工具的完整使用指南，包括安装、原理、使用场景对比和实战工作流。

> **核验说明（2026-09-02）**：本文档条目均经逐一核验。§10-§11 为本轮新增（无注入类 + 多策略类）；
> 未收录未经核验的条目（如 android-armor-breaker 查无此仓库，fart12-lite/TinyDump 等未核验）。

---

## 工具总览

| 工具 | 类型 | 核心技术 | Root需求 | 速度 | 成功率 | 适用场景 |
|------|------|---------|---------|------|--------|---------|
| **BlackDex** | DEX脱壳 | DexFile Cookie | 不需要 | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | 一/二/三代壳快速脱壳 |
| **frida-dexdump** | DEX脱壳 | Frida内存搜索 | 需要 | ⚡⚡ | ⭐⭐⭐⭐ | Frida环境下通用DEX dump |
| **clsdumper** | DEX脱壳 | 9策略聚合+反Frida | 需要 | ⚡⚡ | ⭐⭐⭐⭐⭐ | 带反Frida检测的加固 |
| **FART** | DEX+指令脱壳 | ART主动调用 | 需要定制ROM | ⚡ | ⭐⭐⭐⭐⭐ | 指令抽取壳深度脱壳 |
| **frida_fart** | DEX+指令脱壳 | Frida实现主动调用 | 需要(免刷机) | ⚡ | ⭐⭐⭐⭐ | 抽取壳免刷机方案 |
| **dexhound** | DEX脱壳 | /proc/mem内存雕刻 | 需要 | ⚡⚡ | ⭐⭐⭐⭐ | 强反Frida/RASP目标 |
| **eBPFDexDumper** | DEX+SO脱壳修复 | eBPF观测+vm_readv | 需要 | ⚡⚡ | ⭐⭐⭐⭐ | 强对抗+SO修复 |
| **enma** | 综合dump | 25个Frida agents | 需要 | ⚡⚡ | ⭐⭐⭐⭐⭐ | Unity/UE4游戏、综合审计 |
| **frida_dump** | SO/DEX脱壳 | dlopen hook + ELF修复 | 需要 | ⚡⚡ | ⭐⭐⭐⭐ | Native库提取和修复 |
| **MagiskFrida** | Frida部署 | Magisk模块 | 需要Magisk | N/A | ⭐⭐⭐⭐⭐ | 持久化Frida环境 |
| **rusda (fridaUiTools)** | Frida GUI | PyQt5桌面工具 | 需要 | ⚡⚡⚡ | ⭐⭐⭐⭐ | Frida脚本管理和可视化 |
| **FridaBox** | Gadget注入 | Frida Gadget | 不需要 | ⚡ | ⭐⭐⭐ | 非root设备分析 |
| **freedump** | 快速dump | 内存快照 | 需要 | ⚡⚡⚡ | ⭐⭐⭐ | 快速内存转储 |

---

## 1. BlackDex - 无需Root的通用DEX脱壳神器

### 核心特点
- **最大优势**：无需Root、无需Frida、无需任何环境配置
- **原理**：基于DexFile cookie + VirtualApp容器化技术
- **速度**：数秒完成已安装应用脱壳，未安装应用取决于APK大小
- **兼容性**：Android 5.0-12，支持一代（落地加载）、二代（内存加载）、三代（指令抽取）壳

### 安装

```bash
# 下载BlackDex APK（分32位和64位两个版本）
# GitHub Releases: https://github.com/CodingGay/BlackDex/releases

# 安装对应架构的BlackDex
adb install BlackDex_arm64.apk  # 64位设备
adb install BlackDex_arm.apk    # 32位设备

# 注意：如果在应用列表看不到目标应用，说明架构不匹配，需要安装另一个版本
```

### 使用方法

#### 标准脱壳流程
```bash
1. 打开BlackDex应用
2. 选择"已安装应用"或"未安装应用"
3. 选择目标应用
4. 可选：开启"深度脱壳"模式（指令回填，时间更长）
5. 点击"开始脱壳"
6. 等待完成（几秒到几分钟）
7. 查看结果：/sdcard/BlackDex/<package_name>/
```

#### 深度脱壳模式
```bash
# 深度脱壳会回填被抽取的指令，解决nop问题
# 优点：解决三代壳指令抽取问题
# 缺点：
#   - 时间显著增加（几分钟到十几分钟）
#   - 可能触发应用反检测导致闪退
#   - 不能100%还原（需主动调用才解密的指令无法回填）
```

### 脱壳文件说明
```
/sdcard/BlackDex/<package_name>/
├── hook_xxxxx.dex        # Hook系统API脱壳的DEX（深度脱壳不修复）
└── cookie_xxxxx.dex      # 利用DexFile cookie脱壳的DEX（深度脱壳会修复）
```

### 适用场景
- ✅ **首选工具**：无Root设备的DEX脱壳
- ✅ 快速分析：需要快速获取DEX文件
- ✅ 主流加固：360、梆梆、乐固、爱加密等
- ❌ 不适合：需要同时dump SO和DEX
- ❌ 不适合：强反调试应用（深度脱壳模式可能触发）

### 技术原理
```
1. 容器化运行：在VirtualApp容器内运行目标应用
2. Hook DexFile：Hook DexFile.loadDex等加载函数
3. Cookie提取：从DexFile对象的cookie字段获取DEX内存地址
4. 内存dump：直接读取内存中的完整DEX
5. 指令回填（深度模式）：扫描抽取点，从内存回填真实指令
```

### 与其他工具对比
| 特性 | BlackDex | frida-dexdump | FART |
|------|---------|---------------|------|
| Root需求 | ❌ | ✅ | ✅ (定制ROM) |
| 速度 | 快 | 中等 | 慢 |
| 指令回填 | ✅ (深度模式) | ❌ | ✅ |
| 环境配置 | 零配置 | 需要Frida | 需要刷ROM |
| 成功率 | 极高 | 高 | 极高 |

---

## 2. frida-dexdump - Frida环境通用DEX脱壳工具

### 核心特点
- **最大优势**：命令行工具，易于集成到自动化流程
- **原理**：Frida内存搜索DEX magic + 深度搜索模式修复破损头部
- **兼容性**：所有Frida支持的Android版本
- **状态**：项目已归档（archived），但仍可用

### 安装

```bash
# 使用pip安装
pip3 install frida-dexdump

# 或从源码安装
git clone https://github.com/hluwa/frida-dexdump
cd frida-dexdump
pip3 install -r requirements.txt
python3 setup.py install
```

### 使用方法

#### 基础用法
```bash
# dump前台应用
frida-dexdump -FU

# spawn模式启动并dump
frida-dexdump -U -f com.example.app

# 深度搜索模式（推荐，结果更完整但耗时更长）
frida-dexdump -U -f com.example.app -d

# 指定输出目录
frida-dexdump -U -f com.example.app -o ./my_dex_dump

# 设置启动等待时间（spawn模式默认5秒）
frida-dexdump -U -f com.example.app --sleep 10
```

#### 深度搜索模式
```bash
# 开启深度搜索，修复破损DEX头部
frida-dexdump -U -f com.example.app -d -o ./deep_dump

# 深度搜索会：
# 1. 搜索内存中所有可能的DEX magic（包括破损的）
# 2. 尝试修复DEX头部
# 3. 验证DEX完整性
# 结果更完整，但时间可能增加2-5倍
```

### 输出文件
```
./<appname>/
├── xxxxx_0x12345678.dex    # 每个DEX文件，命名包含内存地址
├── xxxxx_0x23456789.dex
└── ...
```

### 适用场景
- ✅ 有Root权限的设备
- ✅ 已配置Frida环境
- ✅ 需要命令行自动化脚本
- ✅ 需要搜索动态生成的DEX
- ❌ 不适合：无Root设备
- ❌ 不适合：需要指令回填

### 技术原理
```
1. Frida注入目标进程
2. 内存扫描：搜索dex\n035/036/037/038/039 magic头
3. 读取DEX大小：从header解析file_size字段
4. 完整dump：读取从magic头开始的完整DEX
5. 深度模式：尝试修复破损的magic头，扩大搜索范围
```

### 命令行参数
```bash
-F, --frontmost        # 附加到前台应用
-U, --usb              # 使用USB连接设备
-f, --file PACKAGE     # spawn模式启动指定包名
-o, --output DIR       # 输出目录（默认./<appname>/）
-d, --deep-search      # 启用深度搜索模式
--sleep SECONDS        # spawn模式启动等待时间（默认5秒）
```

---

## 3. FART - ART环境指令级深度脱壳方案

### 核心特点
- **最大优势**：唯一能完整还原被抽取函数指令的方案
- **原理**：修改Android系统ART虚拟机，主动调用所有函数触发解密
- **适用壳**：第三代壳（指令抽取壳），如某些高级加固方案
- **要求**：需要刷入FART定制ROM，仅支持Android 6.0/8.0

### 安装

```bash
# 1. 下载FART定制ROM镜像
# 百度网盘：https://pan.baidu.com/s/1c3AyDZ92vVPxt06xwjFO9w
# 提取码：1yzb

# 支持的版本：
#   - Android 6.0 (Marshmallow)
#   - Android 8.0 (Oreo)

# 2. 刷入ROM到测试设备（推荐Pixel系列）
fastboot flash system fart_system_6.0.img
fastboot flash boot fart_boot_6.0.img
fastboot reboot

# 3. 验证FART是否生效
adb logcat | grep FART
# 应该看到FART相关日志
```

### 使用方法

#### ROM版脱壳流程
```bash
# 1. 安装目标APK
adb install target.apk

# 2. 在设置中授予SD卡读写权限（必须！）
# 设置 → 应用 → 目标应用 → 权限 → 存储

# 3. 启动应用（点击桌面图标）
# FART会自动开始主动调用所有函数并dump

# 4. 监控脱壳进度
adb logcat | grep ActivityThread
# 等待出现 "fart run over" 提示

# 5. 提取脱壳文件
adb pull /sdcard/fart/<package_name>/ ./fart_dump/

# 脱壳时间：几分钟到十几分钟（取决于应用大小和函数数量）
```

#### Frida版FART（推荐用于精准控制）
```bash
# 环境要求：
#   - Android 8.0
#   - frida-server 12.8.0
#   - root权限

# 1. 启动frida-server
adb shell "su -c '/data/local/tmp/frida-server &'"

# 2. 使用Frida脚本精准脱壳（frida>=16 无需 --no-pause）
frida -U -f com.example.app -l fart_frida.js

# Frida版优势：
#   - 可指定要dump的类
#   - 可指定要dump的函数
#   - 无需定制ROM（但仍需root）
#   - 更灵活的控制
```

#### frida_fart — 免刷机的主动调用方案（2026-09 核验新增）
```bash
# CYRUS-STUDIO/frida_fart：用 Frida 复刻 FART 主动调用，门槛从"刷定制ROM"降到"root+Frida"
# 核心调用链（注入后自动执行）：
#   hookLoadClassAndInvoke()    # 过滤不需要主动调用的类
#   fartOnDexclassloader()      # 解决局部变量 ClassLoader 枚举不出的问题
#   invokeAllClassloaders()     # 解决非双亲委派关系下动态加载 dex 的脱壳
# 仓库：https://github.com/CYRUS-STUDIO/frida_fart（原版FART仓库内也附带 frida_fart.zip）
# 抽取壳首选起点：先试 frida_fart，不行再上 FART ROM
```

#### 脱壳产物修复链（FART 系必备后续）
```bash
# FART 产物 = *.dex + 每个函数的 *_ins_*.bin（CodeItem），需要合并回填：

# 方案1: FartFixer（CYRUS-STUDIO，推荐，自动化合并）
java -jar FartFixer.jar <dexpath> <binpath> <outpath>
# 仓库：https://github.com/CYRUS-STUDIO/FartFixer（含批量修复脚本）

# 方案2: RXjadx（langgithub）
python2.7 fartpatch.py -d <dexfile> -i <ins_bin>     # 指令修复
java -jar baksmali.jar d <dex> -o out && python modify.py \
  && java -jar smali.jar a out -o modify.dex          # jadx 对抗（修复后仍无法识别时）
# 仓库：https://github.com/langgithub/RXjadx

# 方案3: eBPFDexDumper 的 fix / fixso 子命令（见 §10）
```

### 脱壳文件说明
```
/sdcard/fart/<package_name>/
├── <dex_hash>_<index>.dex           # 完整DEX文件
├── <dex_hash>_<index>_<classid>_ins.bin   # 单个函数的CodeItem二进制
├── <dex_hash>_<index>_<classid>_ins_len.txt # CodeItem长度信息
└── ... (每个类和函数一个bin文件)
```

### 文件用途
```python
# DEX文件：可直接用jadx反编译
# bin文件：需要手动回填到DEX的对应位置

# 回填工具：
# 1. IDA Pro + FART回填插件
# 2. dexfixer工具（自动化回填）
# 3. 手动用010 Editor回填
```

### 适用场景
- ✅ **唯一选择**：遇到三代壳（指令抽取壳）
- ✅ 需要完整还原所有函数指令
- ✅ 有条件刷测试机
- ❌ 不适合：日常快速分析（环境配置成本高）
- ❌ 不适合：生产设备（需要刷机）

### 技术原理
```
1. 修改ART虚拟机：在应用启动时Hook关键函数
2. 主动调用：遍历所有类的所有方法，强制调用
3. 触发解密：调用会触发壳的指令解密逻辑
4. Dump CodeItem：在解密后立即dump函数的CodeItem
5. 保存：将DEX和所有CodeItem保存到SD卡
6. 回填：使用工具将CodeItem回填到DEX对应位置
```

### 与BlackDex深度模式对比
| 特性 | FART | BlackDex深度模式 |
|------|------|----------------|
| 指令还原 | 100%主动调用 | 被动等待执行 |
| 成功率 | 极高 | 高（但依赖执行覆盖） |
| 时间 | 很长（10-30分钟） | 长（5-15分钟） |
| 环境要求 | 定制ROM | 无特殊要求 |
| 适用壳 | 所有三代壳 | 大部分三代壳 |

### 相关资源
- 看雪论坛FART系列文章（原作者"拨云见日"）
- Telegram交流群：https://t.me/+BvJFRSInoo05NTA5
- FART增强版：支持Android 9/10的社区版本

---

## 4. enma - 游戏逆向与综合审计一站式工具

（详见 `tool-enma.md` 完整文档）

### 核心特点
- **最大优势**：唯一同时支持Unity IL2CPP、Mono、UE4的工具
- **25个agents**：覆盖DEX、SO、网络、存储、加密、游戏引擎全部表面
- **Python CLI**：setup → list → dump → analyze → report 完整流程
- **HTML报告**：自动生成可视化分析报告

### 快速使用
```bash
# 安装
git clone https://github.com/ykus4/enma
cd enma
uv sync

# 脱壳流程
uv run enma setup                              # 推送frida-server
uv run enma list                               # 列出应用
uv run enma dump com.example.game -o ./dump    # dump所有artifacts
uv run enma analyze ./dump                     # 分析
uv run enma report ./dump                      # 生成报告
```

### 适用场景
- ✅ **首选**：Unity游戏（IL2CPP/Mono）
- ✅ **首选**：Unreal Engine 4游戏
- ✅ 需要综合审计（一次dump所有内容）
- ✅ 需要网络协议分析（HTTP/WebSocket/Protobuf）
- ❌ 不适合：纯Java应用（太重，用BlackDex更快）

---

## 5. frida_dump - SO库提取与ELF修复工具

### 核心特点
- **最大优势**：自动修复dump的SO文件ELF结构
- **原理**：Hook dlopen + 集成SoFixer修复工具
- **支持**：同时支持SO dump和DEX dump

### 安装

```bash
# 克隆仓库
git clone https://github.com/lasting-yang/frida_dump.git
cd frida_dump

# 依赖：
#   - Python 3.x
#   - frida-tools
#   - adb
#   - root权限
```

### 使用方法

#### dump SO文件
```bash
# dump所有加载的SO模块
python dump_so.py

# dump指定SO文件
python dump_so.py libnative.so

# 输出：
#   - 显示模块基址、大小、路径
#   - 自动保存到设备和PC
#   - 自动推送SoFixer并修复
```

#### dump DEX文件
```bash
# 方法一：ClassLinker.DefineClass hook
frida -U -f com.example.app -l dump_dex.js

# 方法二：dexCache dump（推荐）
frida -UF -l dexCache_dump.js

# 推荐方法二：
#   - 更完整
#   - 兼容性更好
#   - 不依赖类加载时机
```

### 输出文件
```
# SO文件
/data/local/tmp/<module_name>_dumped_<timestamp>.so

# DEX文件
/data/data/<package>/files/dump_<timestamp>.dex
```

### 适用场景
- ✅ **首选**：需要dump和修复SO文件
- ✅ Unity/UE4游戏的libil2cpp.so、libUE4.so
- ✅ 加密SO、VMP/Ollvm混淆的SO
- ✅ 需要IDA分析的Native库
- ❌ 不适合：只需要DEX（用BlackDex更快）

### SoFixer自动修复
```bash
# frida_dump会自动：
# 1. 推送SoFixer到 /data/local/tmp/
# 2. 执行修复：SoFixer -s <dumped_so> -o <fixed_so>
# 3. 拉取修复后的SO到PC

# 手动修复（如果自动失败）：
adb push SoFixer /data/local/tmp/
adb shell "chmod 755 /data/local/tmp/SoFixer"
adb shell "su -c '/data/local/tmp/SoFixer -s /sdcard/dump.so -o /sdcard/fixed.so'"
adb pull /sdcard/fixed.so ./
```

### 技术原理
```
# SO dump：
1. Hook dlopen/android_dlopen_ext
2. 在SO加载时触发回调
3. 读取SO在内存中的完整数据
4. 保存为文件

# ELF修复：
5. 检测ELF头是否完整
6. 修复Section Header Table
7. 修复Program Header Table
8. 确保IDA/Ghidra可以正确加载
```

---

## 6. MagiskFrida - Frida环境持久化部署

### 核心特点
- **最大优势**：开机自动启动frida-server，无需手动操作
- **支持**：Magisk、KernelSU、APatch三种root方案
- **更新**：与Frida官方同步，实时更新

### 安装

```bash
# 1. 下载MagiskFrida模块
# GitHub: https://github.com/ViRb3/magisk-frida/releases
# 下载 MagiskFrida-<version>.zip

# 2. 在Magisk Manager中安装
# Magisk → 模块 → 从本地安装 → 选择MagiskFrida.zip

# 3. 重启设备
adb reboot

# 4. 验证frida-server是否运行
adb shell "ps -A | grep frida"
# 应该看到 frida-server 进程

# 5. 测试连接
frida-ps -U
# 应该能列出所有进程
```

### 支持的架构
- arm64-v8a (64位ARM)
- armeabi-v7a (32位ARM)
- x86_64
- x86

### 适用场景
- ✅ **必备工具**：所有需要Frida的设备
- ✅ 测试机、逆向专用机
- ✅ 需要频繁使用Frida
- ❌ 不适合：临时分析（手动启动更灵活）

### 对比手动启动
| 特性 | MagiskFrida | 手动启动 |
|------|------------|---------|
| 便利性 | 开机即用 | 每次手动 |
| 更新 | 自动同步 | 手动下载 |
| 版本切换 | 需要重刷模块 | 随时切换 |
| 端口自定义 | 固定27042 | 任意指定 |

---

## 7. rusda (fridaUiTools) - Frida可视化管理工具

### 核心特点
- **最大优势**：PyQt5桌面GUI，把Frida脚本管理可视化
- **功能**：连接管理、进程附加、脚本模板、AI辅助、内存搜索
- **定位**：Frida工作台，适合把常用脚本沉淀成本地仓库

### 安装

```bash
# 克隆仓库
git clone https://github.com/dqzg12300/fridaUiTools.git
cd fridaUiTools

# 安装依赖
pip install -r requirements.txt

# 启动
python3 kmainForm.py
```

### 核心功能

#### 1. 连接管理
- USB连接
- WiFi连接
- 自定义端口
- 多设备切换

#### 2. 附加方式
- 附加前台进程
- 附加指定进程
- spawn模式附加

#### 3. 脚本管理
- 内置脚本模板（JNI Trace、Dump Dex、Dump So、SSL Unpin等）
- 自定义脚本保存
- 脚本导入/导出
- 一键启用/禁用

#### 4. 高级功能
- GumTrace工作台：可视化Stalker配置
- 内存搜索：字符串/数值搜索、断点、反汇编
- AI辅助：接入OpenAI兼容API，AI生成脚本、AI分析日志
- Wallbreaker集成：自动反射调用私有方法

### 使用场景
- ✅ **推荐**：Frida脚本很多，需要管理
- ✅ 桌面环境下的Frida操作
- ✅ 团队协作（脚本模板共享）
- ✅ 需要GumTrace可视化配置
- ❌ 不适合：命令行自动化脚本

### AI配置示例
```ini
# 在设置中配置AI接口
[ai]
api_url = https://api.openai.com/v1/chat/completions
apikey = sk-your_api_key
model = gpt-4

# 功能：
#   - AI生成Frida hook脚本
#   - AI分析应用日志
#   - AI提供逆向建议
```

---

## 8. FridaBox - 非Root设备Frida方案

### 核心特点
- **最大优势**：通过Frida Gadget实现非root设备的Frida分析
- **原理**：重打包APK，注入frida-gadget.so
- **限制**：需要重新签名，可能触发签名校验

### 安装与使用

```bash
# FridaBox通常指使用Frida Gadget的一般流程：

# 1. 下载frida-gadget
# https://github.com/frida/frida/releases
# 选择对应架构：frida-gadget-<version>-android-<arch>.so

# 2. 解包APK
apktool d target.apk -o target_unpacked

# 3. 添加frida-gadget.so
cp frida-gadget-16.x.x-android-arm64.so target_unpacked/lib/arm64-v8a/libfrida-gadget.so

# 4. 修改AndroidManifest.xml，添加internet权限
<uses-permission android:name="android.permission.INTERNET"/>

# 5. 配置gadget（可选）
# 在 target_unpacked/lib/arm64-v8a/ 创建 libfrida-gadget.config.so
{
  "interaction": {
    "type": "listen",
    "address": "0.0.0.0",
    "port": 27042
  }
}

# 6. 重新打包
apktool b target_unpacked -o target_gadget.apk

# 7. 签名
# 使用apksigner或jarsigner签名

# 8. 安装并启动
adb install target_gadget.apk

# 9. 连接Frida（启动应用后）
frida -H 127.0.0.1:27042 -n Gadget
```

### 也可使用enma的repack命令
```bash
# enma提供了自动化repack功能
uv run enma repack target.apk -o target_gadget.apk --arch arm64-v8a
```

### 适用场景
- ✅ **唯一选择**：无Root设备需要Frida分析
- ✅ 生产设备临时分析
- ✅ 不能刷机的设备
- ❌ 不适合：有强签名校验的应用
- ❌ 不适合：有反调试/反篡改检测的应用

---

## 9. freedump - 快速内存转储库

### 核心特点
- **最大优势**：专注于快速内存dump，性能优化
- **原理**：直接内存读取，无复杂解析
- **适用**：需要快速获取内存快照

### 安装与使用

```bash
# 通常作为库集成到其他工具
# 或直接使用其Frida脚本

# 基本用法：
frida -U -f com.example.app -l freedump.js

# 功能：
#   - 快速dump整个进程内存
#   - 指定地址范围dump
#   - 最小化解析开销
```

### 适用场景
- ✅ 需要完整内存快照用于离线分析
- ✅ 内存取证
- ✅ 大规模内存搜索前的快照
- ❌ 不适合：只需要DEX/SO（太庞大）

---

## 10. 无注入脱壳 — dexhound / eBPFDexDumper（2026-09 核验新增）

适用场景：目标带强反Frida/RASP，Frida 一附加就闪退。这类工具**完全不注入、不Hook、不ptrace**，
目标进程零感知。

### dexhound — /proc/mem 内存雕刻

- **原理**：root 下遍历 `/proc/<pid>/maps`（跳过系统/框架/其他应用区域），用 `/proc/<pid>/mem`
  读取每个可读区域，扫描 `dex\n0XX` 魔数，校验 header size / endian tag / file size，
  再用 Adler-32 校验并标记 `OK` / `MISMATCH`
- **核心价值**：不 attach、不注入、不向目标加载任何东西——Frida 检测、ptrace 探针、
  hook 扫描全部不触发；配合 Magisk DenyList 过掉开机 root 检测即可
- **要求**：root；目标进程必须已在运行；全 ABI（arm64/armeabi-v7a/x86_64/x86）
- **坑**：只能拿到已解密在内存里的 DEX（壳未解密的拿不到）；产物在设备 `/dump_<pid>_*.dex`
- **仓库**：https://github.com/dPhoeniixx/dexhound

### eBPFDexDumper — eBPF 观测式全工具链

- **四个子命令**：
  - `dump`：基于 eBPF/uprobe 的 DEX 转储（观测加载行为触发）
  - `fix`：修复 dump 出的 DEX
  - `dumpso`：解析 `/proc/<pid>/maps`，把 SO 分散的 r--/r-x/rw- 段合并回连续镜像，
    经 `process_vm_readv` 导出；**还会扫描匿名内存，把首页为 ELF 魔数的自解密库一并导出**
  - `fixso`：修复 dump 出的 SO
- **关键限制（重要）**：eBPF 是只读观测模型，**无法主动调用未执行的方法**——抽取壳里
  "不运行就不解密"的指令拿不到；主动调用仍需注入路线（frida_fart / FART）
- **仓库**：https://github.com/LLeavesG/eBPFDexDumper

### 何时选谁

```
强反Frida，只要DEX且壳会自行解密 → dexhound（更简单直接）
需要DEX+SO一起拿，或需要SO段合并/匿名ELF捕获 → eBPFDexDumper
抽取壳（不运行不解密） → 无注入路线无效，回到 frida_fart / FART
```

---

## 11. clsdumper — 多策略 Frida DEX 聚合（2026-09 核验新增）

- **定位**：frida-dexdump（已归档）的现代替代，一台设备打多种加固
- **9 种 dump 策略聚合**，常用参数：
  ```bash
  clsdumper <package> --spawn              # spawn 模式
  clsdumper <package> --deep-scan          # CDEX 深扫（较慢）
  clsdumper <package> --extract-classes    # 从 dump 出的 DEX 逐类抽取
  clsdumper <package> --no-anti-frida      # 关闭自带的反Frida绕过
  clsdumper --list-apps                    # 列出已安装应用
  ```
- **自带 Anti-Frida 绕过**：对带 Frida 检测的加固开箱即用
- **仓库**：https://github.com/TheQmaks/clsdumper（同作者另有 phantom-frida 魔改构建，见 github_resources）

---

## 工具选择决策树

```
开始分析Android应用
│
├─ 有Root权限吗？
│  ├─ 是 → 需要分析什么？
│  │  ├─ 只需要DEX → BlackDex（最快）或 frida-dexdump / clsdumper
│  │  ├─ 需要DEX+SO → frida_dump 或 enma；SO修复也可用 eBPFDexDumper dumpso
│  │  ├─ Unity/UE4游戏 → enma（唯一选择）
│  │  ├─ 三代壳（指令抽取） → frida_fart（免刷机）→ FART ROM（最完整）→ BlackDex深度模式
│  │  ├─ 强反Frida/一附加就闪退 → 无注入路线：dexhound（/proc/mem）或 eBPFDexDumper（eBPF）
│  │  ├─ 综合审计（全部内容） → enma
│  │  └─ 快速DEX dump → frida-dexdump
│  │
│  └─ 否 → 使用FridaBox（Gadget注入）或 BlackDex
│
├─ 需要持久化Frida环境吗？
│  └─ 是 → MagiskFrida模块
│
├─ 需要Frida脚本管理吗？
│  └─ 是 → rusda (fridaUiTools) 桌面工具
│
└─ 需要内存取证吗？
   └─ 是 → freedump
```

### 企业壳/强对抗升级阶梯（推荐顺序）

```
L0 目标无明显防护 → BlackDex / frida-dexdump（几分钟内出结果）
L1 有Frida检测   → clsdumper（自带anti-frida）+ 魔改frida-server（Florida/strongR/rusda）
L2 附加即闪退(RASP) → 无注入：dexhound / eBPFDexDumper（目标零感知）
L3 抽取壳(不运行不解密) → frida_fart（免刷机主动调用）→ FART ROM → FartFixer/RXjadx修复
L4 VMP/强混淆SO → 见 SKILL.md 黄金法则：绕过混淆不硬刚（Hook输入输出/Unidbg）
```

---

## 典型工作流

### 场景1：快速DEX脱壳（有Root）
```bash
# 方案1：BlackDex（推荐，无需Frida）
1. 安装BlackDex
2. 选择目标应用
3. 点击脱壳
4. 等待几秒
5. 拉取DEX：adb pull /sdcard/BlackDex/...

# 方案2：frida-dexdump
1. frida-dexdump -U -f com.example.app -d
2. 等待完成
3. DEX已保存到当前目录
```

### 场景2：Unity游戏完整dump
```bash
1. 安装MagiskFrida（一次性配置）
2. 安装enma：uv sync
3. 脱壳流程：
   uv run enma setup
   uv run enma dump com.unity.game -o ./unity_dump --spawn
4. 分析：uv run enma analyze ./unity_dump
5. 查看报告：打开 unity_dump/report.html
6. 提取Unity资源：uv run enma unity ./unity_dump -o ./assets
```

### 场景3：三代壳深度脱壳
```bash
# 方案1：BlackDex深度模式（推荐，简单）
1. 安装BlackDex
2. 开启"深度脱壳"选项
3. 等待5-15分钟
4. 检查 cookie_xxxx.dex 是否已修复

# 方案2：FART（最完整，需要测试机）
1. 刷入FART ROM（一次性）
2. 安装应用，授权SD卡权限
3. 启动应用
4. 监控：adb logcat | grep ActivityThread
5. 等待 "fart run over"
6. 拉取：adb pull /sdcard/fart/<pkg>/ ./
7. 使用dexfixer回填指令
```

### 场景4：SO库逆向分析
```bash
1. 使用frida_dump提取并修复SO：
   python dump_so.py libnative.so

2. 拉取修复后的SO：
   adb pull /data/local/tmp/libnative_fixed.so ./

3. 在IDA Pro中分析：
   ida64 libnative_fixed.so

4. 结合Frida动态分析：
   frida -U com.example.app
   # 在REPL中hook native函数
```

### 场景5：非Root设备快速分析
```bash
# 只能用BlackDex或FridaBox

# 方案1：BlackDex（推荐）
1. 安装BlackDex（无需Root）
2. 脱壳目标应用
3. 用jadx分析DEX

# 方案2：FridaBox（需要重打包）
1. enma repack target.apk -o gadget.apk
2. 安装并启动gadget.apk
3. frida -H 127.0.0.1:27042 连接
4. 运行Frida脚本分析
```

---

## 各工具原理深度对比

### DEX脱壳原理对比

| 工具 | 核心技术 | Hook点 | 优点 | 缺点 |
|------|---------|--------|------|------|
| **BlackDex** | DexFile Cookie | VirtualApp容器 + DexFile对象 | 无需Root、速度快 | 容器可能触发反检测 |
| **frida-dexdump** | 内存搜索 | 无Hook，直接搜索magic | 通用性强、无hook痕迹 | 深度搜索慢、可能漏DEX |
| **enma dex_agent** | ClassLoader Hook | BaseDexClassLoader | 精准捕获动态加载 | 需要触发加载才能dump |
| **frida_dump dexCache** | dexCache遍历 | DexFile.mCookie | 完整性好 | 需要DEX已加载 |

### 指令回填原理对比

| 工具 | 回填方式 | 触发机制 | 成功率 | 时间 |
|------|---------|---------|-------|------|
| **FART** | 主动调用所有函数 | 修改ART虚拟机强制调用 | 极高（100%覆盖） | 很长（10-30分钟） |
| **BlackDex深度** | 被动监控执行 | Hook ArtMethod::Invoke | 高（依赖执行覆盖） | 长（5-15分钟） |

### SO dump原理对比

| 工具 | Hook函数 | ELF修复 | 完整性 |
|------|---------|---------|-------|
| **frida_dump** | dlopen + android_dlopen_ext | ✅ 自动（SoFixer） | 高 |
| **enma dlopen_agent** | dlopen/dlsym | ❌ 无 | 中等（需手动修复） |
| **手动Frida脚本** | 自定义 | 取决于脚本 | 取决于脚本 |

---

## 常见问题与解决方案

### Q1: BlackDex脱壳后jadx反编译报错
```
原因：DEX可能不完整或有轻微损坏
解决：
1. 尝试深度脱壳模式
2. 使用dex2jar转jar再反编译
3. 用 enma 或 frida-dexdump 再dump一次对比
```

### Q2: frida-dexdump搜索不到DEX
```
原因：DEX可能在非标准内存区域或使用了非标准magic
解决：
1. 使用 -d 深度搜索模式
2. 增加 --sleep 等待时间
3. 在应用充分运行后再dump（不要立即dump）
```

### Q3: FART脱壳后仍有nop
```
原因：某些指令需要特定条件触发才解密
解决：
1. 检查是否授权SD卡权限
2. 手动触发应用的所有功能
3. 结合BlackDex深度模式再dump一次
4. 使用IDA动态调试确认哪些函数未被调用
```

### Q4: frida_dump修复后SO在IDA中仍报错
```
原因：SoFixer可能修复不完整
解决：
1. 检查Section Header是否完整
2. 使用010 Editor手动修复ELF header
3. 尝试用 enma 再dump一次
4. 如果只是分析代码，可以直接用 base + offset 定位
```

### Q5: MagiskFrida安装后frida-ps连接失败
```
原因：端口冲突或frida-server未正确启动
解决：
1. 检查进程：adb shell "ps -A | grep frida"
2. 检查端口：adb shell "netstat -anp | grep 27042"
3. 手动重启：adb shell "su -c 'killall frida-server && /data/local/tmp/frida-server &'"
4. 检查Magisk模块是否启用
```

### Q6: rusda连接不上设备
```
解决：
1. 确认adb devices能看到设备
2. 确认frida-server在设备上运行
3. 在rusda界面选择正确的设备
4. 尝试切换USB/WiFi连接方式
5. 检查frida版本是否匹配（rusda和frida-server）
```

---

## 工具下载地址汇总

| 工具 | GitHub/Release | 备注 |
|------|---------------|------|
| BlackDex | https://github.com/CodingGay/BlackDex/releases | 下载arm64/arm版本APK |
| frida-dexdump | `pip3 install frida-dexdump` | 已归档但仍可用；活跃替代见 CYRUS-STUDIO/frida_dex_dump |
| clsdumper | https://github.com/TheQmaks/clsdumper | 9策略+反Frida（2026-09核验） |
| dexhound | https://github.com/dPhoeniixx/dexhound | 无注入 /proc/mem（2026-09核验） |
| eBPFDexDumper | https://github.com/LLeavesG/eBPFDexDumper | eBPF dump/fix/dumpso/fixso（2026-09核验） |
| FART | https://github.com/hanbinglengyue/FART | 2.7k⭐ Apache-2.0，ROM见百度网盘 |
| frida_fart | https://github.com/CYRUS-STUDIO/frida_fart | 免刷机主动调用（2026-09核验） |
| FartFixer | https://github.com/CYRUS-STUDIO/FartFixer | FART产物修复合并（2026-09核验） |
| RXjadx | https://github.com/langgithub/RXjadx | 指令修复+jadx对抗（2026-09核验） |
| enma | https://github.com/ykus4/enma | 需要Python 3.12+ |
| frida_dump | https://github.com/lasting-yang/frida_dump | Python脚本 |
| MagiskFrida | https://github.com/ViRb3/magisk-frida/releases | ZIP模块 |
| rusda | https://github.com/dqzg12300/fridaUiTools | 源码，需安装依赖 |
| Frida官方 | https://github.com/frida/frida/releases | frida-server和gadget |
| SoFixer | 通常包含在frida_dump中 | ELF修复工具 |

---

## 推荐工具组合

### 组合1：日常快速分析（有Root）
```
- MagiskFrida（持久化环境）
- BlackDex（快速DEX脱壳）
- rusda（可视化Frida操作）
```

### 组合2：游戏逆向专用
```
- MagiskFrida
- enma（Unity/UE4一站式）
- IDA Pro（Native分析）
```

### 组合3：深度脱壳专用
```
- FART ROM（测试机刷入）
- BlackDex（快速对比）
- dexfixer（指令回填）
```

### 组合4：非Root设备
```
- BlackDex（无需Root的DEX脱壳）
- FridaBox/enma repack（Gadget注入）
- jadx（DEX反编译）
```

### 组合5：自动化流程
```
- frida-dexdump（命令行DEX dump）
- frida_dump（命令行SO dump）
- Python脚本（批量自动化）
```

### 组合6：强对抗加固/企业壳（2026-09 新增）
```
- 魔改 frida-server（Florida / strongR-frida / rusda，见 github_resources.md）
- clsdumper（9策略 + 自带anti-frida）
- 无注入兜底：dexhound（/proc/mem）/ eBPFDexDumper（eBPF，还能修SO）
- 抽取壳收尾：frida_fart（免刷机主动调用）+ FartFixer（指令合并修复）
- 升级顺序见上方"企业壳/强对抗升级阶梯"（L0→L4）
```

---

## 总结

### 最常用的核心工具（必备）
1. **BlackDex** - 90%场景的首选DEX脱壳工具
2. **MagiskFrida** - Root设备必装，省去每次手动启动
3. **enma** - Unity/UE4游戏的唯一完整方案
4. **FART** - 遇到三代壳的最后手段

### 按需使用的工具
- **frida-dexdump**: 命令行自动化场景
- **frida_dump**: 需要SO提取和修复
- **rusda**: 桌面GUI爱好者、脚本管理
- **FridaBox**: 非Root设备的救命稻草
- **freedump**: 内存取证专用

### 学习路径建议
```
入门 → BlackDex + jadx
进阶 → MagiskFrida + frida-dexdump + 基础Frida脚本
高级 → FART + enma + IDA Pro + 自定义Frida脚本
专家 → 修改Android源码 + 编写自己的脱壳工具
```

---

**文档版本**: 1.1  
**最后更新**: 2026-09-02（v1.1: 新增无注入类 dexhound/eBPFDexDumper、多策略 clsdumper、frida_fart/FartFixer 修复链、强对抗升级阶梯；全部条目已核验）  
**维护者**: dabo_android skill  
**参考资源**: 开源项目官方文档和社区实践（未核验条目一律不收录）
