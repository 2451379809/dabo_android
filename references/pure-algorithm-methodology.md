# 纯算还原方法论 — 从SO/unidbg到100%纯算法

> 来源: TikTok libmetasec_ov.so 全纯算攻坚(Gorgon/Ladon/Argus)实战总结
> 适用: 任何"签名算法在SO里, 目标是脱离设备/模拟器纯Python复现"的场景
> 核心思想: **SO是oracle不是黑盒 — 用它生成样本, 逐层对账, 变体穷举**

---

## 一、总路线图

```
阶段0 真实抓包               阶段1 SO oracle          阶段2 逐层对账        阶段3 纯算替换
──────────────             ─────────────           ─────────────       ─────────────
h2/mitm抓真实请求    →      unidbg跑同SO       →     解密SO产物        →   纯算组件逐个替换
(拿到: 请求全貌/凭证)        生成任意输入的签名        与纯算实现对比         SO实现隔离对照
                           (样本无限+可控)          (字节级diff)          定位致命差异
```

**为什么必须先有unidbg oracle**: 真机抓包样本有限且不可控输入;
unidbg可以任意喂参数采样, 是逆向加密层的显微镜。

## 二、组件隔离矩阵(定位"被拒"的归因)

当"SO签名能过、纯算签名被拒"时, 逐个组件交叉替换:

```
[SO全套]           → 200 数据      (基准: SO实现一定对)
[SO签A + 纯算GL]   → 200 数据      (纯算Gorgon/Ladon没问题)
[纯算A + SO签GL]   → 200 0B        (纯算Argus被拒 → 锁定Argus)
[SO字段值+纯算加密] → 200 0B        (字段没问题 → 锁定加密层!)
```

要点:
1. **每行只变一个组件**, 结论才有归因力
2. "复制SO的字段值+纯算加密管线仍被拒" 是锁定加密层的决定性证据
3. 反过来("旧字段+新加密=通过")可证明内容层无强校验

## 三、逐层对账表(加密管线定位法)

把密文按管线分层, 每层独立比对。以Argus为例:

| 层 | 检查方法 | 结论类型 |
|---|---|---|
| 外层封装 | b64长度/前缀随机字节数 | 结构差异 |
| AES层 | key/iv推导, CBC块数 | 原语差异 |
| header | 固定长度? 含flag? 结构变体 | ★策略变体高发区 |
| 分组密码 | 轮数/字长/key schedule | 原语差异 |
| 变换层 | mask推导/XOR/反转方向 | 细节差异 |
| **trailer/尾部** | 替换式还是异或式? | ★最易踩坑(见下) |
| padding | PKCS7块/尾部magic | off-by-one |

**黄金验证**: 用纯算原语重建SO的输出, 追求 `rebuilt == SO` 字节级全等。
能全等 ⇒ 原语全对; 不能全等 ⇒ diff的第一字节就是问题层。

### 血泪案例: trailer结构变体
- 纯算(708长版): `trailer = mask[1]^flag, mask[0]^0x10` (异或式)
- SO(388短版): `trailer = mask[1::-1]` (直接替换!)
- 差2字节, 服务器直接拒绝。**同一SO对不同业务接口输出不同策略变体** —
  采样时必须按接口分类, 不要混。

## 四、决定性实验设计原则

1. **基准先行**: 每组实验必须有一个已知能过的对照(如带token的SO签名请求)。
   没有基准的"0B"无法归因(签名错? 缺凭证? IP风控? host不对?)。
2. **单变量**: 一组只改一个维度(host/token/设备身份/header/端点)。
3. **正反双向**: 验证"服务器认token不认设备"= 游客device_id+token(过) + 账号device+无token(拒)。
4. **穷举维度**: host家族 × 登录态 × 设备身份 × header变体 × 端点变体, 列矩阵跑。

## 五、空体(0B)取证清单

App API返回200+0B时按序排查:
```
1. 基准(已知好请求)还过吗?        → 过: 是变量问题; 不过: IP/凭证过期
2. 换成SO/unidbg签名还0B吗?       → 过: 纯算签名问题; 不过: 凭证/登录态问题
3. query里的device_id/iid与签名内的一致吗? (可能不校验, 但要记录)
4. host路由: 出口IP对哪些host可达? (curl -x proxy逐个测)
5. 缺头? 对照真实抓包逐头补(x-tt-ttnet-origin-host等)
6. 缺设备级cookie? (odin_tt/msToken, 从MITM Set-Cookie流取)
```

## 六、游客/免登录通道排查范式

App API拒游客 ≠ 数据拿不到。按优先级:
```
1. Web SSR: 业务页HTML内嵌JSON (TikTok: __UNIVERSAL_DATA_FOR_REHYDRATION__)
   — 零签名零cookie, 但统计可能是舍入值
2. 公开oEmbed类接口: 常用来反查slug/元数据
3. ttwid类设备级web cookie: 公开注册接口可领 (TikTok: ttwid.bytedance.com)
4. Web API+web签名(X-Bogus/a_bogus): 需另逆一套, 独立于App签名
5. App API+游客设备: 最后才试(常被风控)
```

## 七、Windows实战环境要点

1. **shell是cmd不是bash**: for循环/heredoc语法不同; 复杂逻辑全部写成.py文件再跑
   (inline python多行引号在cmd下必炸)。
2. **HTTP客户端用 curl_cffi** (`impersonate="chrome"`): TLS指纹过Cloudflare类检测,
   requests裸TLS常被拒。代理写法: `proxies={"http": proxy, "https": proxy}`。
3. **多套adb互杀**: LDPlayer/MuMu/通用platform-tools的adb server互杀,
   固定用一套路径(如 D:\leidian\LDPlayer9\adb.exe)。
4. **模拟器跑ARM App极慢**: LDPlayer(x86)转译arm64 App冷启动3-5分钟,
   重启后转译缓存生效会快; 等待是常态, 截屏轮询确认状态。
5. **adb reverse会丢**: adb kill-server/设备offline后reverse隧道消失,
   每次重连后 `adb reverse --list` 核查。

## 八、验证门槛(Definition of Done)

纯算交付前:
- [ ] 与SO/unidbg输出字节级全等(至少3组不同输入) 或 服务器实测通过
- [ ] 多样本(不同时间/随机数)稳定通过
- [ ] 不同业务端点各自验证(注意策略变体!)
- [ ] 失败路径可诊断(带基准对照的错误归因)
- [ ] 依赖清单明确(凭证/代理/一次性人工步骤)

---

**版本**: 1.0 (2026-09-02)
**配套**: `tiktok-metasec-playbook.md`(该方法的完整实战样本)
