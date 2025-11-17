#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Frida隐私合规检测脚本 - 完整集成Camille项目到RuoYi系统
支持Docker容器执行和前端日志输出
"""

import sys
import os
import time
import signal
import argparse
import traceback
import json
import subprocess
from datetime import datetime
from ast import literal_eval

# Docker配置
CONTAINER_NAME = "android-frida-container"
CAMILLE_SCRIPT_PATH = "/opt/camille/script.js"
SDK_JSON_PATH = "/opt/camille/sdk.json"

# 全局变量
isHook = False
excel_data = []
privacy_policy_status = "后"  # 隐私政策状态：前/后


# ==================== 工具函数 ====================

def print_log(message, log_type="INFO"):
    """格式化输出日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"[{timestamp}] [{log_type}] {message}"
    print(log_msg, flush=True)
    return log_msg


def get_format_time():
    """获取格式化时间"""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


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
        print_log("命令执行超时", "ERROR")
        return -1, "", "命令执行超时"
    except Exception as e:
        print_log(f"命令执行异常: {str(e)}", "ERROR")
        return -1, "", str(e)


def check_container_running():
    """检查Docker容器是否在运行"""
    code, stdout, _ = run_command(
        f"docker inspect -f '{{{{.State.Running}}}}' {CONTAINER_NAME}",
        shell=True,
        timeout=10
    )
    return code == 0 and "true" in stdout.lower()


def is_running_in_docker():
    """检测是否在Docker容器内运行"""
    return os.path.exists('/.dockerenv') or os.path.exists('/run/.containerenv')


def resource_path(relative_path):
    """生成资源文件目录访问路径"""
    base_path = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
    return os.path.abspath(os.path.join(base_path, relative_path))


# ==================== 第三方SDK检测 ====================

class ThirdPartySdk:
    """第三方SDK检测类（完整camille功能）"""
    
    def __init__(self):
        try:
            self.third_party_sdk = self.__load_third_party_sdk()
            self.sdk_list = [s['package_name'] for s in self.third_party_sdk]
        except Exception as e:
            print_log('加载第三方SDK失败，关闭第三方SDK检测', "WARN")
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
                resource_path('sdk.json')
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
                print_log(f"成功加载第三方SDK规则: {len(result)} 个SDK", "SUCCESS")
            else:
                print_log('未找到sdk.json文件', "WARN")
        except Exception as e:
            print_log(f'加载第三方SDK失败: {e}', "ERROR")
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
        import os
        
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
                print_log(f"✅ Excel报告已生成: {file_name}", "SUCCESS")
                print_log(f"📊 共记录 {len(data)} 条隐私行为", "INFO")
                print_log(f"📁 文件大小: {file_size} 字节", "INFO")
            else:
                print_log(f"✅ 空报告已生成: {file_name}", "SUCCESS")
                print_log(f"📊 未检测到隐私行为（仅包含表头）", "INFO")
                print_log(f"📁 文件大小: {file_size} 字节", "INFO")
            return True
        else:
            print_log(f"❌ 文件保存失败，文件不存在: {file_name}", "ERROR")
            return False
        
    except ImportError:
        print_log("❌ 未安装xlwt模块，无法导出Excel", "ERROR")
        print_log("安装方法: pip3 install xlwt", "INFO")
        return False
    except Exception as e:
        print_log(f"❌ 导出Excel失败: {e}", "ERROR")
        print_log(traceback.format_exc(), "ERROR")
        return False


# ==================== Frida Hook核心功能（容器内执行）====================

def frida_hook_direct(package_name, use_module=None, wait_time=0, 
                     duration=0, is_show=True, is_attach=True, export_file=None):
    """
    直接执行Frida Hook（在容器内运行）
    完整实现camille的frida_hook功能
    
    Args:
        package_name: 应用包名或进程ID
        use_module: 使用的模块 {"type": "all/use/nouse", "data": [...]}
        wait_time: 延迟hook时间
        is_show: 是否显示实时告警
        is_attach: 是否使用attach模式
        export_file: 导出文件路径
    """
    print_log(f"🔍 函数参数 - export_file: {export_file}", "INFO")
    try:
        import frida
    except ImportError:
        print_log("❌ 未安装frida，请执行: pip3 install frida frida-tools", "ERROR")
        return False
    
    global isHook, excel_data, privacy_policy_status
    
    # 初始化第三方SDK检测
    tps = ThirdPartySdk()
    
    def my_message_handler(message, payload):
        """消息处理器（完整camille实现）"""
        global isHook, excel_data, privacy_policy_status
        
        if message["type"] == "error":
            print_log(f"❌ Frida错误: {message}", "ERROR")
            os.kill(os.getpid(), signal.SIGTERM)
            return
            
        if message['type'] == 'send':
            data = message.get("payload", {})
            
            # 处理隐私行为告警
            if data.get("type") == "notice":
                alert_time = data.get('time', '')
                action = data.get('action', '')
                arg = data.get('arg', '')
                messages = data.get('messages', '')
                stacks = data.get('stacks', '')
                
                # 判断是否为第三方SDK
                subject_type = tps.is_third_party(stacks)
                
                # 输出告警信息（与camille格式一致）
                if is_show:
                    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                    print_log(
                        f"APP行为：{action}、行为主体：{subject_type}、"
                        f"行为描述：{messages}、传入参数：{arg.replace(chr(13)+chr(10), '，')}",
                        "ALERT"
                    )
                    print_log(f"时间点：{alert_time}", "INFO")
                    print("[*] 调用堆栈：")
                    print(stacks)
                    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                
                # 保存到Excel数据
                if export_file:
                    excel_data.append({
                        'alert_time': alert_time,
                        'action': action,
                        'messages': messages,
                        'arg': arg,
                        'stacks': stacks,
                        'subject_type': subject_type,
                        'privacy_policy_status': f"同意隐私政策{privacy_policy_status}"
                    })
                    print_log(f"📊 数据已收集: {len(excel_data)} 条记录", "INFO")
                
            # 处理应用名称验证
            elif data.get('type') == "app_name":
                get_app_name = data.get('data', '')
                my_data = False if get_app_name == package_name else True
                script.post({"my_data": my_data})
            
            # 处理Hook初始化
            elif data.get('type') == "isHook":
                isHook = True
                print_log("✅ Hook初始化完成", "SUCCESS")
                # 发送模块配置
                if use_module:
                    script.post({"use_module": use_module})
            
            # 处理模块错误
            elif data.get('type') == "noFoundModule":
                print_log(f"❌ 输入 {data.get('data', '')} 模块错误，请检查", "ERROR")
            
            # 处理模块加载
            elif data.get('type') == "loadModule":
                modules = data.get('data', [])
                if modules:
                    print_log(f"✅ 已加载模块: {','.join(modules)}", "SUCCESS")
                else:
                    print_log("⚠️  无模块加载，请检查", "WARN")
    
    try:
        print_log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "INFO")
        print_log("正在连接Frida设备...", "INFO")
        
        # 获取设备
        try:
            device = frida.get_usb_device(timeout=5)
            print_log(f"✅ 已连接USB设备: {device}", "SUCCESS")
        except Exception as e:
            print_log("未找到USB设备，尝试连接远程设备...", "WARN")
            try:
                device = frida.get_remote_device()
                print_log(f"✅ 已连接远程设备: {device}", "SUCCESS")
            except:
                print_log("❌ 无法连接到任何Frida设备", "ERROR")
                return False
        
        print_log(f"Frida版本: {frida.__version__}", "INFO")
        print_log(f"目标应用: {package_name}", "INFO")
        print_log(f"Hook模式: {'Attach' if is_attach else 'Spawn'}", "INFO")
        
        # Attach或Spawn进程
        if is_attach:
            print_log(f"正在Attach到进程: {package_name}", "INFO")
            try:
                if str(package_name).isdigit():
                    pid = int(package_name)
                else:
                    pid = package_name
                session = device.attach(pid)
                print_log("✅ Attach成功", "SUCCESS")
            except frida.ProcessNotFoundError:
                print_log(f"⚠️  Attach失败，进程未运行，自动切换到Spawn模式", "WARN")
                print_log(f"正在启动应用: {package_name} (Spawn模式)", "INFO")
                pid = device.spawn([package_name])
                print_log(f"✅ 应用已启动，PID: {pid}", "SUCCESS")
                time.sleep(1)
                session = device.attach(pid)
                print_log("✅ 已附加到进程", "SUCCESS")
        else:
            print_log(f"正在启动应用: {package_name} (Spawn模式)", "INFO")
            pid = device.spawn([package_name])
            print_log(f"✅ 应用已启动，PID: {pid}", "SUCCESS")
            time.sleep(1)
            session = device.attach(pid)
            print_log("✅ 已附加到进程", "SUCCESS")
        
        time.sleep(1)
        
        # 加载脚本
        print_log("正在加载Hook脚本...", "INFO")
        
        # 尝试加载script.js
        script_paths = [
            CAMILLE_SCRIPT_PATH,  # Docker容器内路径
            os.path.join(os.getcwd(), 'camille/script.js'),
            os.path.join(os.path.dirname(__file__), '../camille/script.js'),
            resource_path('script.js')
        ]
        
        script_path = None
        for path in script_paths:
            if os.path.isfile(path):
                script_path = path
                break
        
        if not script_path:
            print_log("❌ 未找到script.js文件", "ERROR")
            return False
        
        print_log(f"加载脚本: {script_path}", "INFO")
        with open(script_path, encoding="utf-8") as f:
            script_code = f.read()
        
        # 添加延迟或立即执行
        if wait_time > 0:
            script_code += f"\nsetTimeout(main, {wait_time}000);\n"
            print_log(f"延迟Hook: {wait_time}秒", "INFO")
        else:
            script_code += "\nsetImmediate(main);\n"
        
        script = session.create_script(script_code)
        script.on("message", my_message_handler)
        script.load()
        
        time.sleep(1)
        
        # 如果是Spawn模式，恢复进程
        if not is_attach:
            device.resume(pid)
            print_log("应用已启动", "SUCCESS")
        
        # 等待Hook就绪
        wait_time_init = wait_time + 1
        time.sleep(wait_time_init)
        
        if isHook:
            print_log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "INFO")
            print_log("✅ Hook脚本加载成功，开始监控...", "SUCCESS")
            print_log("📱 监控中... (按Ctrl+C停止)", "INFO")
            print_log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "INFO")
            
            # 简化信号处理
            def stop_handler(signum, frame):
                print_log(f"接收到停止信号 {signum}，正在清理...", "INFO")
                print_log(f"当前收集到 {len(excel_data)} 条数据", "INFO")
                
                # 生成报告
                if export_file:
                    print_log(f"正在生成信号中断时的检测报告，共收集 {len(excel_data)} 条数据", "INFO")
                    if excel_data:
                        print_log("✅ 检测到隐私行为，正在生成详细报告...", "SUCCESS")
                        write_excel(excel_data, export_file)
                    else:
                        print_log("⚠️  未检测到任何隐私行为", "WARN")
                        print_log("💡 提示：应用可能没有触发隐私API调用，或Hook时机不对", "INFO")
                        # 生成空报告
                        print_log("正在生成空报告...", "INFO")
                        write_excel([], export_file)
                
                try:
                    session.detach()
                    print_log("已断开Frida会话", "INFO")
                except:
                    pass
                sys.exit(0)
            
            signal.signal(signal.SIGINT, stop_handler)
            signal.signal(signal.SIGTERM, stop_handler)
            
            # 保持运行
            if duration > 0:
                # 有时长限制，运行指定时间后自动退出
                print_log(f"将运行 {duration} 秒后自动停止", "INFO")
                start_time = time.time()
                try:
                    while True:
                        elapsed = time.time() - start_time
                        if elapsed >= duration:
                            print_log(f"已运行 {duration} 秒，检测完成", "INFO")
                            break
                        time.sleep(1)
                except KeyboardInterrupt:
                    print_log("接收到 Ctrl+C，停止检测", "INFO")
                
                # 正常完成时生成报告
                if export_file:
                    print_log(f"正在生成检测报告，共收集 {len(excel_data)} 条数据", "INFO")
                    if excel_data:
                        write_excel(excel_data, export_file)
                    else:
                        print_log("⚠️  未检测到任何隐私行为", "WARN")
                        print_log("💡 提示：应用可能没有触发隐私API调用，或Hook时机不对", "INFO")
                        print_log("   建议：尝试手动操作应用，触发更多功能", "INFO")
                        # 生成空报告
                        print_log("正在生成空报告...", "INFO")
                        write_excel([], export_file)
            else:
                # 无时长限制，持续运行直到手动停止
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print_log("接收到 Ctrl+C，停止检测", "INFO")
                    # Ctrl+C中断时生成报告
                    if export_file:
                        print_log(f"正在生成检测报告，共收集 {len(excel_data)} 条数据", "INFO")
                        if excel_data:
                            write_excel(excel_data, export_file)
                        else:
                            print_log("⚠️  未检测到任何隐私行为", "WARN")
                            print_log("💡 提示：应用可能没有触发隐私API调用，或Hook时机不对", "INFO")
                            print_log("   建议：尝试手动操作应用，触发更多功能", "INFO")
                            # 生成空报告
                            print_log("正在生成空报告...", "INFO")
                            write_excel([], export_file)
        else:
            print_log("❌ Hook失败，尝试增加延迟时间", "ERROR")
            return False
        
    except frida.NotSupportedError as e:
        if 'unable to find application with identifier' in str(e):
            print_log(f"❌ 找不到应用 {package_name}，请检查包名是否正确", "ERROR")
        else:
            print_log("❌ frida-server未运行或版本不匹配", "ERROR")
            print_log(str(e), "ERROR")
        # 生成空报告
        if export_file:
            print_log("正在生成空报告...", "INFO")
            write_excel([], export_file)
        return False
    except frida.ProtocolError as e:
        print_log("❌ frida-server未运行或版本不匹配", "ERROR")
        print_log(str(e), "ERROR")
        # 生成空报告
        if export_file:
            print_log("正在生成空报告...", "INFO")
            write_excel([], export_file)
        return False
    except frida.ServerNotRunningError as e:
        print_log("❌ frida-server未运行或没有连接设备", "ERROR")
        print_log(str(e), "ERROR")
        # 生成空报告
        if export_file:
            print_log("正在生成空报告...", "INFO")
            write_excel([], export_file)
        return False
    except frida.ProcessNotFoundError as e:
        print_log(f"❌ 找不到进程: {e}", "ERROR")
        print_log("💡 建议检查：", "INFO")
        print_log("   1. 应用包名是否正确", "INFO")
        print_log("   2. 应用是否已安装在模拟器中", "INFO")
        print_log("   3. 模拟器是否正常运行", "INFO")
        # 生成空报告
        if export_file:
            print_log("正在生成空报告...", "INFO")
            write_excel([], export_file)
        return False
    except frida.InvalidArgumentError as e:
        print_log("❌ script.js脚本错误", "ERROR")
        print_log(str(e), "ERROR")
        # 生成空报告
        if export_file:
            print_log("正在生成空报告...", "INFO")
            write_excel([], export_file)
        return False
    except frida.InvalidOperationError as e:
        print_log("❌ Hook被中断，可能有其他hook框架运行", "ERROR")
        print_log(str(e), "ERROR")
        # 生成空报告
        if export_file:
            print_log("正在生成空报告...", "INFO")
            write_excel([], export_file)
        return False
    except frida.TransportError as e:
        print_log("❌ Hook关闭或超时", "ERROR")
        print_log(str(e), "ERROR")
        # 生成空报告
        if export_file:
            print_log("正在生成空报告...", "INFO")
            write_excel([], export_file)
        return False
    except KeyboardInterrupt:
        print_log("用户停止了Hook", "INFO")
        # 处理报告生成
        if export_file:
            print_log(f"正在生成中断时的检测报告，共收集 {len(excel_data)} 条数据", "INFO")
            if excel_data:
                print_log("✅ 检测到隐私行为，正在生成详细报告...", "SUCCESS")
                write_excel(excel_data, export_file)
            else:
                print_log("⚠️  未检测到任何隐私行为", "WARN")
                print_log("💡 提示：应用可能没有触发隐私API调用，或Hook时机不对", "INFO")
                print_log("   建议：尝试手动操作应用，触发更多功能", "INFO")
                # 生成空报告
                print_log("正在生成空报告...", "INFO")
                write_excel([], export_file)
        else:
            print_log(f"检测中断，共收集 {len(excel_data)} 条数据（未指定报告文件）", "INFO")
        return False
    except Exception as e:
        print_log(f"❌ Hook失败: {e}", "ERROR")
        print_log(traceback.format_exc(), "ERROR")
        # 生成空报告
        if export_file:
            print_log("正在生成空报告...", "INFO")
            write_excel([], export_file)
        return False
    finally:
        # finally块中不再生成报告，避免重复
        pass
    
    return True


# ==================== Docker容器执行包装器 ====================

def frida_hook_via_docker(package_name, use_module=None, wait_time=0,
                         duration=0, is_show=True, is_attach=True, export_file=None):
    """
    通过Docker容器执行Frida Hook（在宿主机运行）
    """
    try:
        # 检查Docker容器是否运行
        print_log("检查Docker容器状态...", "INFO")
        if not check_container_running():
            print_log(f"❌ Docker容器 {CONTAINER_NAME} 未运行", "ERROR")
            print_log("请先启动Android模拟器容器", "ERROR")
            return False
        
        print_log(f"✅ Docker容器正在运行", "SUCCESS")
        print_log(f"目标应用: {package_name}", "INFO")
        print_log(f"延迟Hook: {wait_time}秒", "INFO")
        print_log(f"模式: {'Attach' if is_attach else 'Spawn'}", "INFO")
        if export_file:
            print_log(f"报告文件: {export_file}", "INFO")
        
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
        
        # 添加模式参数
        if is_attach:
            cmd_parts.append("-ia")
        
        # 添加导出文件参数
        if export_file:
            cmd_parts.extend(["-f", export_file])
        
        frida_command = " ".join(cmd_parts)
        print_log(f"执行命令: {frida_command}", "INFO")
        
        # 在Docker容器中执行frida命令，实时输出
        print_log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "INFO")
        print_log("📱 Frida隐私检测开始（实时输出）", "INFO")
        print_log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "INFO")
        
        # 使用docker exec执行
        docker_cmd = ["docker", "exec", "-u 0", "-i", CONTAINER_NAME, "bash", "-c", frida_command]
        
        print_log("执行的docker命令", docker_cmd)

        process = subprocess.Popen(
            docker_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # 实时输出
        for line in iter(process.stdout.readline, ''):
            if line:
                print(line.rstrip(), flush=True)
        
        return_code = process.wait()
        
        print_log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "INFO")
        print_log("📱 Frida隐私检测结束", "INFO")
        print_log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "INFO")
        
        if return_code == 0:
            print_log("✅ Frida检测成功完成", "SUCCESS")
            if export_file:
                print_log(f"📊 报告已保存到容器中: {export_file}", "SUCCESS")
                # 提示如何导出报告
                print_log(f"💡 导出报告到宿主机:", "INFO")
                print_log(f"   docker cp {CONTAINER_NAME}:{export_file} .", "INFO")
            return True
        else:
            print_log(f"⚠️  Frida检测执行异常，返回代码: {return_code}", "WARN")
            return False
        
    except KeyboardInterrupt:
        print_log("检测被用户中断", "WARN")
        # 用户中断时也尝试生成报告
        if export_file:
            print_log("正在生成中断时的报告...", "INFO")
            # 注意：在Docker模式下，我们无法直接访问excel_data
            # 但至少可以生成一个空报告作为占位符
            write_excel([], export_file)
        return False
    except Exception as e:
        print_log(f"❌ 执行失败: {e}", "ERROR")
        print_log(traceback.format_exc(), "ERROR")
        return False


# ==================== 主函数 ====================

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Frida隐私合规检测工具（完整集成Camille）")
    parser.add_argument("package", help="应用包名或进程ID (例: com.example.app 或 12345)")
    parser.add_argument("-t", "--time", type=int, default=0, 
                       help="延迟Hook时间（秒）, 默认: 0")
    parser.add_argument("-d", "--duration", type=int, default=0,
                       help="检测持续时间（秒），0表示无限期，默认: 0")
    parser.add_argument("-ns", "--noshow", action="store_false", dest="show", default=True,
                       help="不显示实时告警信息")
    parser.add_argument("-f", "--file", help="导出Excel报告文件路径")
    parser.add_argument("-ia", "--isattach", action="store_true", default=False,
                       help="使用attach模式（连接已运行的应用）")
    
    # 模块选择（互斥）
    module_group = parser.add_mutually_exclusive_group()
    module_group.add_argument("-u", "--use",
                            help="检测指定模块，多个用逗号分隔 (例: phone,permission)")
    module_group.add_argument("-nu", "--nouse",
                            help="跳过指定模块，多个用逗号分隔 (例: phone,permission)")
    
    args = parser.parse_args()
    
    # 打印Banner
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("   Frida隐私合规检测工具")
    print("   完整集成 Camille 项目")
    print("   https://github.com/zhengjim/camille")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    
    # 解析模块配置
    use_module = {"type": "all", "data": []}
    if args.use:
        use_module = {"type": "use", "data": args.use}
        print_log(f"检测指定模块: {args.use}", "INFO")
    elif args.nouse:
        use_module = {"type": "nouse", "data": args.nouse}
        print_log(f"跳过指定模块: {args.nouse}", "INFO")
    
    # 检测运行环境
    if is_running_in_docker():
        # 在容器内，直接执行Frida
        print_log("检测到运行在Docker容器内，直接执行Frida", "INFO")
        frida_hook_direct(
            package_name=args.package,
            use_module=use_module,
            wait_time=args.time,
            duration=args.duration,
            is_show=args.show,
            is_attach=args.isattach,
            export_file=args.file
        )
    else:
        # 在宿主机，通过Docker容器执行
        print_log("检测到运行在宿主机，将通过Docker容器执行Frida", "INFO")
        frida_hook_via_docker(
        package_name=args.package,
            use_module=use_module,
        wait_time=args.time,
            duration=args.duration,
            is_show=args.show,
        is_attach=args.isattach,
        export_file=args.file
    )


if __name__ == '__main__':
    main()
