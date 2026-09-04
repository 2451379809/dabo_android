"""
Frida Hook脚本生成器
根据用户需求自动生成Frida Hook脚本

使用方法:
    python frida_script_generator.py --type [类型] [参数]
    
示例:
    # 生成SSL Pinning绕过脚本
    python frida_script_generator.py --type ssl
    
    # 生成Hook指定类的脚本
    python frida_script_generator.py --type hook-class --class com.example.MainActivity
    
    # 生成Hook指定方法的脚本
    python frida_script_generator.py --type hook-method --class com.example.Crypto --method encrypt
    
    # 生成反检测脚本
    python frida_script_generator.py --type anti-detect
"""

import argparse
import os

# 脚本模板库
TEMPLATES = {
    'ssl': """
/**
 * SSL Pinning绕过脚本
 * 自动生成于 {timestamp}
 */

Java.perform(function() {{
    console.log("[*] SSL Pinning Bypass");
    
    // OkHttp3
    try {{
        var CertificatePinner = Java.use('okhttp3.CertificatePinner');
        CertificatePinner.check.overload('java.lang.String', 'java.util.List').implementation = function(hostname, list) {{
            console.log('[+] Bypassed for: ' + hostname);
            return;
        }};
    }} catch(e) {{}}
    
    // TrustManager
    try {{
        var X509TrustManager = Java.use('javax.net.ssl.X509TrustManager');
        var SSLContext = Java.use('javax.net.ssl.SSLContext');
        
        var TrustManager = Java.registerClass({{
            name: 'com.generated.TrustAll',
            implements: [X509TrustManager],
            methods: {{
                checkClientTrusted: function() {{}},
                checkServerTrusted: function() {{}},
                getAcceptedIssuers: function() {{ return []; }}
            }}
        }});
        
        SSLContext.init.overload('[Ljavax.net.ssl.KeyManager;', '[Ljavax.net.ssl.TrustManager;', 'java.security.SecureRandom').implementation = function(km, tm, random) {{
            this.init(km, [TrustManager.$new()], random);
        }};
    }} catch(e) {{}}
    
    console.log("[+] SSL Pinning Bypass完成");
}});
""",

    'hook-class': """
/**
 * Hook类的所有方法
 * 目标类: {class_name}
 * 自动生成于 {timestamp}
 */

Java.perform(function() {{
    console.log("[*] 开始Hook {class_name}");
    
    try {{
        var TargetClass = Java.use('{class_name}');
        var methods = TargetClass.class.getDeclaredMethods();
        
        methods.forEach(function(method) {{
            var methodName = method.getName();
            console.log("[*] Hooking:", methodName);
            
            try {{
                var overloads = TargetClass[methodName].overloads;
                overloads.forEach(function(overload) {{
                    overload.implementation = function() {{
                        console.log("\\n[CALL] {class_name}." + methodName);
                        console.log("  Args:", Array.prototype.slice.call(arguments));
                        
                        var result = this[methodName].apply(this, arguments);
                        
                        console.log("  Return:", result);
                        return result;
                    }};
                }});
            }} catch(e) {{
                console.log("[-] 无法Hook:", methodName);
            }}
        }});
        
        console.log("[+] Hook完成");
        
    }} catch(e) {{
        console.log("[-] 错误:", e);
    }}
}});
""",

    'hook-method': """
/**
 * Hook指定方法
 * 类: {class_name}
 * 方法: {method_name}
 * 自动生成于 {timestamp}
 */

Java.perform(function() {{
    console.log("[*] Hook {class_name}.{method_name}");
    
    try {{
        var TargetClass = Java.use('{class_name}');
        
        // 如果知道参数类型，可以指定overload
        // TargetClass.{method_name}.overload('java.lang.String').implementation = function(arg) {{
        
        TargetClass.{method_name}.implementation = function() {{
            console.log("\\n[CALL] {class_name}.{method_name}");
            console.log("  参数:", Array.prototype.slice.call(arguments));
            
            // 调用原始方法
            var result = this.{method_name}.apply(this, arguments);
            
            console.log("  返回值:", result);
            
            // 可以修改返回值
            // return "修改后的值";
            
            return result;
        }};
        
        console.log("[+] Hook设置完成");
        
    }} catch(e) {{
        console.log("[-] Hook失败:", e);
    }}
}});
""",

    'anti-detect': """
/**
 * 反检测脚本
 * 绕过Root、调试、模拟器、Frida检测
 * 自动生成于 {timestamp}
 */

Java.perform(function() {{
    console.log("[*] 反检测脚本加载");
    
    // 1. 反Root
    try {{
        var RootBeer = Java.use('com.scottyab.rootbeer.RootBeer');
        RootBeer.isRooted.implementation = function() {{
            return false;
        }};
    }} catch(e) {{}}
    
    var File = Java.use('java.io.File');
    File.exists.implementation = function() {{
        var path = this.getAbsolutePath();
        var rootFiles = ['/system/xbin/su', '/system/bin/su', '/sbin/su'];
        
        if (rootFiles.some(f => path.indexOf(f) >= 0)) {{
            return false;
        }}
        return this.exists();
    }};
    
    // 2. 反调试
    try {{
        var Debug = Java.use('android.os.Debug');
        Debug.isDebuggerConnected.implementation = function() {{
            return false;
        }};
    }} catch(e) {{}}
    
    // 3. 伪装设备信息
    try {{
        var Build = Java.use('android.os.Build');
        Build.BRAND.value = 'samsung';
        Build.MODEL.value = 'SM-G9600';
        Build.MANUFACTURER.value = 'samsung';
    }} catch(e) {{}}
    
    console.log("[+] 反检测完成");
}});

// Native层
Interceptor.attach(Module.findExportByName(null, 'strstr'), {{
    onEnter: function(args) {{
        var needle = Memory.readUtf8String(args[1]);
        if (needle === 'frida' || needle === 'FRIDA') {{
            args[1].writeUtf8String('xxxxx');
        }}
    }}
}});
""",

    'trace': """
/**
 * 方法调用追踪脚本
 * 追踪包含关键字的所有方法调用
 * 关键字: {keywords}
 * 自动生成于 {timestamp}
 */

Java.perform(function() {{
    console.log("[*] 开始追踪包含关键字的方法: {keywords}");
    
    Java.enumerateLoadedClasses({{
        onMatch: function(className) {{
            // 只追踪应用自己的类
            if (!className.startsWith('com.') && !className.startsWith('cn.')) {{
                return;
            }}
            
            try {{
                var targetClass = Java.use(className);
                var methods = targetClass.class.getDeclaredMethods();
                
                methods.forEach(function(method) {{
                    var methodName = method.getName().toLowerCase();
                    var keywords = [{keywords_list}];
                    
                    if (keywords.some(kw => methodName.includes(kw))) {{
                        console.log("[*] 追踪:", className + "." + method.getName());
                        
                        try {{
                            targetClass[method.getName()].implementation = function() {{
                                console.log("\\n[TRACE] " + className + "." + method.getName());
                                var result = this[method.getName()].apply(this, arguments);
                                return result;
                            }};
                        }} catch(e) {{}}
                    }}
                }});
            }} catch(e) {{}}
        }},
        onComplete: function() {{
            console.log("[+] 追踪设置完成");
        }}
    }});
}});
""",

    'dump-dex': """
/**
 * DEX dump脚本
 * 自动导出内存中加载的DEX文件
 * 自动生成于 {timestamp}
 */

Java.perform(function() {{
    console.log("[*] DEX Dump脚本");
    
    var DexFile = Java.use("dalvik.system.DexFile");
    
    DexFile.$init.overload('java.io.File').implementation = function(file) {{
        var path = file.getAbsolutePath();
        console.log("[*] 加载DEX:", path);
        
        if (path.includes("/data/app/")) {{
            var timestamp = Date.now();
            var dumpPath = "/sdcard/dumped_" + timestamp + ".dex";
            
            try {{
                var Runtime = Java.use("java.lang.Runtime");
                var cmd = "cp " + path + " " + dumpPath;
                Runtime.getRuntime().exec(cmd);
                console.log("[+] DEX已导出:", dumpPath);
            }} catch(e) {{
                console.log("[-] 导出失败:", e);
            }}
        }}
        
        return this.$init(file);
    }};
    
    console.log("[+] DEX Dump设置完成");
}});
""",
}

def generate_script(script_type, **kwargs):
    """生成脚本"""
    from datetime import datetime
    
    template = TEMPLATES.get(script_type)
    if not template:
        print(f"[-] 未知的脚本类型: {script_type}")
        return None
    
    # 填充模板
    params = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        **kwargs
    }
    
    # 特殊处理关键字列表
    if 'keywords' in params:
        keywords = params['keywords'].split(',')
        params['keywords_list'] = ', '.join([f'"{kw.strip()}"' for kw in keywords])
    
    script = template.format(**params)
    return script

def main():
    parser = argparse.ArgumentParser(description='Frida Hook脚本生成器')
    parser.add_argument('--type', required=True, 
                       choices=['ssl', 'hook-class', 'hook-method', 'anti-detect', 'trace', 'dump-dex'],
                       help='脚本类型')
    parser.add_argument('--class', dest='class_name', help='目标类名（完整包名）')
    parser.add_argument('--method', dest='method_name', help='目标方法名')
    parser.add_argument('--keywords', help='追踪的关键字（逗号分隔）')
    parser.add_argument('--output', '-o', help='输出文件名')
    
    args = parser.parse_args()
    
    # 参数验证
    if args.type == 'hook-class' and not args.class_name:
        print("[-] hook-class类型需要--class参数")
        return
    
    if args.type == 'hook-method' and (not args.class_name or not args.method_name):
        print("[-] hook-method类型需要--class和--method参数")
        return
    
    if args.type == 'trace' and not args.keywords:
        print("[-] trace类型需要--keywords参数")
        return
    
    # 生成脚本
    script = generate_script(
        args.type,
        class_name=args.class_name,
        method_name=args.method_name,
        keywords=args.keywords
    )
    
    if not script:
        return
    
    # 输出文件名
    if args.output:
        output_file = args.output
    else:
        type_map = {
            'ssl': 'hook_ssl_unpin.js',
            'hook-class': f'hook_{args.class_name.split(".")[-1]}.js' if args.class_name else 'hook_class.js',
            'hook-method': f'hook_{args.method_name}.js' if args.method_name else 'hook_method.js',
            'anti-detect': 'hook_anti_detect.js',
            'trace': 'hook_trace.js',
            'dump-dex': 'hook_dump_dex.js',
        }
        output_file = type_map[args.type]
    
    # 保存脚本
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(script)
    
    print(f"[+] 脚本已生成: {output_file}")
    print(f"\n使用方法:")
    print(f"  frida -U -f <包名> -l {output_file} --no-pause")
    print(f"  或")
    print(f"  frida -U <包名> -l {output_file}")

if __name__ == '__main__':
    main()
