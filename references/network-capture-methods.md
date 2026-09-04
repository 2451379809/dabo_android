# Android Network Capture Methods - Self-Written Scripts


> **注意（v2.2）**：文中 `okhttp_logger_basic/advanced.js`、`httpurlconnection_logger.js`、
> `ssl_keylog_exporter.js`、`socket_native_hook.js`、`run_capture.py` 为**设计稿，尚未随本 skill 发布**。
> 当前实际可用的抓取资产：`scripts/capture/mitm_full_capture.py`（mitmproxy addon）、
> `scripts/capture/mitm_run_full.py`（驱动）、`scripts/hook/frida_universal_ssl_unpin.js`（配合 Charles/mitm）。

**核心理念**：完全自己编写Frida脚本抓包，不依赖Charles/Fiddler/mitmproxy等第三方代理工具。

---

## 一、方案对比与选择

### 1.1 四大主流方案

| 方案 | 原理 | 覆盖范围 | 明文/密文 | 复杂度 | 推荐场景 |
|------|------|---------|----------|--------|---------|
| **Hook OkHttp** | 拦截 RealCall.execute/enqueue | OkHttp库应用 | ✅ 明文 | ⭐ 简单 | 90%商业App首选 |
| **Hook HttpURLConnection** | 拦截 Java 原生HTTP API | 使用标准库的App | ✅ 明文 | ⭐ 简单 | 老旧App或自研网络层 |
| **SSL Keylog + tcpdump** | 导出TLS会话密钥，系统层抓包 | 所有HTTPS流量 | ✅ 可解密 | ⭐⭐ 中等 | 通杀方案，包括Native层 |
| **Hook Socket (send/recv)** | 拦截 libc.so 底层Socket函数 | 所有TCP流量 | ❌ 密文 | ⭐⭐⭐ 复杂 | 非标准协议或自定义加密 |
| **综合方案 (friTap类)** | SSL_read/write + Keylog + Java层 | 全覆盖 | ✅ 明文 | ⭐⭐⭐ 复杂 | 专业渗透测试 |

### 1.2 决策树

```
开始抓包
│
├─ App使用OkHttp？（90%商业App）
│  └─ 是 → 方案1: Hook OkHttp（最简单，5分钟搞定）
│
├─ 需要抓所有HTTPS？（包括Native层）
│  └─ 是 → 方案3: SSL Keylog + tcpdump（通杀）
│
├─ App使用HttpURLConnection？
│  └─ 是 → 方案2: Hook HttpURLConnection
│
├─ 自定义协议或WebSocket？
│  └─ 是 → 方案1+2组合 或 方案4: Socket层
│
└─ 需要专业流量分析？
   └─ 是 → 方案5: 综合方案（参考friTap）
```

---

## 二、方案1: Hook OkHttp（推荐入门）

### 2.1 原理

OkHttp是Android最流行的HTTP客户端库，Hook其关键类即可拿到明文请求/响应：

**Hook点选择**：
```
okhttp3.RealCall.execute()      # 同步请求
okhttp3.RealCall.enqueue()      # 异步请求
或
okhttp3.Interceptor             # 拦截器注入（更优雅）
```

### 2.2 完整可运行脚本

#### 基础版：打印到控制台

```javascript
/**
 * OkHttp Logger - 基础版
 * 支持：OkHttp 3.x/4.x
 * 功能：打印请求方法、URL、Headers、Body（含JSON/Form）
 */

function hookOkHttp() {
    Java.perform(function() {
        console.log("[*] Starting OkHttp Hook...");
        
        try {
            // Hook RealCall.execute (同步请求)
            var RealCall = Java.use("okhttp3.RealCall");
            
            RealCall.execute.implementation = function() {
                var request = this.request();
                
                console.log("\n╔═══════════════════════════════════════════════════════");
                console.log("║ [REQUEST] " + request.method() + " " + request.url().toString());
                console.log("╠═══════════════════════════════════════════════════════");
                
                // Headers
                var headers = request.headers();
                console.log("║ Headers:");
                for (var i = 0; i < headers.size(); i++) {
                    console.log("║   " + headers.name(i) + ": " + headers.value(i));
                }
                
                // Request Body
                var requestBody = request.body();
                if (requestBody != null) {
                    try {
                        var Buffer = Java.use("okio.Buffer");
                        var buffer = Buffer.$new();
                        requestBody.writeTo(buffer);
                        var body = buffer.readUtf8();
                        console.log("║ Body: " + body);
                    } catch (e) {
                        console.log("║ Body: [Binary or Stream]");
                    }
                }
                
                // 执行原始请求
                var response = this.execute();
                
                console.log("╠═══════════════════════════════════════════════════════");
                console.log("║ [RESPONSE] " + response.code() + " " + response.message());
                console.log("╠═══════════════════════════════════════════════════════");
                
                // Response Headers
                var respHeaders = response.headers();
                console.log("║ Headers:");
                for (var i = 0; i < respHeaders.size(); i++) {
                    console.log("║   " + respHeaders.name(i) + ": " + respHeaders.value(i));
                }
                
                // Response Body (需要peek，避免消费掉)
                try {
                    var responseBody = response.body();
                    var source = responseBody.source();
                    source.request(Java.use("java.lang.Long").MAX_VALUE.value);
                    var buffer = source.buffer();
                    var bodyString = buffer.clone().readUtf8();
                    console.log("║ Body: " + (bodyString.length > 1000 ? bodyString.substring(0, 1000) + "..." : bodyString));
                } catch (e) {
                    console.log("║ Body: [Cannot read]");
                }
                
                console.log("╚═══════════════════════════════════════════════════════\n");
                
                return response;
            };
            
            // Hook RealCall.enqueue (异步请求)
            RealCall.enqueue.implementation = function(callback) {
                var request = this.request();
                console.log("[ASYNC REQUEST] " + request.method() + " " + request.url().toString());
                return this.enqueue(callback);
            };
            
            console.log("[✓] OkHttp Hook installed successfully!");
            
        } catch (e) {
            console.log("[✗] OkHttp Hook failed: " + e);
        }
    });
}

setImmediate(hookOkHttp);
```

**使用方法**：
```bash
# 保存为 okhttp_logger.js
frida -U -f com.example.app -l okhttp_logger.js --no-pause

# 或附加到运行中的进程
frida -U com.example.app -l okhttp_logger.js
```

#### 进阶版：保存到文件

```javascript
/**
 * OkHttp Logger - 进阶版
 * 新增功能：保存请求到文件、支持混淆、JSON美化、请求统计
 */

function hookOkHttpAdvanced() {
    Java.perform(function() {
        var requestCount = 0;
        var outputPath = "/sdcard/okhttp_logs/";
        
        // 创建输出目录
        var File = Java.use("java.io.File");
        var dir = File.$new(outputPath);
        if (!dir.exists()) {
            dir.mkdirs();
        }
        
        // 通用写文件函数
        function saveToFile(filename, content) {
            try {
                var FileWriter = Java.use("java.io.FileWriter");
                var writer = FileWriter.$new(outputPath + filename, true);
                writer.write(content + "\n\n" + "=".repeat(80) + "\n\n");
                writer.close();
            } catch (e) {
                console.log("[!] Save error: " + e);
            }
        }
        
        // JSON美化
        function prettyJSON(str) {
            try {
                var obj = JSON.parse(str);
                return JSON.stringify(obj, null, 2);
            } catch (e) {
                return str;
            }
        }
        
        // 尝试兼容混淆的OkHttp
        function findOkHttpClass() {
            var candidates = [
                "okhttp3.RealCall",
                "okhttp3.internal.connection.RealCall",
                "com.squareup.okhttp3.RealCall"
            ];
            
            for (var i = 0; i < candidates.length; i++) {
                try {
                    return Java.use(candidates[i]);
                } catch (e) {}
            }
            
            // 尝试搜索混淆后的类
            console.log("[!] Standard OkHttp not found, searching obfuscated classes...");
            var classes = Java.enumerateLoadedClassesSync();
            for (var i = 0; i < classes.length; i++) {
                if (classes[i].indexOf("RealCall") > -1 || classes[i].indexOf("okhttp") > -1) {
                    try {
                        return Java.use(classes[i]);
                    } catch (e) {}
                }
            }
            
            return null;
        }
        
        var RealCall = findOkHttpClass();
        if (!RealCall) {
            console.log("[✗] OkHttp not found in this app!");
            return;
        }
        
        RealCall.execute.implementation = function() {
            requestCount++;
            var timestamp = new Date().toISOString().replace(/[:.]/g, "-");
            var reqId = timestamp + "_" + requestCount;
            
            var request = this.request();
            var method = request.method();
            var url = request.url().toString();
            
            // 构建日志
            var logContent = "REQUEST ID: " + reqId + "\n";
            logContent += "Time: " + new Date().toLocaleString() + "\n";
            logContent += "Method: " + method + "\n";
            logContent += "URL: " + url + "\n\n";
            
            // Headers
            logContent += "--- REQUEST HEADERS ---\n";
            var headers = request.headers();
            for (var i = 0; i < headers.size(); i++) {
                logContent += headers.name(i) + ": " + headers.value(i) + "\n";
            }
            
            // Request Body
            var requestBody = request.body();
            if (requestBody != null) {
                try {
                    var Buffer = Java.use("okio.Buffer");
                    var buffer = Buffer.$new();
                    requestBody.writeTo(buffer);
                    var bodyStr = buffer.readUtf8();
                    logContent += "\n--- REQUEST BODY ---\n";
                    logContent += prettyJSON(bodyStr);
                } catch (e) {
                    logContent += "\n--- REQUEST BODY ---\n[Binary or unreadable]\n";
                }
            }
            
            // 执行请求
            var response = this.execute();
            
            // Response
            logContent += "\n\n--- RESPONSE ---\n";
            logContent += "Status: " + response.code() + " " + response.message() + "\n\n";
            
            // Response Headers
            logContent += "--- RESPONSE HEADERS ---\n";
            var respHeaders = response.headers();
            for (var i = 0; i < respHeaders.size(); i++) {
                logContent += respHeaders.name(i) + ": " + respHeaders.value(i) + "\n";
            }
            
            // Response Body
            try {
                var responseBody = response.body();
                var source = responseBody.source();
                source.request(Java.use("java.lang.Long").MAX_VALUE.value);
                var buffer = source.buffer();
                var bodyStr = buffer.clone().readUtf8();
                logContent += "\n--- RESPONSE BODY ---\n";
                logContent += prettyJSON(bodyStr);
            } catch (e) {
                logContent += "\n--- RESPONSE BODY ---\n[Cannot read]\n";
            }
            
            // 保存到文件
            saveToFile("okhttp_" + reqId + ".log", logContent);
            
            // 控制台简短输出
            console.log("[" + requestCount + "] " + method + " " + url + " → " + response.code());
            
            return response;
        };
        
        console.log("[✓] Advanced OkHttp Hook installed!");
        console.log("[✓] Logs will be saved to: " + outputPath);
    });
}

setImmediate(hookOkHttpAdvanced);
```

**使用方法**：
```bash
frida -U -f com.example.app -l okhttp_logger_advanced.js --no-pause

# 拉取日志
adb pull /sdcard/okhttp_logs/ ./network_logs/
```

### 2.3 混淆对抗

某些App会混淆OkHttp类名，识别方法：

```javascript
// 搜索混淆后的OkHttp类
Java.perform(function() {
    Java.enumerateLoadedClasses({
        onMatch: function(className) {
            if (className.indexOf("okhttp") > -1 || 
                className.indexOf("RealCall") > -1 ||
                className.indexOf("Interceptor") > -1) {
                console.log("Found: " + className);
            }
        },
        onComplete: function() {}
    });
});
```

**常见混淆类名特征**：
- `com.a.b.c.d` (完全混淆)
- `okhttp3.a.b.RealCall` (部分混淆)
- `o.okhttp3.RealCall` (命名空间混淆)

---

## 三、方案2: Hook HttpURLConnection

### 3.1 原理

HttpURLConnection是Java标准库的HTTP客户端，老旧App或自研网络层会用。

**Hook点**：
```
java.net.HttpURLConnection.getInputStream()
java.net.HttpURLConnection.getOutputStream()
javax.net.ssl.HttpsURLConnection
```

### 3.2 完整脚本

```javascript
/**
 * HttpURLConnection Logger
 * 支持：HttpURLConnection / HttpsURLConnection
 */

function hookHttpURLConnection() {
    Java.perform(function() {
        console.log("[*] Hooking HttpURLConnection...");
        
        var HttpURLConnection = Java.use("java.net.HttpURLConnection");
        var HttpsURLConnection = Java.use("javax.net.ssl.HttpsURLConnection");
        
        // Hook connect
        HttpURLConnection.connect.implementation = function() {
            var url = this.getURL().toString();
            var method = this.getRequestMethod();
            
            console.log("\n[HttpURLConnection] " + method + " " + url);
            
            // Request Headers
            var headerFields = this.getRequestProperties();
            var keys = headerFields.keySet().iterator();
            console.log("Request Headers:");
            while (keys.hasNext()) {
                var key = keys.next();
                console.log("  " + key + ": " + headerFields.get(key));
            }
            
            return this.connect();
        };
        
        // Hook getInputStream (读响应)
        HttpURLConnection.getInputStream.overload().implementation = function() {
            var stream = this.getInputStream();
            var url = this.getURL().toString();
            
            console.log("[Response] " + this.getResponseCode() + " for " + url);
            
            // Response Headers
            var headerFields = this.getHeaderFields();
            if (headerFields != null) {
                var keys = headerFields.keySet().iterator();
                console.log("Response Headers:");
                while (keys.hasNext()) {
                    var key = keys.next();
                    if (key != null) {
                        console.log("  " + key + ": " + headerFields.get(key));
                    }
                }
            }
            
            return stream;
        };
        
        console.log("[✓] HttpURLConnection Hook installed!");
    });
}

setImmediate(hookHttpURLConnection);
```

---

## 四、方案3: SSL Keylog + tcpdump（通杀方案）

### 4.1 原理

通过Hook OpenSSL的`SSL_CTX_set_keylog_callback`导出TLS会话密钥，配合系统层tcpdump抓包，最后用Wireshark解密。

**优势**：
- ✅ 覆盖所有HTTPS流量（Java层、Native层、系统层）
- ✅ 不修改App代码，纯Hook
- ✅ 抓取完整TCP流

### 4.2 完整脚本

```javascript
/**
 * SSL Keylog Exporter
 * 导出TLS会话密钥到文件，配合tcpdump使用
 */

function exportSSLKeys() {
    var keylogFile = "/sdcard/sslkeylog.txt";
    var keysExported = 0;
    
    console.log("[*] SSL Keylog exporter starting...");
    console.log("[*] Keys will be saved to: " + keylogFile);
    
    // 写文件函数
    function writeKeylog(line) {
        var File = Java.use("java.io.File");
        var FileWriter = Java.use("java.io.FileWriter");
        
        try {
            var writer = FileWriter.$new(keylogFile, true); // append mode
            writer.write(line + "\n");
            writer.close();
            keysExported++;
        } catch (e) {
            console.log("[!] Write error: " + e);
        }
    }
    
    // Hook OpenSSL (BoringSSL on Android)
    var SSL_CTX_set_keylog_callback = Module.findExportByName("libssl.so", "SSL_CTX_set_keylog_callback");
    var SSL_CTX_new = Module.findExportByName("libssl.so", "SSL_CTX_new");
    
    if (SSL_CTX_set_keylog_callback && SSL_CTX_new) {
        console.log("[✓] Found SSL_CTX functions in libssl.so");
        
        // 创建回调函数
        var keylogCallback = new NativeCallback(function(ssl, line) {
            var keyLine = Memory.readUtf8String(line);
            console.log("[KEY] " + keyLine.substring(0, 50) + "...");
            
            // 写入文件
            Java.perform(function() {
                writeKeylog(keyLine);
            });
        }, 'void', ['pointer', 'pointer']);
        
        // Hook SSL_CTX_new，在新建context时注入callback
        Interceptor.attach(SSL_CTX_new, {
            onLeave: function(retval) {
                if (retval.isNull()) return;
                
                var setKeylog = new NativeFunction(SSL_CTX_set_keylog_callback, 'void', ['pointer', 'pointer']);
                setKeylog(retval, keylogCallback);
                console.log("[✓] Keylog callback injected into SSL_CTX");
            }
        });
        
        console.log("[✓] SSL Keylog hook installed!");
    } else {
        console.log("[✗] SSL_CTX functions not found, trying alternative methods...");
        
        // 备用方案：直接Hook SSL_write/SSL_read
        var SSL_write = Module.findExportByName("libssl.so", "SSL_write");
        var SSL_read = Module.findExportByName("libssl.so", "SSL_read");
        
        if (SSL_write) {
            Interceptor.attach(SSL_write, {
                onEnter: function(args) {
                    var ssl = args[0];
                    var buf = args[1];
                    var num = args[2].toInt32();
                    
                    var data = Memory.readByteArray(buf, Math.min(num, 1024));
                    console.log("[SSL_write] " + num + " bytes");
                    console.log(hexdump(data, {length: Math.min(num, 256)}));
                }
            });
        }
        
        if (SSL_read) {
            Interceptor.attach(SSL_read, {
                onLeave: function(retval) {
                    if (retval.toInt32() > 0) {
                        console.log("[SSL_read] " + retval.toInt32() + " bytes");
                    }
                }
            });
        }
    }
    
    // 定时输出统计
    setInterval(function() {
        console.log("[Stats] " + keysExported + " keys exported so far");
    }, 30000);
}

setImmediate(exportSSLKeys);
```

### 4.3 配套使用流程

```bash
# 1. 启动tcpdump抓包（另一个终端）
adb shell "su -c 'tcpdump -i any -w /sdcard/capture.pcap'"

# 2. 运行Frida脚本导出密钥
frida -U -f com.example.app -l ssl_keylog.js --no-pause

# 3. 操作App触发网络请求

# 4. 停止tcpdump (Ctrl+C)

# 5. 拉取文件到PC
adb pull /sdcard/capture.pcap ./
adb pull /sdcard/sslkeylog.txt ./

# 6. Wireshark解密
# Wireshark → Edit → Preferences → Protocols → TLS
# → (Pre)-Master-Secret log filename: 选择 sslkeylog.txt
# → Open capture.pcap
# → 查看解密后的HTTPS流量
```

### 4.4 Wireshark过滤器

```
# 只看HTTPS
tcp.port == 443

# 只看解密后的HTTP2
http2

# 看指定域名
tls.handshake.extensions_server_name == "api.example.com"

# 看POST请求
http.request.method == "POST"
```

---

## 五、方案4: Hook Socket底层（覆盖自定义协议）

### 5.1 原理

直接Hook libc.so的`send`/`recv`/`write`/`read`，或Java层的`SocketOutputStream.write` / `SocketInputStream.read`。

**适用场景**：
- 自定义二进制协议
- WebSocket（在加密前/解密后抓取）
- 非HTTP协议

### 5.2 Hook libc Socket

```javascript
/**
 * Socket底层Hook（Native层）
 * 抓取所有TCP流量（含HTTPS密文）
 */

function hookSocketNative() {
    console.log("[*] Hooking native socket functions...");
    
    // Hook send
    var send = Module.findExportByName("libc.so", "send");
    if (send) {
        Interceptor.attach(send, {
            onEnter: function(args) {
                var sockfd = args[0].toInt32();
                var buf = args[1];
                var len = args[2].toInt32();
                
                if (len > 0 && len < 10000) {  // 过滤太大的包
                    console.log("\n[send] fd=" + sockfd + ", len=" + len);
                    console.log(hexdump(buf, {length: Math.min(len, 256)}));
                    
                    // 尝试解析为ASCII
                    try {
                        var str = Memory.readUtf8String(buf, Math.min(len, 1024));
                        if (str && str.match(/^[GET|POST|PUT|DELETE|HTTP]/)) {
                            console.log("[HTTP] " + str);
                        }
                    } catch (e) {}
                }
            }
        });
        console.log("[✓] Hooked send()");
    }
    
    // Hook recv
    var recv = Module.findExportByName("libc.so", "recv");
    if (recv) {
        Interceptor.attach(recv, {
            onLeave: function(retval) {
                var len = retval.toInt32();
                if (len > 0) {
                    console.log("\n[recv] len=" + len);
                    var buf = this.context.r1 || this.context.rsi;  // ARM/x86
                    if (buf) {
                        console.log(hexdump(buf, {length: Math.min(len, 256)}));
                    }
                }
            }
        });
        console.log("[✓] Hooked recv()");
    }
}

setImmediate(hookSocketNative);
```

### 5.3 Hook Java层Socket

```javascript
/**
 * Socket Hook (Java层)
 * 抓取SocketOutputStream/InputStream
 */

function hookSocketJava() {
    Java.perform(function() {
        console.log("[*] Hooking Java Socket...");
        
        // Hook SocketOutputStream.write
        var SocketOutputStream = Java.use("java.net.SocketOutputStream");
        SocketOutputStream.write.overload('[B', 'int', 'int').implementation = function(b, off, len) {
            console.log("\n[SocketOutputStream.write] len=" + len);
            
            // 转字节数组为字符串尝试
            try {
                var String = Java.use("java.lang.String");
                var str = String.$new(b, off, Math.min(len, 1024));
                console.log("Data: " + str);
            } catch (e) {
                console.log("Data: [Binary]");
            }
            
            return this.write(b, off, len);
        };
        
        // Hook SocketInputStream.read
        var SocketInputStream = Java.use("java.net.SocketInputStream");
        SocketInputStream.read.overload('[B', 'int', 'int').implementation = function(b, off, len) {
            var result = this.read(b, off, len);
            
            if (result > 0) {
                console.log("\n[SocketInputStream.read] len=" + result);
                
                try {
                    var String = Java.use("java.lang.String");
                    var str = String.$new(b, off, Math.min(result, 1024));
                    console.log("Data: " + str);
                } catch (e) {
                    console.log("Data: [Binary]");
                }
            }
            
            return result;
        };
        
        console.log("[✓] Java Socket Hook installed!");
    });
}

setImmediate(hookSocketJava);
```

---

## 六、方案5: 综合方案（参考friTap）

### 6.1 friTap架构

friTap是一个完整的TLS流量镜像工具，整合了：
- SSL_read / SSL_write Hook
- Keylog导出
- Java层网络库Hook
- 自动化PCAP生成

**GitHub**: https://github.com/fkie-cad/friTap

### 6.2 核心思路（可自己实现简化版）

```javascript
/**
 * 综合网络抓包框架（简化版）
 * 整合OkHttp + SSL Keylog + Socket
 */

var CaptureFramework = {
    outputDir: "/sdcard/network_capture/",
    sessionId: Date.now(),
    
    init: function() {
        this.createOutputDir();
        this.hookOkHttp();
        this.hookSSL();
        this.hookSocket();
        console.log("[✓] Capture Framework initialized!");
        console.log("[✓] Session: " + this.sessionId);
    },
    
    createOutputDir: function() {
        Java.perform(function() {
            var File = Java.use("java.io.File");
            var dir = File.$new(CaptureFramework.outputDir);
            if (!dir.exists()) {
                dir.mkdirs();
            }
        });
    },
    
    saveRequest: function(type, data) {
        var filename = this.sessionId + "_" + type + "_" + Date.now() + ".log";
        // 实现保存逻辑
    },
    
    hookOkHttp: function() {
        // 使用前面的OkHttp Hook代码
    },
    
    hookSSL: function() {
        // 使用前面的SSL Keylog代码
    },
    
    hookSocket: function() {
        // 使用前面的Socket Hook代码
    }
};

setImmediate(function() {
    CaptureFramework.init();
});
```

---

## 六点五、方案6: QUIC降级 + 系统代理MITM链路（字节系App实战版）

> 来源: TikTok 46.1.15 抓包实战 (2026-09)。Cronet/TTNet默认QUIC(UDP 443)绕过HTTP代理,
> 且模拟器到宿主机代理的链路有多处坑。本方案是验证过的完整链路。

### 6.5.1 链路拓扑

```
模拟器App → (adb reverse隧道) → 宿主mitmproxy:10814 → (upstream http) → xray HTTP入站:10812 → US出口
```

### 6.5.2 前置步骤

```powershell
# 1. 屏蔽QUIC: 强制Cronet降级TCP走系统代理 (root)
adb shell "su -c 'iptables -I OUTPUT -p udp --dport 443 -j REJECT'"

# 2. mitm CA装进系统证书库 (一次即可; 已装则跳过)
#    Android 13: /system/etc/security/cacerts/ 挂载重写hash命名

# 3. adb reverse: 模拟器内用127.0.0.1访问宿主mitm
adb reverse tcp:10814 tcp:10814
adb reverse --list   # 核查! adb重启/offline后reverse会丢, 必须重配

# 4. 全局代理 (模拟器内)
adb shell settings put global http_proxy 127.0.0.1:10814
```

### 6.5.3 mitmproxy上游链坑

- **mitmproxy 12 不支持 socks5 upstream** (`mode=["upstream:socks5://..."]`报错)
- 解法: xray/v2ray多开一个**HTTP入站**(如10812), mitm上游指它:
  `mode=["upstream:http://127.0.0.1:10812"]`
- mitm监听 `0.0.0.0` 或 `127.0.0.1` 均可(reverse隧道走127.0.0.1)

### 6.5.4 全量抓取addon模式 (scripts/capture/mitm_full_capture.py)

```python
# DumpMaster驱动 + 自定义addon:
#   - 命中关键词路径(aweme/detail/feed/passport...): 记完整headers(含cookie)+body
#   - 所有响应: status/ct/len/body前1KB
#   - 所有Set-Cookie: 单独汇总成cookie jar日志(逆向设备级cookie必备)
```

### 6.5.5 实战踩坑记录

| 症状 | 原因 | 解决 |
|------|------|------|
| mitm在跑但0记录 | **旧mitm实例残留**仍在监听同端口(新流量进了旧addon) | `netstat -ano \| findstr :端口` 找全部PID, taskkill干净再起 |
| 链路突然断 | adb重启后reverse丢失 | `adb reverse --list`核查, 重配+重启App重连 |
| App卡Splash无流量 | 模拟器ARM转译冷启动3-5分钟 | 截屏轮询等待; 重启后转译缓存生效变快 |
| 抓到的都是启动噪声 | addon只按兴趣路径过滤, 启动请求不命中 | 放宽过滤或先跑全路径计数确认流量在走 |
| 系统代理设了但App直连 | App用QUIC绕过代理 | iptables REJECT UDP 443 (6.5.2步骤1) |
| mitm健康检查 | curl需`-x http://127.0.0.1:10814 -k` | 200即通, 不依赖被测App |

### 6.5.6 与Frida方案的取舍

- 本方案优势: **能看到响应体和Set-Cookie**(Frida hook请求层常拿不到响应), 看服务器风控语义
- Frida hook优势: 不动系统设置, 不怕证书固定(Cronet pinning时更稳)
- 字节系(TTNet)实战: MITM可行(mssdk/device_register等请求正常穿透), 但部分业务请求
  可能因pinning或风控失败 — 两种方案互为佐证, 不要单一定论

---

### 7.1 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| Hook后App闪退 | Response Body被消费两次 | 使用`buffer.clone()`或`response.peekBody()` |
| 拿不到Request Body | Body是Stream类型 | 用`Buffer`读取后重新写回 |
| 混淆后找不到OkHttp类 | ProGuard混淆 | 用`Java.enumerateLoadedClasses`搜索 |
| SSL Keylog文件为空 | OpenSSL版本不支持callback | 用备用方案Hook SSL_write/read |
| tcpdump提示权限错误 | 非root或SELinux阻止 | `su -c`执行或临时关闭SELinux |
| Wireshark无法解密 | Keylog格式错误 | 检查每行格式：`CLIENT_RANDOM <48字节> <48字节>` |

### 7.2 性能优化

```javascript
// 1. 过滤不关心的请求
if (url.indexOf("example.com") === -1) {
    return this.execute();  // 直接返回，不记录
}

// 2. 限制Body大小
var bodyStr = buffer.clone().readUtf8();
if (bodyStr.length > 10000) {
    bodyStr = bodyStr.substring(0, 10000) + "\n[... truncated " + (bodyStr.length - 10000) + " bytes]";
}

// 3. 异步写文件（避免阻塞主线程）
Java.scheduleOnMainThread(function() {
    saveToFile(filename, content);
});

// 4. 批量写入
var requestBuffer = [];
setInterval(function() {
    if (requestBuffer.length > 0) {
        saveToFile("batch.log", requestBuffer.join("\n"));
        requestBuffer = [];
    }
}, 5000);
```

### 7.3 调试技巧

```javascript
// 1. 打印调用栈（定位请求来源）
console.log(Java.use("android.util.Log").getStackTraceString(
    Java.use("java.lang.Exception").$new()
));

// 2. 实时过滤（在Frida REPL中）
// 启动时不传脚本，进入REPL后动态注入
frida -U com.example.app
> // 粘贴Hook代码
> // 观察输出后再决定保存哪些

// 3. 条件断点
if (url.indexOf("/api/login") > -1) {
    debugger;  // Frida会暂停，可以在REPL检查变量
}
```

---

## 八、工具集成到dabo_android

### 8.1 推荐目录结构

```
dabo_android/
├── scripts/
│   ├── capture/
│   │   ├── okhttp_logger_basic.js          # 基础OkHttp抓包
│   │   ├── okhttp_logger_advanced.js       # 进阶版（保存文件）
│   │   ├── httpurlconnection_logger.js     # HttpURLConnection抓包
│   │   ├── ssl_keylog_exporter.js          # SSL密钥导出
│   │   ├── socket_native_hook.js           # Native层Socket
│   │   ├── socket_java_hook.js             # Java层Socket
│   │   ├── capture_framework.js            # 综合框架
│   │   └── README.md                       # 使用说明
│   └── ...
└── references/
    └── network-capture-methods.md          # 本文档
```

### 8.2 Python包装脚本（可选）

```python
# scripts/capture/run_capture.py
import subprocess
import sys

def okhttp_capture(package, output_dir="./network_logs"):
    """一键启动OkHttp抓包"""
    script = "scripts/capture/okhttp_logger_advanced.js"
    cmd = [
        "frida", "-U", "-f", package,
        "-l", script,
        "--no-pause"
    ]
    subprocess.run(cmd)
    print(f"[✓] Logs saved to: /sdcard/okhttp_logs/")
    print(f"[!] Pull logs: adb pull /sdcard/okhttp_logs/ {output_dir}")

def ssl_keylog_capture(package):
    """SSL Keylog + tcpdump抓包"""
    print("[1/3] Starting tcpdump...")
    # 启动tcpdump（后台）
    
    print("[2/3] Starting Frida SSL Keylog...")
    # 启动Frida脚本
    
    print("[3/3] Waiting for user action...")
    input("Press Enter when done...")
    
    print("[✓] Pulling files...")
    # 拉取pcap和keylog

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python run_capture.py <method> <package>")
        print("Methods: okhttp, ssl, socket, all")
        sys.exit(1)
    
    method = sys.argv[1]
    package = sys.argv[2]
    
    if method == "okhttp":
        okhttp_capture(package)
    elif method == "ssl":
        ssl_keylog_capture(package)
```

---

## 九、参考资源

### 9.1 开源项目（可直接使用或学习）

| 项目 | 地址 | 特点 | 推荐指数 |
|------|------|------|---------|
| **OkHttpLogger-Frida** | https://github.com/siyujie/OkHttpLogger-Frida | 最完整的OkHttp抓包，支持混淆、重放 | ⭐⭐⭐⭐⭐ |
| **Frida-HTTP-logging** | https://github.com/pranavkdileep/Frida-HTTP-logging | OkHttp + HttpURLConnection通用 | ⭐⭐⭐⭐ |
| **friTap** | https://github.com/fkie-cad/friTap | 完整TLS镜像框架 | ⭐⭐⭐⭐⭐ |
| **frida_bypass_ssl_example** | https://github.com/lasting-yang/frida_bypass_ssl_example | SSL Keylog简洁实现 | ⭐⭐⭐⭐ |
| **android-tcp-sniffer** | https://github.com/sowmiksudo/android-tcp-sniffer | 纯原生层TCP抓取 | ⭐⭐⭐ |
| **r0capture** | 搜索 r0ysue/r0capture | eBPF + Frida流量镜像 | ⭐⭐⭐⭐ |

### 9.2 Frida CodeShare脚本

访问 https://codeshare.frida.re 搜索：
- `okhttp logging`
- `ssl keylog`
- `socket sniffer`
- `http logger`

---

## 十、总结：工具选择指南

| 你的需求 | 推荐方案 | 脚本文件 | 难度 |
|---------|---------|---------|------|
| 快速抓OkHttp应用 | 方案1基础版 | `okhttp_logger_basic.js` | ⭐ |
| 保存所有请求到文件 | 方案1进阶版 | `okhttp_logger_advanced.js` | ⭐ |
| 老应用或自研网络层 | 方案2 | `httpurlconnection_logger.js` | ⭐ |
| 抓Native层HTTPS | 方案3 | `ssl_keylog_exporter.js` + tcpdump | ⭐⭐ |
| 自定义二进制协议 | 方案4 | `socket_native_hook.js` | ⭐⭐⭐ |
| 专业渗透测试 | 方案5 | `capture_framework.js` 或 friTap | ⭐⭐⭐⭐ |

**经验总结**：
1. **90%场景用方案1**（Hook OkHttp），5分钟搞定
2. **通杀方案用方案3**（SSL Keylog），但需要Wireshark后处理
3. **自定义协议才用方案4/5**，否则杀鸡用牛刀

---

**文档版本**: 1.0  
**最后更新**: 2026-08-26  
**维护者**: dabo_android skill  
**适用环境**: Windows + Android 5.0+
