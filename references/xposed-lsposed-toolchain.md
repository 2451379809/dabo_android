# Xposed / LSPosed 工具链（持久化 Hook 与脱壳路线）

> 定位：Frida 路线的**补充**而非替代。适合"配置一次、长期生效"的持久 Hook/脱壳，
> 以及对 Frida 检测强但对 Xposed 检测弱的目标。
> 核验日期：2026-09-02（未核验条目一律不收录）

---

## ⛔ Prerequisites Gate（先读这一节，再决定是否走此路线）

**规则：设备上没有装 Xposed 系框架，就不要向用户推荐本路线的任何工具**，
直接回退到 Frida 路线（SKILL.md Workflow 2 / unpacking-tools-guide.md）。

### 1. 检测框架是否安装（adb，需 root）

```powershell
# LSPosed（当前主流）。任一命中即视为已安装：
adb shell su -c "ls /data/adb/lspd"                  # LSPosed 数据目录（最可靠）
adb shell su -c "ls /data/adb/modules"               # Magisk 模块列表里找 lspd
adb shell pm path org.lsposed.manager                # Manager 应用（隐藏模式下可能查不到）

# 旧框架：
adb shell pm path de.robv.android.xposed.installer   # 原版 Xposed（Android 8 以下）
adb shell pm path org.meowcat.edxposed.manager       # EdXposed（已停维护）
```

也可直接跑 `python scripts\check\check_android_env.py`（内置 LSPosed 探测段）。

### 2. 生效规则（必须告知用户的运维成本）

| 操作 | 生效条件 |
|------|---------|
| 安装/更新 LSPosed 框架 | **整机重启**（官方 Wiki：Magisk装模块 → Reboot） |
| 启用模块 / 修改作用域（勾选目标应用） | **重启最稳**（dumpDex 官方说明："应用xposed模块后重启"）；至少强制停止目标应用 |
| 更新模块 APK | 重启 |
| 已运行的目标进程 | **不会热生效**——hook 在进程 fork 时注入，进程得重新拉起 |

**推论**：这条路不适合快速迭代调试（每次改动一轮重启），适合"一次配置长期用"；
调试期优先 Frida，定型后可移植为 Xposed 模块做持久化。

### 3. 框架版本约束

- **LSPosed 官方版（24.5k⭐, GPL-3.0）只支持 Android 8.1~14**，需 Magisk 24+（Zygisk 或 Riru 26.1.7+）
- Android 15/16+ 需社区分支（如 JingMatrix/LSPosed_mod、KernelSU 生态的 zygisk_lsposed，标称支持到 17）
- 原版 Xposed / EdXposed 已过时，新项目不要基于它们

---

## Frida vs Xposed 选型

| 维度 | Frida | LSPosed/Xposed |
|------|-------|---------------|
| 即时性 | spawn/attach 即时生效 | 改动需重启（进程重新 fork） |
| 持久性 | 会话级，重启失效 | 开机自动生效 |
| 隐蔽性 | 有端口/进程/线程名指纹，检测手段多 | 应用层可检测特征少（无端口无独立进程；LSPosed 对抗检测比 Frida 容易） |
| 迭代速度 | 秒级改脚本 | 每轮改动重启 |
| Native层 | 原生支持 | 需模块内自行做 JNI/native hook（如 FunELF 的 linker hook） |
| 典型场景 | 调试期、快速验证、Native分析 | 长期监控、重打包签名对抗、Frida被重点检测的目标 |

---

## 脱壳 / Dump 模块（均已核验）

| 模块 | 用途 | 关键事实 | 仓库 |
|------|------|---------|------|
| **dumpDex** | 通用 DEX dump（3.2k⭐） | dump 到 `/data/data/包名/dump`；**暂不支持模拟器**；目标包名不在内置列表时需改 PackerInfo.java 重编译 | https://github.com/WrBug/dumpDex |
| **TinyDumper** | 内存 dump DEX | 输出到 `/data/data/包名/dumper` | https://github.com/TinyHai/TinyDumper |
| **GetDex** | 抽取壳修复 dump（C++） | 能修复**指令被替换成 nop** 的 dex（一代/二代抽取壳） | https://github.com/Mivik/GetDex |
| **RDex** | 二代填充式类抽取加固 | QContainer **容器**方案（应用跑在容器里，非全局注入） | https://github.com/AlienwareHe/RDex |
| **FunELF** | **SO 脱壳**（Xposed 系独有优势） | hook linker 在 SO 加载后 dump+修复，支持无 ELF 头 soinfo 修复；修复内核是 **SoFixer**（与本 skill 的 dump_so.py 同源）；支持 Android 5~13 | https://github.com/Xposed-Modules-Repo/com.zhenxi.funelf |
| **FDex2** | 老牌 DEX dump | 较旧，Android 6+ 可能失效，仅兜底 | https://github.com/AndnixSH/FDex2 |
| **smartdone/dexdump** | 一代壳快速释放 | 轻量即装即用 | https://github.com/smartdone/dexdump |

**与 Frida 路线的分工**：DEX 脱壳优先走 Frida/BlackDex（无重启成本）；
Xposed 路线的独占价值是 **GetDex 的 nop 修复**、**RDex 的容器式二代壳**、**FunELF 的 SO 修复**，
以及目标"检测 Frida 但不检测 Xposed"的场景。

## 辅助模块

| 模块 | 用途 | 关键事实 | 仓库 |
|------|------|---------|------|
| **CorePatch (Core Patch N)** | 禁用签名校验：降级安装、覆盖安装不同签名、装改过的 APK | **LSPosed 官方接管版** 3.3k⭐ GPL-2.0；Android 9+，v4.8 支持 A16 与 V3 签名破解；需 libxposed API 101 | https://github.com/LSPosed/CorePatch |
| 原版 CorePatch | 同上（旧版） | Android 10-14，包名 com.coderstory.toolkit | https://modules.lsposed.org/module/com.coderstory.toolkit |

**用法**：重打包/patch 过的 APK 安装被 `INSTALL_FAILED_VERSION_DOWNGRADE` 或签名校验挡住时，
启用 CorePatch（作用域勾选"系统框架/Android系统"）后重启再装。

## 框架与开发资源

- LSPosed 框架：https://github.com/LSPosed/LSPosed （Android 8.1~14；GPL-3.0）
- LSPlant（LSPosed 底层 ART Hook 库，可独立使用）：https://github.com/LSPosed/LSPlant
- AndroidHiddenApiBypass（模块内调用非SDK接口）：https://github.com/LSPosed/AndroidHiddenApiBypass
- 官方模块仓库（找模块优先来这里搜）：https://modules.lsposed.org/

## 核验记录

- 2026-09-02 核验通过：LSPosed/LSPlant/AndroidHiddenApiBypass、TinyDumper、dumpDex、GetDex、RDex、
  FunELF、FDex2、smartdone/dexdump、CorePatch（官方版+原版）
- **未核验不收录**：JDex2（J5now，查无实据）、LSPilot（me.yun.lspilot，未确认）、SoTap、
  lsposed-universal-template、FridaXposedModule、LSPosed-Mod-Dev.skill —— 使用前自行核验

## 与本 skill 其他文档的关系

- 脱壳工具总对比与升级阶梯：`references/unpacking-tools-guide.md`（本文是其 Xposed 分支的展开）
- Frida 路线（默认路线）：SKILL.md Workflow 2
- 重打包/签名对抗全流程：`references/unpacking_advanced_tips.md`
