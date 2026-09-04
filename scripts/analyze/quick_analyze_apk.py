"""
自动化APK分析工具
快速提取、反编译、分析APK的关键信息

使用方法:
    python quick_analyze_apk.py <包名>
    python quick_analyze_apk.py com.example.app
"""

import subprocess
import os
import sys
import json
from pathlib import Path

# 工具自动探测（PATH -> 常见安装位置 -> toolenv_extra.py 兜底）
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
import toolenv

ADB = None       # str: adb 可执行路径
JADX_CMD = None  # list: argv 前缀，如 [java, -jar, jadx.jar] 或 [jadx.bat]
APKTOOL_CMD = None


def init_tools():
    """解析工具路径；缺失时打印安装提示并退出。"""
    global ADB, JADX_CMD, APKTOOL_CMD
    ADB = toolenv.require('adb')
    JADX_CMD = toolenv.require_cmd('jadx')
    APKTOOL_CMD = toolenv.require_cmd('apktool')
    print(f"[+] adb:     {ADB}")
    print(f"[+] jadx:    {' '.join(JADX_CMD)}")
    print(f"[+] apktool: {' '.join(APKTOOL_CMD)}")

def run_cmd(cmd, shell=True):
    """执行命令并返回输出"""
    try:
        result = subprocess.run(cmd, shell=shell, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        return result.stdout + result.stderr
    except Exception as e:
        return f"Error: {e}"

def extract_apk(package_name):
    """从设备提取APK"""
    print(f"[1/6] 获取APK路径...")
    output = run_cmd(f'"{ADB}" shell pm path {package_name}')
    
    if 'package:' not in output:
        print(f"[-] 未找到包: {package_name}")
        return None
    
    apk_path = output.strip().replace('package:', '')
    print(f"[+] APK路径: {apk_path}")
    
    print(f"[2/6] 拉取APK到本地...")
    local_apk = f"{package_name}.apk"
    run_cmd(f'"{ADB}" pull {apk_path} {local_apk}')
    
    if os.path.exists(local_apk):
        print(f"[+] APK已保存: {local_apk}")
        return local_apk
    else:
        print("[-] APK拉取失败")
        return None

def decompile_jadx(apk_file):
    """使用jadx反编译"""
    output_dir = f"{apk_file.replace('.apk', '')}_jadx"
    print(f"[3/6] jadx反编译到 {output_dir}...")
    
    cmd = ' '.join(f'"{x}"' for x in JADX_CMD) + f' -d {output_dir} --no-res {apk_file}'
    run_cmd(cmd)
    
    if os.path.exists(output_dir):
        print(f"[+] jadx反编译完成")
        return output_dir
    else:
        print("[-] jadx反编译失败")
        return None

def decompile_apktool(apk_file):
    """使用apktool解包"""
    output_dir = f"{apk_file.replace('.apk', '')}_apktool"
    print(f"[4/6] apktool解包到 {output_dir}...")
    
    cmd = ' '.join(f'"{x}"' for x in APKTOOL_CMD) + f' d {apk_file} -o {output_dir}'
    run_cmd(cmd)
    
    if os.path.exists(output_dir):
        print(f"[+] apktool解包完成")
        return output_dir
    else:
        print("[-] apktool解包失败")
        return None

def analyze_manifest(apktool_dir):
    """分析AndroidManifest.xml"""
    print(f"[5/6] 分析Manifest...")
    manifest_path = os.path.join(apktool_dir, 'AndroidManifest.xml')
    
    if not os.path.exists(manifest_path):
        print("[-] Manifest文件不存在")
        return {}
    
    with open(manifest_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    info = {
        'debuggable': 'android:debuggable="true"' in content,
        'allowBackup': 'android:allowBackup="true"' in content,
        'networkSecurityConfig': 'android:networkSecurityConfig' in content,
        'usesCleartextTraffic': 'android:usesCleartextTraffic="true"' in content,
    }
    
    # 提取权限
    import re
    permissions = re.findall(r'<uses-permission android:name="([^"]+)"', content)
    info['permissions'] = permissions
    
    # 提取导出组件
    exported_components = re.findall(r'<(activity|service|receiver|provider)[^>]*android:exported="true"[^>]*android:name="([^"]+)"', content)
    info['exported_components'] = [f"{comp[0]}: {comp[1]}" for comp in exported_components]
    
    print(f"[+] Debuggable: {info['debuggable']}")
    print(f"[+] AllowBackup: {info['allowBackup']}")
    print(f"[+] 权限数量: {len(info['permissions'])}")
    print(f"[+] 导出组件数量: {len(info['exported_components'])}")
    
    return info

def search_keywords(jadx_dir):
    """搜索敏感关键词"""
    print(f"[6/6] 搜索敏感关键词...")
    
    keywords = {
        '加密': ['encrypt', 'decrypt', 'cipher', 'aes', 'des', 'rsa'],
        '签名': ['sign', 'signature', 'md5', 'sha', 'hmac'],
        '网络': ['okhttp', 'retrofit', 'http', 'api', 'url'],
        '密钥': ['key', 'secret', 'token', 'password'],
    }
    
    results = {}
    sources_dir = os.path.join(jadx_dir, 'sources')
    
    if not os.path.exists(sources_dir):
        print("[-] sources目录不存在")
        return results
    
    for category, kws in keywords.items():
        results[category] = []
        
        for root, dirs, files in os.walk(sources_dir):
            for file in files:
                if not file.endswith('.java'):
                    continue
                
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read().lower()
                        
                        for kw in kws:
                            if kw in content:
                                rel_path = os.path.relpath(filepath, sources_dir)
                                results[category].append((kw, rel_path))
                                break
                except:
                    pass
    
    for category, matches in results.items():
        print(f"[+] {category}: 找到 {len(matches)} 个相关文件")
    
    return results

def generate_report(package_name, manifest_info, keyword_results):
    """生成分析报告"""
    report_file = f"{package_name}_analysis_report.json"
    
    report = {
        'package_name': package_name,
        'manifest_info': manifest_info,
        'keyword_results': {k: [f"{kw} in {path}" for kw, path in v] for k, v in keyword_results.items()},
        'security_issues': []
    }
    
    # 安全问题检查
    if manifest_info.get('debuggable'):
        report['security_issues'].append('应用可调试（debuggable=true）')
    
    if manifest_info.get('allowBackup'):
        report['security_issues'].append('允许备份（allowBackup=true），数据可能被提取')
    
    if manifest_info.get('usesCleartextTraffic'):
        report['security_issues'].append('允许明文流量（usesCleartextTraffic=true）')
    
    if manifest_info.get('exported_components'):
        report['security_issues'].append(f'存在 {len(manifest_info["exported_components"])} 个导出组件')
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n[+] 分析报告已保存: {report_file}")
    
    # 打印摘要
    print("\n========== 分析摘要 ==========")
    print(f"包名: {package_name}")
    print(f"安全问题: {len(report['security_issues'])}")
    for issue in report['security_issues']:
        print(f"  - {issue}")
    
    print("\n关键文件统计:")
    for category, matches in keyword_results.items():
        if matches:
            print(f"  {category}: {len(matches)} 个文件")

def main():
    if len(sys.argv) < 2:
        print("用法: python quick_analyze_apk.py <包名>")
        print("示例: python quick_analyze_apk.py com.example.app")
        sys.exit(1)
    
    package_name = sys.argv[1]
    
    print("=" * 50)
    print(f"Android APK 快速分析工具")
    print(f"目标包名: {package_name}")
    print("=" * 50)

    # 解析工具路径（缺失时给出安装提示并退出）
    init_tools()

    # 步骤1-2: 提取APK
    apk_file = extract_apk(package_name)
    if not apk_file:
        sys.exit(1)
    
    # 步骤3: jadx反编译
    jadx_dir = decompile_jadx(apk_file)
    
    # 步骤4: apktool解包
    apktool_dir = decompile_apktool(apk_file)
    
    # 步骤5: 分析Manifest
    manifest_info = {}
    if apktool_dir:
        manifest_info = analyze_manifest(apktool_dir)
    
    # 步骤6: 搜索关键词
    keyword_results = {}
    if jadx_dir:
        keyword_results = search_keywords(jadx_dir)
    
    # 生成报告
    generate_report(package_name, manifest_info, keyword_results)
    
    print("\n[+] 分析完成！")
    print(f"\n输出目录:")
    print(f"  - {apk_file} (原始APK)")
    if jadx_dir:
        print(f"  - {jadx_dir}/ (Java代码)")
    if apktool_dir:
        print(f"  - {apktool_dir}/ (Smali代码)")
    print(f"  - {package_name}_analysis_report.json (分析报告)")

if __name__ == '__main__':
    main()
