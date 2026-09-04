/**
 * 通用SSL Pinning绕过脚本
 * 来源整合: HelloHuDi/AndroidReverseNotes + CreditTone/hooker
 * 
 * 使用方法:
 *   frida -U -f com.example.app -l frida_universal_ssl_unpin.js
 */

console.log("[*] 开始加载SSL Pinning绕过脚本");

Java.perform(function() {
    console.log("[*] Java环境已就绪");
    
    // ========== 方法1: OkHttp3 CertificatePinner ==========
    try {
        var CertificatePinner = Java.use('okhttp3.CertificatePinner');
        console.log("[*] 找到OkHttp3 CertificatePinner");
        
        CertificatePinner.check.overload('java.lang.String', 'java.util.List').implementation = function(hostname, list) {
            console.log('[+] OkHttp3 SSL Pinning bypassed for: ' + hostname);
            return;
        };
        
        // OkHttp 3.14+ 的新方法
        try {
            CertificatePinner.check.overload('java.lang.String', 'kotlin.jvm.functions.Function0').implementation = function(hostname, func) {
                console.log('[+] OkHttp3 SSL Pinning (new) bypassed for: ' + hostname);
                return;
            };
        } catch(e) {}
        
    } catch(e) {
        console.log('[-] OkHttp3 CertificatePinner not found');
    }
    
    // ========== 方法2: TrustManager替换 ==========
    try {
        var X509TrustManager = Java.use('javax.net.ssl.X509TrustManager');
        var SSLContext = Java.use('javax.net.ssl.SSLContext');
        
        // 创建信任所有证书的TrustManager
        var TrustManager = Java.registerClass({
            name: 'com.dabo.TrustAllManager',
            implements: [X509TrustManager],
            methods: {
                checkClientTrusted: function(chain, authType) {},
                checkServerTrusted: function(chain, authType) {},
                getAcceptedIssuers: function() {
                    return [];
                }
            }
        });
        
        // Hook SSLContext.init
        SSLContext.init.overload('[Ljavax.net.ssl.KeyManager;', '[Ljavax.net.ssl.TrustManager;', 'java.security.SecureRandom').implementation = function(km, tm, random) {
            console.log('[+] SSLContext.init hooked, replacing TrustManager');
            this.init(km, [TrustManager.$new()], random);
        };
        
        console.log('[+] TrustManager 替换完成');
        
    } catch(e) {
        console.log('[-] TrustManager hook failed:', e);
    }
    
    // ========== 方法3: HttpsURLConnection ==========
    try {
        var HttpsURLConnection = Java.use('javax.net.ssl.HttpsURLConnection');
        
        HttpsURLConnection.setDefaultHostnameVerifier.implementation = function(hostnameVerifier) {
            console.log('[+] HttpsURLConnection HostnameVerifier bypassed');
            return;
        };
        
        HttpsURLConnection.setSSLSocketFactory.implementation = function(socketFactory) {
            console.log('[+] HttpsURLConnection SSLSocketFactory bypassed');
            return;
        };
        
        HttpsURLConnection.setHostnameVerifier.implementation = function(hostnameVerifier) {
            console.log('[+] HttpsURLConnection instance HostnameVerifier bypassed');
            return;
        };
        
        console.log('[+] HttpsURLConnection hooks 完成');
        
    } catch(e) {
        console.log('[-] HttpsURLConnection hook failed:', e);
    }
    
    // ========== 方法4: WebView SSL Error Handler ==========
    try {
        var WebViewClient = Java.use('android.webkit.WebViewClient');
        
        WebViewClient.onReceivedSslError.overload('android.webkit.WebView', 'android.webkit.SslErrorHandler', 'android.net.http.SslError').implementation = function(webView, handler, error) {
            console.log('[+] WebView SSL Error bypassed');
            handler.proceed();
        };
        
        console.log('[+] WebView SSL hooks 完成');
        
    } catch(e) {
        console.log('[-] WebView hook failed:', e);
    }
    
    // ========== 方法5: Cronet (Google网络库) ==========
    try {
        var CronetEngine = Java.use('org.chromium.net.impl.CronetEngineBuilderImpl');
        
        // 禁用Public Key Pinning
        CronetEngine.enablePublicKeyPinningBypassForLocalTrustAnchors.overload('boolean').implementation = function(value) {
            console.log('[+] Cronet Public Key Pinning bypass enabled');
            return this.enablePublicKeyPinningBypassForLocalTrustAnchors(true);
        };
        
        console.log('[+] Cronet hooks 完成');
        
    } catch(e) {
        console.log('[-] Cronet not found');
    }
    
    // ========== 方法6: Apache HTTP Client ==========
    try {
        var SSLSocketFactory = Java.use('org.apache.http.conn.ssl.SSLSocketFactory');
        
        SSLSocketFactory.getSocketFactory.overload().implementation = function() {
            console.log('[+] Apache SSLSocketFactory bypassed');
            return SSLSocketFactory.getSocketFactory();
        };
        
    } catch(e) {
        console.log('[-] Apache HTTP Client not found');
    }
    
    console.log("\n[+] ========================================");
    console.log("[+] SSL Pinning绕过脚本加载完成");
    console.log("[+] 现在可以使用Burp/Charles等工具抓包");
    console.log("[+] ========================================\n");
});
