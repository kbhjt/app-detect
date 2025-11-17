#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Android 动态分析自动化脚本
功能：启动Docker模拟器、安装APK、配置Frida、执行Hook监控
"""

import subprocess
import time
import sys
import json
import os
from datetime import datetime

# 配置参数
CONTAINER_NAME = "android-frida-container"
DOCKER_IMAGE = "my-android-frida:11.0"
VNC_PORT = 6080
EMULATOR_DEVICE = "Nexus 5"
MAX_BOOT_TIME = 300  # 最大启动时间（秒）- 增加到5分钟
CHECK_INTERVAL = 5   # 状态检查间隔（秒）- 减少频繁检查
FRIDA_SCRIPT_PATH = "/opt/frida/hook.js"  # Frida hook脚本路径
REUSE_CONTAINER = True  # 是否复用已存在的容器


def log(message, level="INFO"):
    """输出日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] [{level}] {message}"
    print(log_msg, flush=True)
    return log_msg


def run_command(command, shell=False, capture_output=True, timeout=30):
    """执行系统命令"""
    try:
        if shell:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=capture_output,
                text=True,
                timeout=timeout
            )
        else:
            result = subprocess.run(
                command,
                capture_output=capture_output,
                text=True,
                timeout=timeout
            )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        log("命令执行超时", "ERROR")
        return -1, "", "命令执行超时"
    except Exception as e:
        log(f"命令执行异常: {str(e)}", "ERROR")
        return -1, "", str(e)


def run_command_realtime(command, shell=False):
    """执行系统命令并实时输出（用于Frida等需要持续输出的命令）"""
    try:
        if shell:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
        else:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
        
        # 实时读取并输出
        for line in iter(process.stdout.readline, ''):
            if line:
                print(line.rstrip(), flush=True)
        
        process.wait()
        return process.returncode
    except Exception as e:
        log(f"命令执行异常: {str(e)}", "ERROR")
        return -1


def check_container_exists():
    """检查容器是否存在"""
    log("检查容器是否已存在...")
    code, stdout, _ = run_command(
        ["docker", "ps", "-a", "--filter", f"name={CONTAINER_NAME}", "--format", "{{.Names}}"])
    return CONTAINER_NAME in stdout


def remove_container():
    """删除已存在的容器"""
    log(f"删除容器: {CONTAINER_NAME}")
    code, stdout, stderr = run_command(["docker", "rm", "-f", CONTAINER_NAME])
    if code == 0:
        log("容器删除成功")
        return True
    else:
        log(f"容器删除失败: {stderr}", "ERROR")
        return False


def start_docker_container():
    """启动 Docker 容器（支持复用已存在的容器）"""
    log("检查 Android 模拟器容器...")

    # 检查容器是否已存在且可用
    if check_container_exists():
        if REUSE_CONTAINER:
            log("发现已存在的容器，检查是否可用...")
            
            # 如果容器正在运行
            if check_container_running():
                log("容器正在运行，检查模拟器状态...")
                
                # 检查模拟器是否已就绪
                if check_adb_ready():
                    log("✅ 容器和模拟器都已就绪，直接使用！", "SUCCESS")
                    return True
                else:
                    log("模拟器尚未就绪，需要等待启动完成...", "WARN")
                    return True  # 容器在运行，只是模拟器还在启动中
            else:
                # 容器存在但未运行，尝试启动
                log("容器已停止，尝试重新启动...")
                code, _, _ = run_command(["docker", "start", CONTAINER_NAME])
                if code == 0:
                    log("容器重启成功")
                    return True
                else:
                    log("容器重启失败，删除后重新创建", "WARN")
                    remove_container()
                    time.sleep(2)
        else:
            # 不复用，直接删除
            log("发现已存在的容器，正在删除...")
            remove_container()
            time.sleep(2)

    # 创建新容器
    log("创建新的容器...")
    command = [
        "docker", "run", "-d",
        "-p", f"{VNC_PORT}:6080",
        "--privileged",
        "-e", f"EMULATOR_DEVICE={EMULATOR_DEVICE}",
        "-e", "WEB_VNC=true",
        "--device", "/dev/kvm",
        "--name", CONTAINER_NAME,
        DOCKER_IMAGE
    ]

    code, stdout, stderr = run_command(command, timeout=60)

    if code == 0:
        log(f"✅ 容器创建成功，Container ID: {stdout[:12]}", "SUCCESS")
        return True
    else:
        log(f"❌ 容器创建失败: {stderr}", "ERROR")
        return False


def check_container_running():
    """检查容器是否在运行"""
    code, stdout, _ = run_command(
        f"docker inspect -f '{{{{.State.Running}}}}' {CONTAINER_NAME}",
        shell=True
    )
    return code == 0 and "true" in stdout.lower()


def check_adb_ready():
    """检查adb是否可用（更可靠的状态检查）"""
    try:
        # 检查adb devices是否能看到设备
        code, stdout, stderr = run_command([
            "docker", "exec", "-u", "0", CONTAINER_NAME,
            "adb", "devices"
        ], timeout=10)
        
        if code == 0 and "emulator" in stdout:
            # 进一步检查设备是否完全启动
            code2, stdout2, _ = run_command([
                "docker", "exec", "-u", "0", CONTAINER_NAME,
                "adb", "shell", "getprop", "sys.boot_completed"
            ], timeout=10)
            
            if code2 == 0 and "1" in stdout2:
                return True
        return False
    except Exception as e:
        log(f"检查adb状态异常: {e}", "WARN")
        return False


def is_container_usable():
    """检查容器是否可用（正在运行且模拟器已就绪）"""
    if not check_container_running():
        return False
    
    # 检查adb是否就绪
    if check_adb_ready():
        log("发现可用的容器，模拟器已就绪！", "SUCCESS")
        return True
    
    return False


def check_emulator_status():
    """检查模拟器状态（使用多种方法）"""
    # 首先检查容器是否还在运行
    if not check_container_running():
        log("容器已停止", "ERROR")
        return "CONTAINER_STOPPED"

    # 方法1：检查adb是否就绪（最可靠）
    if check_adb_ready():
        return "READY"
    
    # 方法2：读取 device_status 文件（备用）
    command = ["docker", "exec", "-u", "0", CONTAINER_NAME, "cat", "device_status"]
    code, stdout, stderr = run_command(command, timeout=5)

    if code == 0 and stdout.strip():
        status = stdout.strip()
        if status == "READY":
            return "READY"
        elif status in ["BOOTING", "STARTING"]:
            return "BOOTING"

    # 方法3：检查adb devices（判断是否在启动中）
    code, stdout, _ = run_command([
        "docker", "exec", "-u", "0", CONTAINER_NAME,
        "adb", "devices"
    ], timeout=5)
    
    if code == 0 and "emulator" in stdout:
        return "BOOTING"  # 设备存在但未完全启动
    
    return "BOOTING"  # 默认认为正在启动，而不是UNKNOWN


def wait_for_emulator_ready(max_retries=2):
    """等待模拟器启动完成（优化版，减少不必要的重启）"""
    
    for retry in range(max_retries):
        if retry > 0:
            log(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            log(f"第 {retry + 1} 次尝试启动模拟器...", "WARN")
            log(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            
            # 删除有问题的容器
            if check_container_exists():
                remove_container()
                time.sleep(3)
            
            # 重新启动
            if not start_docker_container():
                log("重新启动容器失败", "ERROR")
                continue
            time.sleep(10)  # 给容器足够的启动时间

        log("等待模拟器启动完成...")
        log(f"最大等待时间: {MAX_BOOT_TIME} 秒 ({MAX_BOOT_TIME//60} 分钟)")
        
        start_time = time.time()
        last_status = ""
        last_log_time = 0
        booting_count = 0  # 记录BOOTING状态的次数

        while True:
            elapsed = time.time() - start_time

            # 检查状态
            status = check_emulator_status()

            # 每30秒或状态变化时输出日志
            should_log = (status != last_status) or (elapsed - last_log_time > 30)
            
            if should_log:
                progress = min(100, int((elapsed / MAX_BOOT_TIME) * 100))
                log(f"模拟器状态: {status} | 进度: {progress}% | 已等待: {int(elapsed)}秒")
                last_status = status
                last_log_time = elapsed

            # 状态判断
            if status == "READY":
                log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                log("✅ 模拟器启动成功！", "SUCCESS")
                log(f"⏱️  总耗时: {int(elapsed)} 秒")
                log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                return True

            elif status == "CONTAINER_STOPPED":
                log("容器意外停止", "ERROR")
                break  # 跳出循环，进入下一次重试

            elif status == "BOOTING":
                booting_count += 1
                # 正常启动中，继续等待
                time.sleep(CHECK_INTERVAL)

            else:
                # 其他状态，继续等待
                time.sleep(CHECK_INTERVAL)

            # 检查是否超时
            if elapsed > MAX_BOOT_TIME:
                log(f"⏰ 等待超时（{MAX_BOOT_TIME}秒）", "WARN")

                # 超时前最后一次详细检查
                log("执行最后一次详细检查...")
                final_status = check_emulator_status()
                
                if final_status == "READY":
                    log("✅ 最终检查：模拟器已就绪！", "SUCCESS")
                    return True
                
                # 检查容器日志
                log("查看容器日志（最后20行）：")
                code, logs, _ = run_command([
                    "docker", "logs", "--tail", "20", CONTAINER_NAME
                ], timeout=10)
                if code == 0:
                    for line in logs.split('\n')[-10:]:
                        if line.strip():
                            log(f"  {line.strip()}", "WARN")
                
                if retry < max_retries - 1:
                    log("准备重试...", "WARN")
                    break
                else:
                    log("已达到最大重试次数", "ERROR")

    log("❌ 模拟器启动失败", "ERROR")
    log("建议：")
    log("  1. 检查服务器资源（CPU、内存、磁盘）", "ERROR")
    log("  2. 检查Docker和KVM是否正常", "ERROR")
    log("  3. 手动执行: docker logs android-frida-container", "ERROR")
    log("  4. 考虑增加 MAX_BOOT_TIME 配置", "ERROR")
    return False


def install_apk(apk_path):
    """在模拟器中安装 APK"""
    log(f"开始安装 APK: {apk_path}")

    # 检查APK文件是否存在
    if not os.path.exists(apk_path):
        log(f"APK文件不存在: {apk_path}", "ERROR")
        return False

    # 将APK复制到容器中
    log("复制APK文件到容器...")
    container_apk_path = f"/tmp/{os.path.basename(apk_path)}"
    
    # 获取APK文件大小
    apk_size_mb = os.path.getsize(apk_path) / (1024 * 1024)
    log(f"APK文件大小: {apk_size_mb:.2f} MB")
    
    # 根据文件大小调整超时时间（大文件需要更长时间）
    copy_timeout = max(60, int(apk_size_mb * 2) + 30)
    
    code, stdout, stderr = run_command([
        "docker", "cp", apk_path, f"{CONTAINER_NAME}:{container_apk_path}"
    ], timeout=copy_timeout)

    if code != 0:
        log(f"复制APK失败: {stderr}", "ERROR")
        return False
    
    log("✅ APK文件复制成功")

    # 在容器中安装APK
    log("正在安装APK到模拟器...")
    log("⏳ APK安装可能需要1-2分钟，请耐心等待...")
    
    # 增加超时时间到120秒（2分钟）
    code, stdout, stderr = run_command([
        "docker", "exec", "-u", "0", CONTAINER_NAME,
        "adb", "install", "-r", container_apk_path
    ], timeout=120)

    if code == 0 and "Success" in stdout:
        log("✅ APK安装成功！", "SUCCESS")
        return True
    elif code == -1:
        log(f"❌ APK安装超时（120秒），可能APK文件过大或模拟器响应缓慢", "ERROR")
        log(f"完整输出: {stdout}", "ERROR")
        return False
    else:
        log(f"❌ APK安装失败: {stdout} {stderr}", "ERROR")
        return False


def push_frida_server():
    """将 Frida Server 推送到模拟器"""
    log("配置 Frida Server...")
    log("⏳ Frida Server推送可能需要30-60秒...")

    # 执行 push-frida.sh 脚本，增加超时到90秒
    code, stdout, stderr = run_command([
        "docker", "exec", "-u", "0", CONTAINER_NAME,
        "bash", "/opt/frida/push-frida.sh"
    ], timeout=90)

    if code == 0:
        log("✅ Frida Server 配置成功", "SUCCESS")
        if stdout:
            log(stdout)
        return True
    elif code == -1:
        log(f"❌ Frida Server 配置超时（90秒）", "ERROR")
        return False
    else:
        log(f"❌ Frida Server 配置失败: {stderr}", "ERROR")
        return False


def get_package_name_from_filename(apk_path):
    """从APK文件名推断包名"""
    import re
    
    filename = os.path.basename(apk_path)
    log(f"尝试从文件名推断包名: {filename}")
    
    # 移除.apk后缀
    name_without_ext = filename.replace('.apk', '').replace('.APK', '')
    
    # 匹配模式：uuid_com.example.app_version_source 或 com.example.app_version
    # 包名格式：至少包含一个点，由字母数字点组成
    package_pattern = r'(com\.[a-zA-Z0-9_.]+|[a-z]+\.[a-zA-Z0-9_.]+)'
    matches = re.findall(package_pattern, name_without_ext)
    
    if matches:
        # 选择最长的匹配项（通常是完整包名）
        package_name = max(matches, key=len)
        
        # 清理包名：移除尾部的下划线、数字、点
        package_name = re.sub(r'[._\d]+$', '', package_name)
        
        # 验证包名：至少两个部分（如com.example）
        parts = package_name.split('.')
        if len(parts) >= 2 and all(part for part in parts):
            log(f"从文件名推断出包名: {package_name}", "WARN")
            return package_name
    
    log("无法从文件名推断包名", "WARN")
    return None


def get_package_name_from_apk(apk_path):
    """从APK安装后通过adb获取最新安装的包名"""
    log("通过adb获取最新安装的APK包名...")
    
    # 等待一下，确保APK信息已经注册到系统
    time.sleep(3)
    
    # 重试3次获取包名
    for attempt in range(3):
        if attempt > 0:
            log(f"重试获取包名... (第 {attempt + 1} 次)", "WARN")
            time.sleep(2)
        
        # 使用优化的命令：通过文件时间戳获取最新安装的应用包名
        # 这个命令会列出所有第三方应用，获取它们的安装时间，然后返回最新的
        adb_command = (
            'pm list packages -U -f -3 | '
            'while read line; do '
            'pkg=$(echo $line | sed -E "s/.*=//"); '
            'path=$(pm path $pkg | cut -d: -f2); '
            'ts=$(stat -c %Y $path 2>/dev/null); '
            'echo "$ts $pkg"; '
            'done | '
            'sort -nr | head -1 | awk "{print \\$2}"'
        )
        
        code, stdout, stderr = run_command([
            "docker", "exec", "-u", "0", CONTAINER_NAME,
            "adb", "shell", adb_command
        ], timeout=15)
        
        log(f"命令返回码: {code}")
        
        if code == 0 and stdout:
            package_name = stdout.strip()
            
            # 验证包名格式（至少包含一个点）
            if package_name and '.' in package_name and len(package_name) > 3:
                log(f"✅ 检测到最新安装的包名: {package_name}", "SUCCESS")
                return package_name
            else:
                log(f"获取到无效的包名: [{package_name}]", "WARN")
        else:
            log(f"命令执行失败 (code={code}), stderr: {stderr}", "WARN")
    
    # adb方法失败，尝试从文件名推断
    log("adb方法失败，尝试从文件名推断包名...", "WARN")
    package_name = get_package_name_from_filename(apk_path)
    
    if package_name:
        log(f"✅ 使用从文件名推断的包名: {package_name}", "SUCCESS")
        return package_name
    
    log("无法通过任何方法获取包名", "ERROR")
    log("提示：可以在命令行中手动指定包名作为第二个参数", "ERROR")
    return None


def start_app_with_monkey(package_name):
    """使用 monkey 命令启动应用"""
    log(f"使用 monkey 启动应用: {package_name}")

    # 先确保应用没有运行
    log("停止应用（如果正在运行）...")
    run_command([
        "docker", "exec", "-u", "0", CONTAINER_NAME,
        "adb", "shell", "am", "force-stop", package_name
    ])
    time.sleep(1)

    # 使用 monkey 启动应用
    log("启动应用...")
    code, stdout, stderr = run_command([
        "docker", "exec", "-u", "0", CONTAINER_NAME,
        "adb", "shell", "monkey", "-p", package_name,
        "-c", "android.intent.category.LAUNCHER", "1"
    ], timeout=60)

    if code == 0:
        log("✅ 应用启动成功", "SUCCESS")
        time.sleep(3)  # 等待应用完全启动
        return True
    else:
        log(f"❌ 应用启动失败: {stderr}", "ERROR")
        return False


def start_frida_hook(package_name, hook_script=FRIDA_SCRIPT_PATH):
    """启动 Frida Hook 监控（attach 模式）"""
    log(f"启动 Frida Hook 监控: {package_name}")

    # 检查hook脚本是否存在
    code, _, _ = run_command([
        "docker", "exec", "-u", "0", CONTAINER_NAME,
        "test", "-f", hook_script
    ])

    if code != 0:
        log(f"Hook脚本不存在: {hook_script}，创建默认脚本", "WARN")
        # 创建默认的hook脚本
        default_script = """Java.perform(function() {
    console.log("[*] ===================================");
    console.log("[*] Frida Hook Started");
    console.log("[*] ===================================");

    try {
        var context = Java.use("android.app.ActivityThread").currentApplication().getApplicationContext();
        var packageName = context.getPackageName();
        console.log("[*] Package: " + packageName);
    } catch(e) {
        console.log("[*] Could not get package name: " + e);
    }

    // Hook android.util.Log
    try {
        var Log = Java.use("android.util.Log");

        Log.d.overload("java.lang.String", "java.lang.String").implementation = function(tag, msg) {
            console.log("[LOG.D] " + tag + ": " + msg);
            return this.d(tag, msg);
        };

        Log.i.overload("java.lang.String", "java.lang.String").implementation = function(tag, msg) {
            console.log("[LOG.I] " + tag + ": " + msg);
            return this.i(tag, msg);
        };

        Log.e.overload("java.lang.String", "java.lang.String").implementation = function(tag, msg) {
            console.log("[LOG.E] " + tag + ": " + msg);
            return this.e(tag, msg);
        };

        console.log("[*] Hook设置完成，开始监控...");
    } catch(e) {
        console.log("[*] Hook setup error: " + e);
    }

    console.log("[*] ===================================");
});"""
        # 使用临时文件避免shell转义问题
        run_command([
            "docker", "exec", "-u", "0", CONTAINER_NAME,
            "bash", "-c", f"cat > {hook_script} << 'HOOKEOF'\n{default_script}\nHOOKEOF"
        ], shell=False)

    # 步骤1: 使用 monkey 启动应用
    #if not start_app_with_monkey(package_name):
    #    log("应用启动失败，无法继续 Hook", "ERROR")
    #    return False

    # 步骤2: 使用 frida attach 到已运行的应用
    log("正在 attach 到应用进行 Hook...")
    log("=" * 60)
    log("📱 Frida Hook 输出开始（实时显示）")
    log("=" * 60)

    # 使用 frida -U -n (attach by name) 并实时输出
    frida_command = [
        "docker", "exec", "-u", "0", "-i", CONTAINER_NAME,
        "frida", "-U", "-f", package_name, "-l", hook_script
    ]

    log(f"执行 Frida 命令: frida -U -f {package_name} -l {hook_script}")
    
    # 使用实时输出模式执行Frida命令
    return_code = run_command_realtime(frida_command)
    
    if return_code != 0:
        log(f"Frida Hook 执行异常，返回代码: {return_code}", "WARN")
    
    log("=" * 60)
    log("📱 Frida Hook 输出结束")
    log("=" * 60)


def main():
    """主函数"""
    log("=" * 60)
    log("Android 动态分析自动化脚本启动")
    log("=" * 60)

    # 从命令行参数获取APK路径和包名（可选）
    if len(sys.argv) < 2:
        log("用法: python3 android_dynamic_analysis.py <apk_path> [package_name]", "ERROR")
        sys.exit(1)

    apk_path = sys.argv[1]
    package_name_arg = sys.argv[2] if len(sys.argv) > 2 else None

    log(f"目标APK: {apk_path}")
    if package_name_arg:
        log(f"指定包名: {package_name_arg}")

    try:
        # 智能检查：如果容器已就绪，跳过启动步骤
        log("\n[预检查] 检查容器状态...")
        container_ready = False
        
        if check_container_exists() and check_container_running():
            log("发现运行中的容器，检查模拟器状态...")
            if check_adb_ready():
                log("✅ 容器和模拟器都已就绪，跳过启动步骤！", "SUCCESS")
                log("💡 提示：这大大加快了分析速度！")
                container_ready = True
            else:
                log("容器运行中但模拟器未就绪，需要等待...", "WARN")
        
        # 步骤1: 启动Docker容器（如果需要）
        if not container_ready:
            log("\n[步骤 1/5] 启动 Docker 容器...")
            if not start_docker_container():
                log("容器启动失败，终止分析", "ERROR")
                sys.exit(1)

            # 步骤2: 等待模拟器启动
            log("\n[步骤 2/5] 等待模拟器启动...")
            if not wait_for_emulator_ready():
                log("模拟器启动失败，终止分析", "ERROR")
                sys.exit(1)
        else:
            log("\n[步骤 1-2/5] ✅ 已跳过（容器已就绪）")

        time.sleep(2)
        # 步骤3: 安装APK
        log("\n[步骤 3/5] 安装 APK...")
        if not install_apk(apk_path):
            log("APK安装失败，终止分析", "ERROR")
            sys.exit(1)

        # 步骤4: 配置Frida
        log("\n[步骤 4/5] 配置 Frida Server...")
        if not push_frida_server():
            log("Frida配置失败，终止分析", "ERROR")
            sys.exit(1)

        # 步骤5: 启动Frida Hook
        log("\n[步骤 5/5] 启动 Frida Hook 监控...")

        # 如果命令行提供了包名，直接使用；否则尝试获取
        if package_name_arg:
            package_name = package_name_arg
            log(f"使用指定的包名: {package_name}")
        else:
            package_name = get_package_name_from_apk(apk_path)
            if not package_name:
                log("无法获取包名，终止分析", "ERROR")
                log("提示：可以在命令行中手动指定包名", "ERROR")
                log(f"示例: python3 {sys.argv[0]} {apk_path} com.example.app", "ERROR")
                sys.exit(1)

        time.sleep(2)
        start_frida_hook(package_name)

        log("\n" + "=" * 60)
        log("动态分析启动完成！")
        log(f"VNC访问地址: http://192.168.216.146:{VNC_PORT}/vnc_lite.html")
        log("=" * 60)

    except KeyboardInterrupt:
        log("\n分析被用户中断", "WARN")
        sys.exit(0)
    except Exception as e:
        log(f"发生异常: {str(e)}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


