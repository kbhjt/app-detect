#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Android 动态分析自动化脚本
功能：启动Docker模拟器、安装APK、配置Frida、执行隐私合规检测
集成Camille项目的完整隐私检测功能，支持第三方SDK检测和Excel报告生成
"""

import subprocess
import time
import sys
import os
import traceback
from datetime import datetime

# 配置参数
CONTAINER_NAME = "android-frida-container"
DOCKER_IMAGE = "my-android-frida:11.0"
EMULATOR_DEVICE = "Nexus 5"  # Android 模拟器设备型号
VNC_PORT = 6080
MAX_BOOT_TIME = 300  # 最大启动时间（秒）
CHECK_INTERVAL = 5   # 状态检查间隔（秒）
SDK_JSON_PATH = "/opt/camille/sdk.json"  # SDK配置文件路径
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



# ==================== 第三方SDK检测类 ====================

class ThirdPartySdk:
    """第三方SDK检测类（完整camille功能）"""
    
    def __init__(self):
        try:
            self.third_party_sdk = self.__load_third_party_sdk()
            self.sdk_list = [s['package_name'] for s in self.third_party_sdk]
        except Exception as e:
            log('加载第三方SDK失败，关闭第三方SDK检测', "WARN")
            self.third_party_sdk = []
            self.sdk_list = []

    def __load_third_party_sdk(self):
        """加载第三方sdk规则"""
        result = []
        try:
            # 尝试多个路径
            sdk_paths = [
                SDK_JSON_PATH,  # Docker容器内路径
                os.path.join(os.getcwd(), 'camille/utlis/sdk.json'),
                os.path.join(os.path.dirname(__file__), '../camille/utlis/sdk.json'),
                os.path.join(os.path.dirname(__file__), 'sdk.json')
            ]
            
            sdk_path = None
            for path in sdk_paths:
                if os.path.isfile(path):
                    sdk_path = path
                    break
            
            if sdk_path:
                with open(sdk_path, 'r', encoding='utf-8') as f:
                    sdk_rule = f.read()
                result = literal_eval(sdk_rule)
                log(f"成功加载第三方SDK规则: {len(result)} 个SDK", "SUCCESS")
            else:
                log('未找到sdk.json文件', "WARN")
        except Exception as e:
            log(f'加载第三方SDK失败: {e}', "ERROR")
        return result

    def get_sdk_name(self, package_name):
        """返回sdk名称"""
        sdk_name = ''
        for s in self.third_party_sdk:
            if s['package_name'] == package_name:
                sdk_name = s['sdk_name']
        return sdk_name

    def is_third_party(self, content):
        """判断是否为第三方sdk调用"""
        result = 'APP本身'
        for sdk in self.sdk_list:
            if sdk in content:
                result = self.get_sdk_name(sdk)
                break
        return result


# ==================== Excel报告生成 ====================

def write_excel(data, file_name):
    """
    将结果写入Excel（完整camille格式）
    支持空数据（只生成表头）
    """
    try:
        import xlwt
        
        # 确保目录存在
        os.makedirs(os.path.dirname(file_name), exist_ok=True)
        
        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet('隐私合规检测报告')
        
        # 标题样式
        title_style = xlwt.XFStyle()
        title_font = xlwt.Font()
        title_font.bold = True
        title_font.height = 30 * 11
        title_style.font = title_font
        
        # 对齐方式
        alignment = xlwt.Alignment()
        alignment.horz = xlwt.Alignment.HORZ_CENTER
        alignment.vert = xlwt.Alignment.VERT_CENTER
        title_style.alignment = alignment
        
        # 写入标题（与camille完全一致）
        headers = ['隐私政策状态', '时间点', '行为主体', '操作行为', '行为描述', '传入参数', '调用堆栈']
        col_widths = [20 * 300, 20 * 300, 20 * 300, 20 * 300, 20 * 400, 20 * 400, 20 * 1200]
        
        for i, (header, width) in enumerate(zip(headers, col_widths)):
            worksheet.write(0, i, header, title_style)
            worksheet.col(i).width = width
        
        worksheet.row(0).height_mismatch = True
        worksheet.row(0).height = 20 * 25
        
        # 内容样式
        content_style = xlwt.XFStyle()
        content_font = xlwt.Font()
        content_font.height = 20 * 11
        content_style.font = content_font
        content_style.alignment = alignment
        content_style.alignment.wrap = 1
        
        # 写入数据（如果有）
        if data:
            for i, row_data in enumerate(data):
                row_num = i + 1
                worksheet.write(row_num, 0, row_data.get('privacy_policy_status', ''), content_style)
                worksheet.write(row_num, 1, row_data.get('alert_time', ''), content_style)
                worksheet.write(row_num, 2, row_data.get('subject_type', ''), content_style)
                worksheet.write(row_num, 3, row_data.get('action', ''), content_style)
                worksheet.write(row_num, 4, row_data.get('messages', ''), content_style)
                worksheet.write(row_num, 5, row_data.get('arg', ''), content_style)
                worksheet.write(row_num, 6, row_data.get('stacks', ''), content_style)
        
        workbook.save(file_name)
        
        # 验证文件是否真的被保存
        if os.path.exists(file_name):
            file_size = os.path.getsize(file_name)
            if data:
                log(f"✅ Excel报告已生成: {file_name}", "SUCCESS")
                log(f"📊 共记录 {len(data)} 条隐私行为", "INFO")
                log(f"📁 文件大小: {file_size} 字节", "INFO")
            else:
                log(f"✅ 空报告已生成: {file_name}", "SUCCESS")
                log(f"📊 未检测到隐私行为（仅包含表头）", "INFO")
                log(f"📁 文件大小: {file_size} 字节", "INFO")
            return True
        else:
            log(f"❌ 文件保存失败，文件不存在: {file_name}", "ERROR")
            return False
        
    except ImportError:
        log("❌ 未安装xlwt模块，无法导出Excel", "ERROR")
        log("安装方法: pip3 install xlwt", "INFO")
        return False
    except Exception as e:
        log(f"❌ 导出Excel失败: {e}", "ERROR")
        log(traceback.format_exc(), "ERROR")
        return False


# ==================== Frida隐私检测Hook ====================

def start_frida_hook(package_name, use_module=None, wait_time=0, 
                     duration=300, is_show=True, is_attach=True, export_file=None):
    """
    启动 Frida 隐私合规检测（集成完整camille功能）
    
    Args:
        package_name: 应用包名
        use_module: 使用的模块 {"type": "all/use/nouse", "data": [...]}
        wait_time: 延迟hook时间（秒）
        duration: 检测持续时间（秒），默认300秒（5分钟）
        is_show: 是否显示实时告警
        is_attach: 是否使用attach模式
        export_file: 导出文件路径
    """
    log(f"🔍 启动Frida隐私合规检测: {package_name}")
    
    # 通过Docker容器执行隐私检测
    return frida_hook_via_docker(
        package_name=package_name,
        use_module=use_module,
        wait_time=wait_time,
        duration=duration,
        is_show=is_show,
        is_attach=is_attach,
        export_file=export_file
    )



def frida_hook_via_docker(package_name, use_module=None, wait_time=0,
                         duration=300, is_show=True, is_attach=True, export_file=None):
    """
    通过Docker容器执行Frida隐私检测
    """
    try:
        # 检查Docker容器是否运行
        log("检查Docker容器状态...", "INFO")
        if not check_container_running():
            log(f"❌ Docker容器 {CONTAINER_NAME} 未运行", "ERROR")
            log("请先启动Android模拟器容器", "ERROR")
            return False
        
        log(f"✅ Docker容器正在运行", "SUCCESS")
        log(f"目标应用: {package_name}", "INFO")
        log(f"延迟Hook: {wait_time}秒", "INFO")
        log(f"检测时长: {duration}秒", "INFO")
        log(f"模式: {'Attach' if is_attach else 'Spawn'}", "INFO")
        if export_file:
            log(f"📊 报告文件参数: {export_file}", "INFO")
        else:
            log("⚠️  未指定报告文件", "WARN")
        
        # 构建在容器内执行的Python命令
        cmd_parts = [
            "python3", "/opt/camille/frida_privacy_check.py",
            str(package_name)
        ]
        
        # 添加延迟时间参数
        if wait_time > 0:
            cmd_parts.extend(["-t", str(wait_time)])
        
        # 添加检测时长参数
        if duration > 0:
            cmd_parts.extend(["-d", str(duration)])
        
        # 添加模块参数
        if use_module:
            module_type = use_module.get("type", "all")
            module_data = use_module.get("data", [])
            
            if module_type == "use" and module_data:
                data_str = module_data if isinstance(module_data, str) else ','.join(module_data)
                cmd_parts.extend(["-u", data_str])
            elif module_type == "nouse" and module_data:
                data_str = module_data if isinstance(module_data, str) else ','.join(module_data)
                cmd_parts.extend(["-nu", data_str])
        
        # 添加显示参数
        if not is_show:
            cmd_parts.append("-ns")
        
        # 添加模式参数（spawn模式不需要-ia参数）
        if is_attach:
            cmd_parts.append("-ia")
        
        # 添加导出文件参数
        if export_file:
            cmd_parts.extend(["-f", export_file])
        
        frida_command = " ".join(cmd_parts)
        log(f"执行命令: {frida_command}", "INFO")
        
        # 在Docker容器中执行frida命令，实时输出
        log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "INFO")
        log("📱 Frida隐私检测开始（实时输出）", "INFO")
        log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "INFO")
        
        # 使用docker exec执行
        docker_cmd = ["docker", "exec", "-u", "0", "-i", CONTAINER_NAME, "bash", "-c", frida_command]
        
        log(f"执行的docker命令: {docker_cmd}", "INFO")
        
        process = subprocess.Popen(
            docker_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # 优化的日志输出 - 减少前端卡顿
        log_buffer = []
        last_output_time = time.time()
        data_count = 0
        
        # 日志过滤常量
        IMPORTANT_KEYWORDS = [
            "✅", "❌", "⚠️", "🔍", "📊", "SUCCESS", "ERROR", "WARN",
            "Hook脚本加载成功", "监控中", "检测完成", "数据已收集",
            "应用已启动", "已附加到进程", "Hook初始化完成"
        ]
        
        SKIP_KEYWORDS = [
            "调用堆栈：", "android.app.", "com.android.", "java.lang.",
            "Native Method", "Handler.java", "Looper.java"
        ]
        
        def should_output_line(line):
            """判断是否应该输出这行日志"""
            line = line.strip()
            if not line:
                return False
            
            # 重要日志始终输出
            for keyword in IMPORTANT_KEYWORDS:
                if keyword in line:
                    return True
            
            # 过滤掉频繁的调试信息
            for keyword in SKIP_KEYWORDS:
                if keyword in line:
                    return False
            
            # APP行为数据始终输出
            return "APP行为：" in line or "行为主体：" in line
        
        def flush_log_buffer():
            """批量输出日志缓冲区"""
            if log_buffer:
                # 合并多行日志，避免过于频繁的输出
                combined_log = "\n".join(log_buffer)
                print(combined_log, flush=True)
                log_buffer.clear()
        
        # 实时输出（优化版）
        for line in iter(process.stdout.readline, ''):
            if line:
                line = line.rstrip()
                
                # 统计数据收集进度
                if "数据已收集:" in line:
                    try:
                        count = int(line.split("数据已收集:")[1].split("条")[0].strip())
                        if count > data_count:
                            data_count = count
                            # 每10条数据输出一次进度
                            if count % 10 == 0 or count <= 10:
                                print(f"📊 隐私数据收集进度: {count} 条", flush=True)
                        continue
                    except:
                        pass
                
                # 判断是否应该输出
                if should_output_line(line):
                    log_buffer.append(line)
                
                # 控制输出频率：每0.5秒或缓冲区满10行时输出
                current_time = time.time()
                if (current_time - last_output_time >= 0.5) or len(log_buffer) >= 10:
                    flush_log_buffer()
                    last_output_time = current_time
        
        # 输出剩余的日志
        flush_log_buffer()
        
        # 输出最终统计
        if data_count > 0:
            print(f"🎯 检测完成，共收集到 {data_count} 条隐私行为数据", flush=True)
        
        return_code = process.wait()
        
        log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "INFO")
        log("📱 Frida隐私检测结束", "INFO")
        log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "INFO")
        
        if return_code == 0:
            log("✅ Frida检测成功完成", "SUCCESS")
            if export_file:
                log(f"📊 报告已保存到容器中: {export_file}", "SUCCESS")
                # 提示如何导出报告
                log(f"💡 导出报告到宿主机:", "INFO")
                log(f"   docker cp {CONTAINER_NAME}:{export_file} .", "INFO")
            return True
        else:
            log(f"⚠️  Frida检测执行异常，返回代码: {return_code}", "WARN")
            return False
        
    except KeyboardInterrupt:
        log("检测被用户中断", "WARN")
        return False
    except Exception as e:
        log(f"❌ 执行失败: {e}", "ERROR")
        log(traceback.format_exc(), "ERROR")
        return False


def main():
    """主函数"""
    log("=" * 60)
    log("Android 动态分析自动化脚本启动")
    log("=" * 60)
    
    # 参数调试信息
    log(f"🔍 接收参数: APK={sys.argv[1] if len(sys.argv) > 1 else 'None'}, TaskID={sys.argv[4] if len(sys.argv) > 4 else 'None'}")

    # 从命令行参数获取APK路径、包名和taskId
    # Java后端调用格式: python3 script.py apkPath '' '' taskId
    if len(sys.argv) < 2:
        log("用法: python3 android_dynamic_analysis.py <apk_path> [package_name] [reserved1] [reserved2] [task_id]", "ERROR")
        sys.exit(1)

    apk_path = sys.argv[1]
    package_name_arg = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else None
    # 跳过第3、4个参数（reserved）
    task_id_arg = sys.argv[4] if len(sys.argv) > 4 else None

    log(f"目标APK: {apk_path}")
    if package_name_arg:
        log(f"指定包名: {package_name_arg}")
    if task_id_arg:
        log(f"任务ID: {task_id_arg}")

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
        
        # 生成报告文件路径（使用taskId以匹配Java后端期望的文件名格式）
        # 优先使用命令行参数中的taskId，如果没有则使用timestamp作为备用
        if task_id_arg:
            task_id = task_id_arg
            log(f"✅ 使用Java后端传递的taskId: {task_id}")
        else:
            task_id = str(int(time.time() * 1000))
            log(f"⚠️  未接收到taskId，使用生成的timestamp: {task_id}", "WARN")
        
        export_file = f"/opt/frida_reports/frida_report_{task_id}.xls"
        log(f"📊 报告文件路径: {export_file}")
        
        # 启动隐私检测（默认5分钟检测时长）
        log("💡 提示：检测将持续5分钟，请在此期间手动操作应用以触发隐私行为")
        log("💡 建议操作：登录、拍照、定位、通讯录、拨号等功能")
        
        start_frida_hook(
            package_name=package_name,
            duration=300,  # 5分钟检测时长
            is_attach=False,  # 使用spawn模式
            export_file=export_file
        )

        log("\n" + "=" * 60)
        log("Android隐私合规检测完成！")
        log(f"VNC访问地址: http://192.168.216.146:{VNC_PORT}/vnc_lite.html")
        if export_file:
            log(f"📊 检测报告: {export_file}")
            log(f"💡 导出报告: docker cp {CONTAINER_NAME}:{export_file} .")
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


