/**
 * 加密算法Hook脚本
 * 覆盖：AES、DES、RSA、MD5、SHA、HMAC等常见加密算法
 * 
 * 功能：
 * - 自动打印加密参数（明文、密文、密钥、IV）
 * - 支持Java层和部分Native层
 * - 帮助快速定位和还原加密逻辑
 * 
 * 使用方法：
 *   frida -U -f com.target.app -l frida_crypto_hook.js
 */

console.log("[*] 加密算法Hook脚本启动");

// 辅助函数：字节数组转十六进制
function bytesToHex(bytes) {
    if (!bytes) return "null";
    
    var hex = "";
    for (var i = 0; i < bytes.length && i < 256; i++) { // 限制最多256字节
        var b = bytes[i] & 0xFF;
        hex += ("0" + b.toString(16)).slice(-2);
    }
    if (bytes.length > 256) {
        hex += "... (长度: " + bytes.length + ")";
    }
    return hex;
}

// 辅助函数：Base64编码
function toBase64(bytes) {
    if (!bytes) return "null";
    
    try {
        var Base64 = Java.use('android.util.Base64');
        return Base64.encodeToString(bytes, 2); // NO_WRAP
    } catch(e) {
        return bytesToHex(bytes);
    }
}

Java.perform(function() {
    console.log("[*] Java环境已就绪\n");
    
    // ========== 1. Cipher（AES/DES/RSA核心类） ==========
    try {
        var Cipher = Java.use('javax.crypto.Cipher');
        
        // Hook init方法（初始化加密器）
        Cipher.init.overload('int', 'java.security.Key').implementation = function(mode, key) {
            console.log("\n[Cipher.init]");
            console.log("  模式:", mode === 1 ? "ENCRYPT" : (mode === 2 ? "DECRYPT" : mode));
            console.log("  算法:", key.getAlgorithm());
            
            // 打印密钥
            try {
                var keyBytes = key.getEncoded();
                console.log("  密钥(Hex):", bytesToHex(keyBytes));
                console.log("  密钥(Base64):", toBase64(keyBytes));
            } catch(e) {}
            
            return this.init(mode, key);
        };
        
        // Hook init with IV
        Cipher.init.overload('int', 'java.security.Key', 'java.security.spec.AlgorithmParameterSpec').implementation = function(mode, key, spec) {
            console.log("\n[Cipher.init with IV]");
            console.log("  模式:", mode === 1 ? "ENCRYPT" : (mode === 2 ? "DECRYPT" : mode));
            console.log("  算法:", key.getAlgorithm());
            
            // 打印密钥
            try {
                var keyBytes = key.getEncoded();
                console.log("  密钥(Hex):", bytesToHex(keyBytes));
            } catch(e) {}
            
            // 打印IV
            try {
                var IvParameterSpec = Java.use('javax.crypto.spec.IvParameterSpec');
                if (spec.$className === 'javax.crypto.spec.IvParameterSpec') {
                    var ivBytes = Java.cast(spec, IvParameterSpec).getIV();
                    console.log("  IV(Hex):", bytesToHex(ivBytes));
                }
            } catch(e) {}
            
            return this.init(mode, key, spec);
        };
        
        // Hook doFinal（执行加解密）
        Cipher.doFinal.overload('[B').implementation = function(input) {
            console.log("\n[Cipher.doFinal]");
            console.log("  输入(Hex):", bytesToHex(input));
            console.log("  输入(Base64):", toBase64(input));
            
            var result = this.doFinal(input);
            
            console.log("  输出(Hex):", bytesToHex(result));
            console.log("  输出(Base64):", toBase64(result));
            
            return result;
        };
        
        console.log("[+] Cipher Hook已设置");
        
    } catch(e) {
        console.log("[-] Cipher Hook失败:", e);
    }
    
    // ========== 2. MessageDigest（MD5/SHA） ==========
    try {
        var MessageDigest = Java.use('java.security.MessageDigest');
        
        MessageDigest.digest.overload('[B').implementation = function(input) {
            console.log("\n[MessageDigest.digest]");
            console.log("  算法:", this.getAlgorithm());
            console.log("  输入:", new TextDecoder().decode(input));
            console.log("  输入(Hex):", bytesToHex(input));
            
            var result = this.digest(input);
            
            console.log("  输出(Hex):", bytesToHex(result));
            
            return result;
        };
        
        MessageDigest.digest.overload().implementation = function() {
            console.log("\n[MessageDigest.digest]");
            console.log("  算法:", this.getAlgorithm());
            
            var result = this.digest();
            
            console.log("  输出(Hex):", bytesToHex(result));
            
            return result;
        };
        
        console.log("[+] MessageDigest Hook已设置");
        
    } catch(e) {
        console.log("[-] MessageDigest Hook失败:", e);
    }
    
    // ========== 3. Mac（HMAC） ==========
    try {
        var Mac = Java.use('javax.crypto.Mac');
        
        Mac.init.overload('java.security.Key').implementation = function(key) {
            console.log("\n[Mac.init]");
            console.log("  算法:", this.getAlgorithm());
            
            try {
                var keyBytes = key.getEncoded();
                console.log("  密钥(Hex):", bytesToHex(keyBytes));
            } catch(e) {}
            
            return this.init(key);
        };
        
        Mac.doFinal.overload('[B').implementation = function(input) {
            console.log("\n[Mac.doFinal]");
            console.log("  输入:", new TextDecoder().decode(input));
            console.log("  输入(Hex):", bytesToHex(input));
            
            var result = this.doFinal(input);
            
            console.log("  输出(Hex):", bytesToHex(result));
            
            return result;
        };
        
        console.log("[+] Mac Hook已设置");
        
    } catch(e) {
        console.log("[-] Mac Hook失败:", e);
    }
    
    // ========== 4. Base64 ==========
    try {
        var Base64 = Java.use('android.util.Base64');
        
        Base64.encodeToString.overload('[B', 'int').implementation = function(input, flags) {
            var result = this.encodeToString(input, flags);
            
            console.log("\n[Base64.encode]");
            console.log("  输入(Hex):", bytesToHex(input));
            console.log("  输出:", result);
            
            return result;
        };
        
        Base64.decode.overload('java.lang.String', 'int').implementation = function(str, flags) {
            var result = this.decode(str, flags);
            
            console.log("\n[Base64.decode]");
            console.log("  输入:", str.substring(0, Math.min(100, str.length)));
            console.log("  输出(Hex):", bytesToHex(result));
            
            return result;
        };
        
        console.log("[+] Base64 Hook已设置");
        
    } catch(e) {
        console.log("[-] Base64 Hook失败:", e);
    }
    
    // ========== 5. SecretKeySpec（密钥生成） ==========
    try {
        var SecretKeySpec = Java.use('javax.crypto.spec.SecretKeySpec');
        
        SecretKeySpec.$init.overload('[B', 'java.lang.String').implementation = function(key, algorithm) {
            console.log("\n[SecretKeySpec]");
            console.log("  算法:", algorithm);
            console.log("  密钥(Hex):", bytesToHex(key));
            console.log("  密钥(Base64):", toBase64(key));
            
            return this.$init(key, algorithm);
        };
        
        console.log("[+] SecretKeySpec Hook已设置");
        
    } catch(e) {
        console.log("[-] SecretKeySpec Hook失败:", e);
    }
    
    console.log("\n[+] ========================================");
    console.log("[+] 加密算法Hook全部设置完成");
    console.log("[+] 触发加密操作后将自动打印参数");
    console.log("[+] ========================================\n");
});

// Native层常见加密函数Hook
var nativeHooks = [
    // OpenSSL AES
    {name: 'AES_encrypt', module: 'libcrypto.so'},
    {name: 'AES_decrypt', module: 'libcrypto.so'},
    {name: 'AES_set_encrypt_key', module: 'libcrypto.so'},
    {name: 'AES_set_decrypt_key', module: 'libcrypto.so'},
    
    // OpenSSL MD5/SHA
    {name: 'MD5', module: 'libcrypto.so'},
    {name: 'SHA1', module: 'libcrypto.so'},
    {name: 'SHA256', module: 'libcrypto.so'},
];

nativeHooks.forEach(function(hook) {
    try {
        var addr = Module.findExportByName(hook.module, hook.name);
        if (addr) {
            Interceptor.attach(addr, {
                onEnter: function(args) {
                    console.log("\n[Native." + hook.name + "]");
                    console.log("  调用地址:", addr);
                }
            });
            console.log("[+] Native Hook:", hook.name);
        }
    } catch(e) {}
});
