# Android逆向GitHub资源汇总

本文档整合了GitHub上优秀的Android逆向相关资源。

## 热门工具和框架

### 1. CreditTone/hooker ⭐ 5,285
**描述**: 基于Frida的Android逆向工程工具包
**特点**:
- 用户友好的CLI界面
- 通用Hook脚本
- 自动生成Hook代码
- 内存遍历检测Activities/Services
- 一键SOCKS5代理设置
- Frida JustTrustMe集成
- BoringSSL解pinning

**仓库**: https://github.com/CreditTone/hooker

---

## 学习资源

### 1. HelloHuDi/AndroidReverseNotes
**描述**: Android逆向笔记—从入门到入土

**内容结构**:
- **预备知识**
  - 梦幻三板斧—apktool、dex2jar、jd-gui
  - 进击的gui

- **Xposed入门**（9个实战演练）
  - 神奇的Xposed
  - Hook入门
  - 进击微信系列（获取附近的人、摇骰子作弊、自动发朋友圈等）
  - 微信自动秒抢红包
  - 修改运动步数
  - 消息防撤回

- **其他技术**
  - UiAutomator实战
  - Smali语法
  - AccessibilityService应用

- **脱壳工具**
  - dumpDex
  - drizzleDumper
  - ZjDroid
  - FUPK3

- **重要资源链接**
  - 破解工具包
  - 看雪工具/论坛
  - 吾爱破解
  - 先知社区

**仓库**: https://github.com/HelloHuDi/AndroidReverseNotes

---

### 2. xishandong/Android_reverse
**描述**: 安卓逆向实战合集以及部分笔记

**个人博客**: https://www.xsblog.site/

**实战案例**:

#### 豆瓣签名分析（简单难度）
**分析流程**:
1. 抓包分析，确认加密参数 `_sig`
2. 全局搜索，确认加密位置
3. Hook加密函数，分析加密流程
4. Python实现

**算法**: 
- 请求方式 + URL path + 时间戳用`&`连接
- HMAC-SHA1加密
- Base64编码

#### 得物newSign分析（中等难度）
**特点**:
- 加密在SO层（VMP保护）
- 需要结合Java层和Native层分析

**分析流程**:
1. 抓包分析参数 `newSign`
2. 全局搜索关键字
3. Hook函数定位
4. SO层分析
5. Python改写

**算法**:
- params添加额外参数
- 排序
- AES加密
- MD5加密得到newSign

**仓库**: https://github.com/xishandong/Android_reverse

---

### 3. maddiestone/AndroidAppRE
**描述**: Google安全工程师Maddie Stone的Android应用逆向工程工作坊

**文档结构**:
1. **app_fundamentals.md** - Android应用基础知识
2. **reversing_intro.md** - 逆向工程入门
3. **reversing_dex.md** - DEX文件逆向
4. **reversing_native_libs.md** - Native库逆向（20KB详细指南）
5. **obfuscation.md** - 混淆技术分析
6. **conclusion.md** - 总结

**适合人群**: 
- 安全研究人员
- 漏洞分析人员
- 想要系统学习Android逆向的开发者

**仓库**: https://github.com/maddiestone/AndroidAppRE

---

## Xposed相关项目

### 实用模块

| 项目 | 功能 | 仓库链接 |
|------|------|----------|
| Hardwarecode | 修改硬件信息 | https://github.com/1998lixin/Hardwarecode |
| weixin_change_city | 修改微信地区 | https://github.com/MartinHan01/weixin_change_city |
| XposedWechatHelper | 微信辅助模块 | https://github.com/wuxiaosu/XposedWechatHelper |
| XposedHook | 免重启Xposed模块 | https://github.com/shuihuadx/XposedHook |
| WechatEnhancement | 微信Xposed插件 | https://github.com/firesunCN/WechatEnhancement |
| WeChatMomentExport | 导出朋友圈数据 | https://github.com/Chion82/WeChatMomentExport |
| WechatBotXposed | 微信回复机器人 | https://github.com/Blankeer/WechatBotXposed |
| WechatMagician | 微信操作工具 | https://github.com/Gh0u1L5/WechatMagician |
| WechatSpellbook | 开源微信插件框架 | https://github.com/Gh0u1L5/WechatSpellbook |

---

## AccessibilityService实战项目

| 项目 | 功能 | 仓库链接 |
|------|------|----------|
| WeChatLuckyMoney | 微信抢红包 | https://github.com/geeeeeeeeek/WeChatLuckyMoney |
| DingDingHelper | 钉钉助手 | https://github.com/Justson/DingDingHelper |
| luckymoney | 抢红包工具 | https://github.com/chenjishi/luckymoney |

---

## 脱壳工具

### 现役主力（2026-09-02 核验）

| 工具 | 特点 | 仓库链接 |
|------|------|----------|
| BlackDex | 无Root、Android 5.0-12、秒级 | https://github.com/CodingGay/BlackDex |
| frida-dexdump | pip 一键装、深度搜索 | https://github.com/hluwa/frida-dexdump |
| clsdumper | 9策略聚合 + 自带反Frida绕过 | https://github.com/TheQmaks/clsdumper |
| dexhound | 无注入 /proc/mem 内存雕刻，抗RASP | https://github.com/dPhoeniixx/dexhound |
| eBPFDexDumper | eBPF观测，dump/fix/dumpso/fixso | https://github.com/LLeavesG/eBPFDexDumper |
| FART | ART主动调用（需定制ROM），2.7k⭐ | https://github.com/hanbinglengyue/FART |
| frida_fart | 免刷机版主动调用（root+Frida） | https://github.com/CYRUS-STUDIO/frida_fart |
| FartFixer | FART产物 dex+bin 自动合并修复 | https://github.com/CYRUS-STUDIO/FartFixer |
| RXjadx | 指令修复 + jadx对抗 | https://github.com/langgithub/RXjadx |

### 经典/参考

| 工具 | 特点 | 仓库链接 |
|------|------|----------|
| dumpDex | Xposed模块基础DEX dump | https://github.com/WrBug/dumpDex |
| drizzleDumper | 主动调用脱壳 | https://github.com/DrizzleRisk/drizzleDumper |
| ZjDroid | 经典脱壳工具 | https://github.com/halfkiss/ZjDroid |
| FUPK3 | 强力脱壳 | https://github.com/F8LEFT/FUPK3 |

---

## 反检测 Frida 构建（2026-09-02 核验）

替代官方 frida-server，消除二进制层指纹（字符串/端口/线程名等）。

| 构建 | 特点 | 仓库链接 |
|------|------|----------|
| Florida | 2.2k⭐，跟随上游自动补丁构建，首选入门 | https://github.com/Ylarod/Florida |
| strongR-frida-android | 1.7k⭐，维护主线（CrackerCat原版已老） | https://github.com/hzzheyang/strongR-frida-android |
| rusda | 中文项目，Release直接下载，官方客户端兼容 | https://github.com/taisuii/rusda |
| phantom-frida | ~90补丁覆盖16种检测向量，周构建+随机名 | https://github.com/TheQmaks/phantom-frida |
| fridare | 本地重打包改名工具 v4.x | https://github.com/suifei/fridare |
| frida-stealth | stealth补丁+知识库（作者 AsenOsen） | https://github.com/AsenOsen/frida-stealth |
| undetected-frida | 跟随官方同日发版 | https://github.com/ultrafunkamsterdam/undetected-frida |
| undetected-frida (zer0def) | 融合strongR+Florida补丁，出Magisk/KSU模块 | https://github.com/zer0def/undetected-frida |

**注入方式（免 ptrace）**：

| 工具 | 特点 | 仓库链接 |
|------|------|----------|
| ZygiskFrida | zygisk注入gadget，无ptrace+maps隐藏 | https://github.com/lico-n/ZygiskFrida |
| ksu-frida | KernelSU版+库重映射隐藏 | https://github.com/gorkemgun/ksu-frida |

**已知坑**：
- fridare：设备端 frida-server 与 PC 端 frida-tools 必须使用**完全相同的魔改名**，否则 spawn 卡死
- ZygiskFrida：模拟器上 gadget 运行在 native realm，**只能 hook Java 不能 hook native**（雷电/MuMu 用户注意）

**注意**：网上流传的清单里 `rubenvereecken/frida-stealth`、`nowsecure/frida-trace`、`iGio90/FridaAndroidTracer`、`Haoning199101/android-armor-breaker` 等经核验**不存在**，勿引用。

---

## 抓包工具

### 桌面工具
- **Fiddler**: https://www.telerik.com/download/fiddler
- **Charles**: https://www.charlesproxy.com/latest-release/

### 手机端工具
- **AndroidHttpCapture**: https://github.com/JZ-Darkal/AndroidHttpCapture
- **NetWorkPacketCapture**: https://github.com/huolizhuminh/NetWorkPacketCapture （应用商店：抓包精灵）

---

## 重要社区资源

### 中文社区
- **看雪论坛**: https://bbs.pediy.com/
- **看雪学院**: http://www.pediy.com/
- **看雪工具**: https://tools.pediy.com/
- **吾爱破解**: https://www.52pojie.cn/
- **吾爱漏洞**: http://www.52bug.cn/
- **学逆向**: https://www.xuenixiang.com/
- **逆向未来**: https://www.pd521.com/

### 技术博客
- **先知社区**: https://xz.aliyun.com/
- **黑客与极客 (FreeBuf)**: http://www.freebuf.com/wenku
- **奇虎360技术博客**: http://blogs.360.cn/
- **尼古拉斯·赵四博客**: http://www.wjdiankong.cn/

### Xposed资源
- **Xposed框架中文站**: https://xposed.appkg.com/

---

## 使用建议

### 新手路线
1. 从HelloHuDi/AndroidReverseNotes开始，按顺序学习基础知识
2. 跟着实战案例（豆瓣）动手练习
3. 学习Xposed框架，尝试简单的Hook
4. 阅读maddiestone/AndroidAppRE，建立系统性知识

### 进阶路线
1. 研究CreditTone/hooker的自动化工具实现
2. 学习脱壳技术，分析加固应用
3. 深入Native层逆向，学习IDA + Frida联动
4. 挑战中等难度的实战案例（得物等）

### 工具选择
- **静态分析**: jadx（优先） + apktool
- **动态Hook**: Frida（推荐） 或 Xposed
- **脱壳**: FUPK3 或 frida-dexdump
- **抓包**: Charles（桌面） + 抓包精灵（手机）
- **Native分析**: IDA Pro + Ghidra

---

## 更新日志

- **2026-08-26**: 初始版本，整合GitHub热门资源
- **2026-09-02**: 脱壳工具分"现役主力/经典"两层并逐条核验；新增反检测 Frida 构建表（含已知坑与幻觉条目黑名单）
- 后续将持续补充新的工具和教程（仅收录已核验条目）

---

**免责声明**: 所有工具和资源仅供学习研究使用，请勿用于非法用途。
