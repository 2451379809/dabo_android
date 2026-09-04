/**
 * list_modules.js — 列出目标进程已加载的全部模块
 *
 * 用法（spawn 模式，等 3 秒让模块加载完）:
 *   frida -U -f com.target.app -l list_modules.js
 * 用法（attach 模式）:
 *   frida -U com.target.app -l list_modules.js
 *
 * 说明:
 * - [APP] 前缀 = 应用目录下的库（/data/...），通常是分析目标
 * - 只关心特定库时，把下面 KEYWORD 改成库名子串（如 "libgame"）
 */
var KEYWORD = null;        // 例: "libgame" / "metasec" / null=全部
var DELAY_MS = 3000;       // spawn 模式等待应用库加载

setTimeout(function () {
    var mods = Process.enumerateModules();
    var shown = 0;
    console.log("[*] 共加载 " + mods.length + " 个模块" + (KEYWORD ? "（过滤: " + KEYWORD + "）" : "") + "\n");

    mods.forEach(function (m) {
        if (KEYWORD && m.name.toLowerCase().indexOf(KEYWORD.toLowerCase()) === -1) {
            return;
        }
        shown++;
        var tag = m.path.indexOf("/data/") === 0 ? "[APP]" : "[SYS]";
        console.log(tag + " " + m.name + "  base=" + m.base + "  size=" + m.size + "  " + m.path);
    });

    console.log("\n[*] 显示 " + shown + " 个模块");
    console.log("[*] 提示: dump 任意 SO 可用 dump_so.js / dump_so.py");
}, DELAY_MS);
