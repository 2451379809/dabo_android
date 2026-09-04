/**
 * 通用反调试/反Hook检测绕过脚本
 * 整合常见的反Frida、反调试、反Root检测绕过方法
 * 
 * 使用方法:
 *   frida -U -f com.example.app -l frida_anti_detection.js
 */

console.log("[*] 加载反检测绕过脚本");

Java.perform(function() {
    
    // ========== 1. 反Root检测 ==========
    console.log("[*] 设置反Root检测绕过");
    
    // RootBeer库（常用Root检测库）
    try {
        var RootBeer = Java.use('com.scottyab.rootbeer.RootBeer');
        RootBeer.isRooted.implementation = function() {
            console.log('[+] RootBeer.isRooted() 返回false');
            return false;
        };
        RootBeer.isRootedWithoutBusyBoxCheck.implementation = function() {
            console.log('[+] RootBeer.isRootedWithoutBusyBoxCheck() 返回false');
            return false;
        };
    } catch(e) {}
    
    // 通用Root检测 - 文件存在检测
    var File = Java.use('java.io.File');
    var originalExists = File.exists;
    File.exists.implementation = function() {
        var path = this.getAbsolutePath();
        var result = originalExists.call(this);
        
        // Root特征文件列表
        var rootFiles = [
            '/system/app/Superuser.apk',
            '/system/xbin/su',
            '/system/bin/su',
            '/sbin/su',
            '/data/local/xbin/su',
            '/data/local/bin/su',
            '/system/sd/xbin/su',
            '/system/bin/failsafe/su',
            '/data/local/su',
            '/su/bin/su',
            '/system/xbin/daemonsu',
            '/system/etc/init.d/99SuperSUDaemon',
            '/system/bin/.ext/.su',
            '/system/xbin/busybox',
            '/data/adb/magisk'
        ];
        
        if (rootFiles.some(f => path.indexOf(f) >= 0)) {
            console.log('[+] 阻止检测Root文件: ' + path);
            return false;
        }
        
        return result;
    };
    
    // ========== 2. 反调试检测 ==========
    console.log("[*] 设置反调试检测绕过");
    
    // Debug.isDebuggerConnected()
    try {
        var Debug = Java.use('android.os.Debug');
        Debug.isDebuggerConnected.implementation = function() {
            console.log('[+] Debug.isDebuggerConnected() 返回false');
            return false;
        };
    } catch(e) {}
    
    // ApplicationInfo flags检测
    try {
        var ApplicationInfo = Java.use('android.content.pm.ApplicationInfo');
        ApplicationInfo.FLAG_DEBUGGABLE.value = 0;
    } catch(e) {}
    
    // ========== 3. 反模拟器检测 ==========
    console.log("[*] 设置反模拟器检测绕过");
    
    // SystemProperties
    try {
        var SystemProperties = Java.use('android.os.SystemProperties');
        var originalGet = SystemProperties.get.overload('java.lang.String');
        
        SystemProperties.get.overload('java.lang.String').implementation = function(key) {
            var value = originalGet.call(this, key);
            
            // 模拟器特征替换
            var spoofMap = {
                'ro.product.brand': 'samsung',
                'ro.product.device': 'SM-G9600',
                'ro.product.model': 'SM-G9600',
                'ro.product.manufacturer': 'samsung',
                'ro.build.tags': 'release-keys',
                'ro.build.fingerprint': 'samsung/dream2qltezh/dream2qltechn:9/PPR1.180610.011/G9600ZHU1CRIA:user/release-keys',
                'ro.kernel.qemu': '0',
                'ro.hardware': 'qcom',
                'ro.build.characteristics': 'default'
            };
            
            if (spoofMap[key]) {
                console.log('[+] SystemProperties劫持: ' + key + ' = ' + spoofMap[key]);
                return spoofMap[key];
            }
            
            return value;
        };
    } catch(e) {}
    
    // Build类字段修改
    try {
        var Build = Java.use('android.os.Build');
        Build.BRAND.value = 'samsung';
        Build.MODEL.value = 'SM-G9600';
        Build.MANUFACTURER.value = 'samsung';
        Build.DEVICE.value = 'dream2qltechn';
        Build.PRODUCT.value = 'dream2qltezh';
        Build.HARDWARE.value = 'qcom';
        Build.FINGERPRINT.value = 'samsung/dream2qltezh/dream2qltechn:9/PPR1.180610.011/G9600ZHU1CRIA:user/release-keys';
        Build.TAGS.value = 'release-keys';
        
        console.log('[+] Build字段已伪装为三星设备');
    } catch(e) {}
    
    // ========== 4. 反Frida检测 ==========
    console.log("[*] 设置反Frida检测绕过");
    
    // 进程名检测
    try {
        var Process = Java.use('android.os.Process');
        // Hook可能的进程检查方法
    } catch(e) {}
    
    // 端口扫描检测（检测27042端口）
    // 这部分在Native层处理更有效
    
    console.log("\n[+] ========================================");
    console.log("[+] 反检测绕过脚本加载完成");
    console.log("[+] Root检测: 已绕过");
    console.log("[+] 调试检测: 已绕过");
    console.log("[+] 模拟器检测: 已伪装");
    console.log("[+] Frida检测: 部分绕过");
    console.log("[+] ========================================\n");
});

// ========== Native层反检测 ==========
Interceptor.attach(Module.findExportByName(null, 'strstr'), {
    onEnter: function(args) {
        this.haystack = Memory.readUtf8String(args[0]);
        this.needle = Memory.readUtf8String(args[1]);
        
        // 替换Frida特征字符串
        if (this.needle === 'frida' || this.needle === 'FRIDA' || 
            this.needle === 'frida-server' || this.needle === 'frida-agent' ||
            this.needle === 'gadget' || this.needle === 're.frida') {
            console.log('[+] 拦截strstr搜索: ' + this.needle);
            args[1].writeUtf8String('xxxxx');
        }
    }
});

// Hook fopen检测maps文件读取
Interceptor.attach(Module.findExportByName(null, 'fopen'), {
    onEnter: function(args) {
        var path = Memory.readUtf8String(args[0]);
        
        // 检测/proc/self/maps读取（用于查找Frida库）
        if (path.indexOf('/proc/') >= 0 && path.indexOf('/maps') >= 0) {
            console.log('[+] 检测到maps文件读取: ' + path);
            // 可以返回伪造的文件句柄
        }
    }
});

// Hook pthread_create检测线程创建（反调试常用）
Interceptor.attach(Module.findExportByName(null, 'pthread_create'), {
    onEnter: function(args) {
        // 记录线程创建，可用于检测反调试线程
        console.log('[*] 新线程创建');
    }
});

console.log("[+] Native层反检测Hook已设置");

// ========== 额外检测绕过 ==========

// Hook exit/kill防止应用自杀
Interceptor.attach(Module.findExportByName(null, 'exit'), {
    onEnter: function(args) {
        console.log('[+] 拦截exit调用，退出码:', args[0].toInt32());
        // 不执行exit，直接返回
        this.context.pc = this.returnAddress;
    }
});

Interceptor.attach(Module.findExportByName(null, 'kill'), {
    onEnter: function(args) {
        var pid = args[0].toInt32();
        var sig = args[1].toInt32();
        console.log('[+] 拦截kill调用, PID:', pid, 'Signal:', sig);
        
        // 如果是杀死自己，阻止
        if (pid === Process.id) {
            console.log('[+] 阻止应用自杀');
            this.context.pc = this.returnAddress;
        }
    }
});

// Hook abort防止异常终止
Interceptor.attach(Module.findExportByName(null, 'abort'), {
    onEnter: function() {
        console.log('[+] 拦截abort调用');
        this.context.pc = this.returnAddress;
    }
});

// Hook ptrace反调试
Interceptor.attach(Module.findExportByName(null, 'ptrace'), {
    onEnter: function(args) {
        var request = args[0].toInt32();
        console.log('[+] ptrace调用，request:', request);
        
        // PTRACE_TRACEME = 0
        if (request === 0) {
            console.log('[+] 拦截PTRACE_TRACEME反调试');
            this.ret = true;
        }
    },
    onLeave: function(retval) {
        if (this.ret) {
            retval.replace(0); // 返回成功
        }
    }
});

// Hook connect（检测27042端口）
Interceptor.attach(Module.findExportByName(null, 'connect'), {
    onEnter: function(args) {
        var sockfd = args[0].toInt32();
        var addr = args[1];
        
        // 读取端口号（struct sockaddr_in的sin_port字段，offset 2）
        try {
            var port = Memory.readU16(addr.add(2));
            port = ((port & 0xFF) << 8) | ((port >> 8) & 0xFF); // 网络字节序转换
            
            if (port === 27042 || port === 27043) {
                console.log('[+] 拦截Frida端口扫描:', port);
                this.block = true;
            }
        } catch(e) {}
    },
    onLeave: function(retval) {
        if (this.block) {
            retval.replace(-1); // 连接失败
        }
    }
});

// Hook stat/access检测文件
var fileCheckFuncs = ['stat', 'lstat', 'fstat', 'access'];
fileCheckFuncs.forEach(function(funcName) {
    try {
        var func = Module.findExportByName(null, funcName);
        if (func) {
            Interceptor.attach(func, {
                onEnter: function(args) {
                    var path = Memory.readCString(args[0]);
                    
                    var suspiciousFiles = [
                        'frida', 'frida-server', 'frida-agent',
                        're.frida', 'gadget',
                        'xposed', 'substrate',
                        'magisk'
                    ];
                    
                    if (path && suspiciousFiles.some(f => path.toLowerCase().indexOf(f) >= 0)) {
                        console.log('[+] 拦截文件检测:', funcName, path);
                        this.block = true;
                    }
                },
                onLeave: function(retval) {
                    if (this.block) {
                        retval.replace(-1); // 文件不存在
                    }
                }
            });
        }
    } catch(e) {}
});

console.log("[+] 增强版反检测完成（exit/kill/ptrace/connect/file check）");
