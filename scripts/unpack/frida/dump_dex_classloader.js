/**
 * DEX ClassLoader Hook Dump脚本
 * 原理：Hook DexFile.loadDex / BaseDexClassLoader构造函数，在DEX加载时导出
 * 
 * 适用场景：
 * - 动态加载DEX的应用
 * - 多DEX应用
 * - InMemoryDexClassLoader加载的DEX
 * 
 * 优势：
 * - 能捕获运行时动态加载的DEX
 * - 不需要搜索内存
 * - 自动获取完整DEX
 * 
 * 使用方法：
 *   frida -U -f com.target.app -l frida_dump_dex_classloader.js
 */

console.log("[*] DEX ClassLoader Hook Dump脚本启动");

Java.perform(function() {
    console.log("[*] Java环境已就绪");
    
    // 获取输出目录
    var ActivityThread = Java.use('android.app.ActivityThread');
    var currentApp = ActivityThread.currentApplication();
    var context = currentApp.getApplicationContext();
    var dataDir = context.getFilesDir().getAbsolutePath();
    var outputDir = dataDir + "/dumped_dex/";
    
    // 创建输出目录
    var File = Java.use('java.io.File');
    var dir = File.$new(outputDir);
    if (!dir.exists()) {
        dir.mkdirs();
    }
    
    console.log("[+] 输出目录:", outputDir);
    
    var dumpCount = 0;
    
    // Hook 1: DexFile类（Android < 8）
    try {
        var DexFile = Java.use('dalvik.system.DexFile');
        
        // Hook loadDex方法
        DexFile.loadDex.overload('java.lang.String', 'java.lang.String', 'int').implementation = function(sourcePathName, outputPathName, flags) {
            console.log("\n[*] DexFile.loadDex被调用");
            console.log("    源路径:", sourcePathName);
            console.log("    输出路径:", outputPathName);
            
            var result = this.loadDex(sourcePathName, outputPathName, flags);
            
            // 复制DEX到输出目录
            try {
                var FileInputStream = Java.use('java.io.FileInputStream');
                var FileOutputStream = Java.use('java.io.FileOutputStream');
                
                var filename = "loader_" + dumpCount + "_" + Date.now() + ".dex";
                var targetPath = outputDir + filename;
                
                var fis = FileInputStream.$new(sourcePathName);
                var fos = FileOutputStream.$new(targetPath);
                
                var buffer = Java.array('byte', [1024]);
                var len;
                while ((len = fis.read(buffer)) !== -1) {
                    fos.write(buffer, 0, len);
                }
                
                fis.close();
                fos.close();
                
                console.log("[+] 已导出:", targetPath);
                dumpCount++;
                
            } catch(e) {
                console.log("[-] 导出失败:", e);
            }
            
            return result;
        };
        
        console.log("[+] DexFile Hook已设置");
        
    } catch(e) {
        console.log("[-] DexFile Hook失败（可能是Android 8+）");
    }
    
    // Hook 2: BaseDexClassLoader（所有版本）
    try {
        var BaseDexClassLoader = Java.use('dalvik.system.BaseDexClassLoader');
        
        BaseDexClassLoader.$init.overload('java.lang.String', 'java.io.File', 'java.lang.String', 'java.lang.ClassLoader').implementation = function(dexPath, optimizedDirectory, librarySearchPath, parent) {
            console.log("\n[*] BaseDexClassLoader构造");
            console.log("    DEX路径:", dexPath);
            console.log("    优化目录:", optimizedDirectory);
            
            // 复制DEX
            if (dexPath && dexPath.endsWith('.dex') || dexPath.endsWith('.jar') || dexPath.endsWith('.apk')) {
                try {
                    var paths = dexPath.split(':');
                    paths.forEach(function(path) {
                        if (path.length === 0) return;
                        
                        var File = Java.use('java.io.File');
                        var file = File.$new(path);
                        
                        if (file.exists()) {
                            var FileInputStream = Java.use('java.io.FileInputStream');
                            var FileOutputStream = Java.use('java.io.FileOutputStream');
                            
                            var filename = "basedex_" + dumpCount + "_" + file.getName();
                            var targetPath = outputDir + filename;
                            
                            var fis = FileInputStream.$new(file);
                            var fos = FileOutputStream.$new(targetPath);
                            
                            var buffer = Java.array('byte', [8192]);
                            var len;
                            while ((len = fis.read(buffer)) !== -1) {
                                fos.write(buffer, 0, len);
                            }
                            
                            fis.close();
                            fos.close();
                            
                            console.log("[+] 已导出:", targetPath);
                            dumpCount++;
                        }
                    });
                } catch(e) {
                    console.log("[-] 导出失败:", e);
                }
            }
            
            return this.$init(dexPath, optimizedDirectory, librarySearchPath, parent);
        };
        
        console.log("[+] BaseDexClassLoader Hook已设置");
        
    } catch(e) {
        console.log("[-] BaseDexClassLoader Hook失败:", e);
    }
    
    // Hook 3: InMemoryDexClassLoader（Android 8+，内存加载DEX）
    try {
        var InMemoryDexClassLoader = Java.use('dalvik.system.InMemoryDexClassLoader');
        
        InMemoryDexClassLoader.$init.overload('java.nio.ByteBuffer', 'java.lang.ClassLoader').implementation = function(dexBuffer, parent) {
            console.log("\n[*] InMemoryDexClassLoader 内存DEX加载");
            
            // 获取ByteBuffer内容
            try {
                var dexSize = dexBuffer.remaining();
                console.log("    DEX大小:", dexSize);
                
                // 读取ByteBuffer内容
                var dexBytes = Java.array('byte', [dexSize]);
                dexBuffer.get(dexBytes);
                dexBuffer.rewind(); // 重置position供原方法使用
                
                // 写入文件
                var filename = "inmemory_" + dumpCount + "_" + Date.now() + ".dex";
                var targetPath = outputDir + filename;
                
                var FileOutputStream = Java.use('java.io.FileOutputStream');
                var fos = FileOutputStream.$new(targetPath);
                fos.write(dexBytes);
                fos.close();
                
                console.log("[+] 已导出:", targetPath);
                dumpCount++;
                
            } catch(e) {
                console.log("[-] 导出失败:", e);
            }
            
            return this.$init(dexBuffer, parent);
        };
        
        console.log("[+] InMemoryDexClassLoader Hook已设置");
        
    } catch(e) {
        console.log("[-] InMemoryDexClassLoader Hook失败（可能不是Android 8+）");
    }
    
    console.log("\n[+] ========================================");
    console.log("[+] DEX ClassLoader Hook已全部设置");
    console.log("[+] 等待应用加载DEX...");
    console.log("[+] 导出位置: " + outputDir);
    console.log("[+] ========================================");
    console.log("\n[!] 拉取命令:");
    console.log("    adb pull " + outputDir + " ./dumped/");
});
