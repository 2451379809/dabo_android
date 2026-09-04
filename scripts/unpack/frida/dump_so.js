/**
 * SO库Dump脚本
 * 原理：Hook dlopen/android_dlopen_ext，在SO加载后导出内存中的完整SO
 * 
 * 适用场景：
 * - 加密SO的导出
 * - VMP/Ollvm混淆的SO（导出解密后的）
 * - Unity/IL2CPP游戏的libil2cpp.so
 * - 壳加固后的Native库
 * 
 * 使用方法：
 *   frida -U -f com.target.app -l frida_dump_so.js
 */

console.log("[*] SO Dump脚本启动");

Java.perform(function() {
    console.log("[*] Java环境已就绪");
    
    // 获取输出目录
    var ActivityThread = Java.use('android.app.ActivityThread');
    var currentApp = ActivityThread.currentApplication();
    var context = currentApp.getApplicationContext();
    var dataDir = context.getFilesDir().getAbsolutePath();
    var outputDir = dataDir + "/dumped_so/";
    
    // 创建输出目录
    var File = Java.use('java.io.File');
    var dir = File.$new(outputDir);
    if (!dir.exists()) {
        dir.mkdirs();
    }
    
    console.log("[+] 输出目录:", outputDir);
    console.log("\n[+] ========================================");
    console.log("[+] SO Dump Hook已设置");
    console.log("[+] 等待SO加载...");
    console.log("[+] ========================================\n");
});

// Native层Hook
var dumpedSo = {}; // 记录已导出的SO，避免重复

// Hook dlopen
var dlopen = Module.findExportByName(null, "dlopen");
if (dlopen) {
    Interceptor.attach(dlopen, {
        onEnter: function(args) {
            var soPath = Memory.readCString(args[0]);
            this.soPath = soPath;
        },
        onLeave: function(retval) {
            if (retval.toInt32() !== 0 && this.soPath) {
                dumpSoLibrary(this.soPath);
            }
        }
    });
    console.log("[+] dlopen Hook已设置");
}

// Hook android_dlopen_ext (Android 7+)
var android_dlopen_ext = Module.findExportByName(null, "android_dlopen_ext");
if (android_dlopen_ext) {
    Interceptor.attach(android_dlopen_ext, {
        onEnter: function(args) {
            var soPath = Memory.readCString(args[0]);
            this.soPath = soPath;
        },
        onLeave: function(retval) {
            if (retval.toInt32() !== 0 && this.soPath) {
                dumpSoLibrary(this.soPath);
            }
        }
    });
    console.log("[+] android_dlopen_ext Hook已设置");
}

// Dump SO函数
function dumpSoLibrary(soPath) {
    // 过滤系统SO
    if (soPath.indexOf("/system/") === 0 || 
        soPath.indexOf("/vendor/") === 0 ||
        soPath.indexOf("/apex/") === 0) {
        return;
    }
    
    // 避免重复导出
    if (dumpedSo[soPath]) {
        return;
    }
    dumpedSo[soPath] = true;
    
    console.log("\n[*] SO加载: " + soPath);
    
    // 延迟dump，确保SO完全加载和解密
    setTimeout(function() {
        try {
            // 从路径获取SO名称
            var soName = soPath.split('/').pop();
            
            // 查找SO模块
            var module = Process.findModuleByName(soName);
            if (!module) {
                console.log("[-] 未找到模块:", soName);
                return;
            }
            
            console.log("[+] 模块基址:", module.base);
            console.log("[+] 模块大小:", module.size);
            
            // 读取SO内存
            var soData = Memory.readByteArray(module.base, module.size);
            
            // 构造输出文件名
            var timestamp = Date.now();
            var outputName = soName.replace('.so', '_dumped_' + timestamp + '.so');
            var outputPath = "/data/local/tmp/" + outputName;
            
            // 写入文件
            var file = new File(outputPath, "wb");
            file.write(soData);
            file.close();
            
            console.log("[+] 已导出: " + outputPath);
            console.log("[!] 拉取命令: adb pull " + outputPath + " ./\n");
            
        } catch(e) {
            console.log("[-] Dump失败:", e);
        }
    }, 1000);
}

// 主动dump已加载的SO
function dumpAllLoadedSo() {
    console.log("\n[*] 主动Dump所有已加载的SO...\n");
    
    Process.enumerateModules().forEach(function(module) {
        // 跳过系统SO
        if (module.path.indexOf("/system/") === 0 || 
            module.path.indexOf("/vendor/") === 0 ||
            module.path.indexOf("/apex/") === 0) {
            return;
        }
        
        // 跳过已导出的
        if (dumpedSo[module.path]) {
            return;
        }
        
        console.log("[*] Dump模块:", module.name);
        dumpSoLibrary(module.path);
    });
    
    console.log("\n[+] 主动Dump完成");
}

// 5秒后主动dump一次已加载的SO
setTimeout(function() {
    dumpAllLoadedSo();
}, 5000);

console.log("\n[!] 提示:");
console.log("    1. 脚本会自动Hook新加载的SO");
console.log("    2. 5秒后会主动dump所有已加载的应用SO");
console.log("    3. 导出位置: /data/local/tmp/");
console.log("    4. 某些SO可能需要ELF修复工具（SoFixer）");
