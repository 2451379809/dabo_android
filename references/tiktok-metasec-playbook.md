# TikTok (ByteDance) libmetasec 签名体系作战手册

> 来源: TikTok Android 46.1.15 (versionCode 2024601150) 全纯算攻坚实战
> 状态: Gorgon/Ladon/Argus 100% 纯算还原, 服务器实测通过 (2026-09)
> 完整工程: `E:\project\reverse-code\projects\tiktok-android-46115\`
> 原始研究: `E:\project\tk_app\研究记录_纯算攻坚.md` (92KB) / `PURE_DETAIL_FINAL.md`

---

## 一、目标概况

| 项 | 值 |
|---|---|
| 包名 | com.zhiliaoapp.musically |
| 签名SO | libmetasec_ov.so (ARM64) |
| 网络层 | libsscronet.so (Cronet/TTNet, 默认QUIC) |
| 业务签名头 | x-argus / x-gorgon / x-ladon / x-khronos / x-ss-stub |
| 登录态头 | x-tt-token (服务器签发) |
| mssdk端点 | mssdk-va.tiktokv.com /ms/dyn/task, /ms/get_seed, /sdi/get_token |

## 二、签名算法速查(全部已纯算)

### SIGN_KEY 派生体系
```
SIGN_KEY = b64decode("wC8lD4bMTxmNVwY5jSkqi3QWmrphr/58ugLko7UZgWM=")
AES_KEY  = md5(SIGN_KEY[:16]).digest()     # Argus外层AES-CBC
AES_IV   = md5(SIGN_KEY[16:]).digest()
```

### Gorgon (x-gorgon, 自研流密码)
种子驱动S-Box + nibble交换 + 位反转 + NOT。输入: query的url-encode串、x-ss-stub、时间戳。
seed = (0x4A, 0x10, 0x16, rand, 0x47, 0x6C, flag, rand<<4)。

### Ladon (x-ladon, 自研Feistel)
34轮Feistel, 64bit字, key = md5(nonce + str(aid)).hexdigest()。

### Argus (x-argus) — 核心管线
```
inner = protobuf(fields)                     # 设备/请求信息
padded = pkcs7_pad(inner)
simon_key = sm3(SIGN_KEY + kr + SIGN_KEY)[:32]   # kr=4B随机
enc = Simon-128/256-72轮(padded, simon_key)      # 逐16B块
mask = _mix(kr[2:])
transformed = xor_reverse(mask+mask+enc, mask)
header = 0xEC + env[0:4] + 01 + env[4] + 08 + 18 # 9B固定(388短版)
trailer = ???  ←★见下方双变体
buf = header + transformed[:-2] + trailer
padded_buf = buf + kr[2:] + pad12 + 0x0D
argus = b64(kr[:2] + AES-CBC(padded_buf, AES_KEY, AES_IV))
```

### ★Argus双策略变体(攻坚最关键发现)
| | 388短版 (detail类) | 708长版 (feed/search类) |
|---|---|---|
| trailer | `mask[1::-1]` **直接替换** | `bytes([mask[1]^flag, mask[0]^0x10])` 异或式 |
| header | 固定9B | 变长+flag |
| 字段集 | 精简(无f16/f18/f19/f24/f26/f27, f10=8B零) | 全量(含f24_seed/f32/p1等) |
| 底层原语 | 完全一致 | 完全一致 |

**教训**: 同一加密管线存在"业务区策略变体"。纯算被拒时, 先怀疑
加密层结构(trailer/header), 再怀疑内容层字段。服务器对字段集无强校验,
对 trailer 结构有强校验。

### f13/f14 (请求绑定)
```
f13 = sm3(md5(body).hexdigest().upper())[:6]   # body哈希
f14 = sm3(query_string)[:6]                     # query哈希(实际请求用的query)
```

## 三、服务器响应语义(风控信号字典)

| 响应 | 含义 | 动作 |
|---|---|---|
| HTTP 200 + 大body | 签名+凭证全通过 | — |
| **HTTP 200 + 0B空体** | 请求被风控/缺登录态(非签名错! 签名错通常也是0B, 需对照排除) | 加基准对照定位缺什么 |
| HTTP 403 | 边缘网关拒绝(常缺设备级cookie: odin_tt/msToken) | 补cookie或换host |
| HTTP 455 "origin not match" | 聚合host(aggr16-*)缺 `x-tt-ttnet-origin-host` 头 | 补该头指向api16-normal-useastN |
| status_code:5 "Invalid parameters" | 聚合host要求更完整的App头 | 对照真实抓包补头 |

**判别铁律**: 每组实验必须带一个"已知能过"的基准(如带token请求),
否则0B无法归因。

## 四、Host拓扑(2026-09实测)

```
aggr16-normal.tiktokv.us            App真实聚合入口, 需x-tt-ttnet-origin-host头
api16-normal-useast8.tiktokv.us     可用(部分出口)
api16-normal-useast5.tiktokv.us     可用
api16-va.tiktokv.com                游客App实际路由, 403门槛(cookie)
api16-normal-c-useast1a/2a...       开源爬虫生态host, 多数IDC出口超时不通
```
出口IP与host路由强相关: 换host先测连通性(curl经代理)。

## 五、x-tt-token (登录态凭证)

```
结构: {98B服务器加密块}--{protobuf: 2×32B轮换密钥+"tiktok"}-{IDC编号}.0.1
     (365字符, 服务器只校验第1段)
签发: 登录后服务器响应头 X-Tt-Token 下发, 客户端无法本地伪造加密块
续期: GET /passport/token/beat/v2/ 带旧token+常规签名
      → 响应头x-tt-token下发新token → 即时可用
      轮换约8分钟窗口; 绑定账号不绑定device_id
ToolGuard: 客户端ECDSA(libdelta.so)签名tt-ticket-guard头, 但业务API不强制校验
```

## 六、游客(未登录)访问结论 — 终极矩阵(2026-09-02二次深挖)

| 通道 | 无登录结果 |
|---|---|
| Android App API (multi/v1 detail, feed) | **token是唯一差分**: 游客App原样形态(其UA/完整头/设备身份/US地区参数)+纯算签名, 无token=0B, 仅加token=60KB(同签名对照) |
| Web SSR (视频页HTML内嵌JSON) | **✓完全可用**: 零登录/零签名/零cookie |

### 关键坑: 模拟器中国SIM指纹触发大陆禁服页
未登录App(雷电模拟器)的请求携带 `current_region=CN&residence=CN&mcc_mnc=46000`
+ `x-tt-store-region: cn` → 响应503 body `!!! Unavailable in your area`。
**与出口IP无关**(字节级重放到US可达host同样503; 同IP同host带token正常出数据)。
→ 模拟器测游客行为前先核查query地区参数, 别把大陆禁服页误判成登录墙/风控。

```
Web通道: GET /oembed?url=.../video/{id} 反查作者slug (对占位slug不敏感)
        → GET /@{slug}/video/{id} 页面内 <script id="__UNIVERSAL_DATA_FOR_REHYDRATION__">
        → __DEFAULT_SCOPE__.webapp.video-detail.itemInfo.itemStruct
局限: 统计为四舍五入显示值(26900 vs 精确26420)
```
**判定**: 服务器以token为准, 不做设备强绑定(游客device_id+token照样出数据)。
未验证: 住宅US IP+未登录真机(无环境) — 数据中心IP上游客一律0B。

## 七、unidbg桥接(从SO到纯算的桥)

```
引擎: E:\project\unidbg_metasec (unidbg 0.9.9, Maven, Java 17)
关键: VFS映射OV快照(.m任务程序/.t凭证) → /data/user/0/.../files
     JNI回调桩: prefs(0x1000022/23), sdi+seed注入, 0x100003f token提供
用途: 签名oracle(对照基准) + 字段动态采样 + 加密层逐字节对账
```
用法见 `研究记录_unidbg_detail_2026-09-01.md`。

## 八、QUIC降级(TikTok抓包前置)

Cronet默认QUIC(UDP443)绕过HTTP代理。两条路:
1. iptables: `su -c 'iptables -I OUTPUT -p udp --dport 443 -j REJECT'` → 强制TCP+系统代理
2. 系统CA装mitm证书后 `settings put global http_proxy` 生效

---

**版本**: 1.0 (2026-09-02)
**配套**: `pure-algorithm-methodology.md`(通用方法论) / `network-capture-methods.md`(方案6)
