/**
 * DEX内存Dump脚本（基于技术原理自行实现）
 * 原理：搜索内存中的DEX magic头（dex\n035/036/037/038/039），修复header，导出
 * 
 * 适用场景：
 * - 一代壳（整体加密DEX）
 * - 360加固、梆梆加固、乐固等常见加固
 * - 需要绕过反Frida检测后使用
 * 
 * 使用方法：
 *   frida -U -f com.target.app -l frida_dump_dex_memory.js
 */

console.log("[*] DEX内存Dump脚本启动");

// DEX Magic常量
const DEX_MAGIC = {
    'dex035': [0x64, 0x65, 0x78, 0x0a, 0x30, 0x33, 0x35, 0x00],
    'dex036': [0x64, 0x65, 0x78, 0x0a, 0x30, 0x33, 0x36, 0x00],
    'dex037': [0x64, 0x65, 0x78, 0x0a, 0x30, 0x33, 0x37, 0x00],
    'dex038': [0x64, 0x65, 0x78, 0x0a, 0x30, 0x33, 0x38, 0x00],
    'dex039': [0x64, 0x65, 0x78, 0x0a, 0x30, 0x33, 0x39, 0x00]
};

Java.perform(function() {
    console.log("[*] Java环境已就绪");
    
    // 获取应用包名和数据目录
    var ActivityThread = Java.use('android.app.ActivityThread');
    var currentApp = ActivityThread.currentApplication();
    var context = currentApp.getApplicationContext();
    var packageName = context.getPackageName();
    var dataDir = context.getFilesDir().getAbsolutePath();
    
    console.log("[+] 包名:", packageName);
    console.log("[+] 数据目录:", dataDir);
    
    // 创建输出目录
    var outputDir = dataDir + "/dumped_dex/";
    var File = Java.use('java.io.File');
    var dir = File.$new(outputDir);
    if (!dir.exists()) {
        dir.mkdirs();
    }
    
    console.log("[+] 输出目录:", outputDir);
    
    // 搜索并导出DEX
    function dumpDexFromMemory() {
        console.log("\n[*] 开始搜索内存中的DEX...");
        
        var dexCount = 0;
        
        // 遍历所有内存区域
        Process.enumerateRanges('r--').concat(Process.enumerateRanges('rw-')).forEach(function(range) {
            // 跳过太小的区域
            if (range.size < 0x1000) return;
            
            try {
                var baseAddr = range.base;
                var size = range.size;
                
                // 搜索DEX magic
                Memory.scan(baseAddr, size, "64 65 78 0a 30 33", {
                    onMatch: function(address, size) {
                        try {
                            // 验证是否为有效DEX
                            var magic = Memory.readByteArray(address, 8);
                            var magicBytes = new Uint8Array(magic);
                            
                            // 检查DEX版本
                            var isDex = false;
                            for (var version in DEX_MAGIC) {
                                var expected = DEX_MAGIC[version];
                                var match = true;
                                for (var i = 0; i < 8; i++) {
                                    if (magicBytes[i] !== expected[i]) {
                                        match = false;
                                        break;
                                    }
                                }
                                if (match) {
                                    isDex = true;
                                    break;
                                }
                            }
                            
                            if (!isDex) return;
                            
                            // 读取DEX大小（offset 0x20, 4 bytes）
                            var dexSize = Memory.readU32(address.add(0x20));
                            
                            // 合理性检查
                            if (dexSize < 0x1000 || dexSize > 100 * 1024 * 1024) return;
                            
                            console.log("[+] 找到DEX @ " + address + ", 大小: " + dexSize);
                            
                            // 读取DEX数据
                            var dexData = Memory.readByteArray(address, dexSize);
                            
                            // 写入文件
                            var filename = "classes_" + dexCount + "_" + Date.now() + ".dex";
                            var filepath = outputDir + filename;
                            
                            var FileOutputStream = Java.use('java.io.FileOutputStream');
                            var fos = FileOutputStream.$new(filepath);
                            fos.write(dexData);
                            fos.close();
                            
                            console.log("[+] 已导出: " + filepath);
                            dexCount++;
                            
                        } catch(e) {
                            // 忽略错误，继续搜索
                        }
                    },
                    onComplete: function() {}
                });
                
            } catch(e) {
                // 某些内存区域可能无法访问
            }
        });
        
        console.log("\n[+] ========================================");
        console.log("[+] DEX Dump完成");
        console.log("[+] 共导出 " + dexCount + " 个DEX文件");
        console.log("[+] 位置: " + outputDir);
        console.log("[+] ========================================");
        console.log("\n[!] 使用以下命令拉取到电脑:");
        console.log("    adb pull " + outputDir + " ./dumped/");
    }
    
    // 延迟执行，等待DEX完全加载
    setTimeout(function() {
        dumpDexFromMemory();
    }, 3000);
    
    console.log("[+] 将在3秒后开始Dump...");
});
