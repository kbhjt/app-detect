# Frida隐私合规检测脚本

本目录包含用于Android应用隐私合规检测的Frida脚本及部署工具。

## 文件说明

### frida_privacy_check.py
基于camille项目改造的Frida隐私合规检测脚本，主要功能：
- 使用Frida Hook Android应用敏感API
- 实时监控隐私行为
- 识别第三方SDK调用
- 生成Excel格式检测报告

### deploy_frida.sh
自动部署脚本，用于在Ubuntu服务器上快速安装Frida环境：
- 安装Python3和pip
- 安装Frida及依赖
- 创建工作目录
- 设置权限

## 快速开始

### 1. 在服务器上部署

```bash
# 上传部署脚本到服务器
scp deploy_frida.sh user@server:/tmp/

# SSH登录服务器
ssh user@server

# 执行部署脚本
cd /tmp
chmod +x deploy_frida.sh
./deploy_frida.sh
```

### 2. 上传项目文件

```bash
# 从本地上传camille项目到服务器
scp -r camille/* user@server:/opt/camille/

# 上传集成脚本
scp scripts/frida_privacy_check.py user@server:/opt/camille/
```

### 3. 准备Android环境

```bash
# 下载与本地frida版本匹配的frida-server
# 查看本地frida版本
pip3 show frida

# 从 https://github.com/frida/frida/releases 下载对应版本

# 推送到Android设备
adb push frida-server /data/local/tmp/
adb shell "chmod 755 /data/local/tmp/frida-server"

# 启动frida-server (需要root)
adb shell "su -c '/data/local/tmp/frida-server &'"

# 验证连接
frida-ps -U
```

### 4. 测试运行

```bash
# SSH登录服务器
ssh user@server

# 确保有Android应用正在运行
# 假设包名为 com.example.testapp

# 执行检测
cd /opt/camille
python3 frida_privacy_check.py com.example.testapp -ia

# 查看帮助
python3 frida_privacy_check.py -h
```

## 使用方法

### 基本用法

```bash
# 检测指定应用（attach模式）
python3 frida_privacy_check.py com.example.app -ia

# 延迟5秒后Hook（规避加壳）
python3 frida_privacy_check.py com.example.app -ia -t 5

# 指定检测模块
python3 frida_privacy_check.py com.example.app -ia -u phone,location

# 导出报告
python3 frida_privacy_check.py com.example.app -ia -f /opt/reports/report.xls
```

### 参数说明

```
positional arguments:
  package               应用包名或进程ID (例: com.example.app 或 12345)

optional arguments:
  -h, --help            显示帮助信息
  -t TIME, --time TIME  延迟Hook时间（秒）, 默认: 0
  -u USE, --use USE     使用的检测模块，多个用逗号分隔
                        可选: phone,location,contact,clipboard,device,network
  -ia, --isattach       使用attach模式 (默认)
  -f FILE, --file FILE  导出Excel报告文件路径
```

### 检测模块

| 模块 | 说明 | 检测内容 |
|------|------|----------|
| all | 全部模块 | 所有敏感API |
| phone | 电话信息 | IMEI、IMSI、手机号、通话记录 |
| location | 位置信息 | GPS、网络定位、基站定位 |
| contact | 联系人 | 读取/修改联系人 |
| clipboard | 剪贴板 | 读取/写入剪贴板 |
| device | 设备信息 | 设备ID、MAC地址、序列号 |
| network | 网络请求 | HTTP/HTTPS请求 |

## 集成到RuoYi系统

本脚本已集成到RuoYi-Vue项目的动态分析模块中：

1. **前端入口**：`ruoyi-ui/src/views/app/task/dynamic/index.vue`
   - 点击"Frida合规检测"按钮
   - 配置检测参数
   - 查看实时日志

2. **后端服务**：`ruoyi-app/src/main/java/com/ruoyi/app/service/impl/FridaAnalysisServiceImpl.java`
   - 通过SSH调用此脚本
   - 捕获输出日志
   - 通过SSE推送到前端

3. **Controller**：`ruoyi-app/src/main/java/com/ruoyi/app/controller/DynamicAnalysisController.java`
   - API端点：`/app/dynamic/frida/*`

详细集成文档请查看：`docs/FRIDA_INTEGRATION.md`

## 输出格式

### 控制台输出

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[*] 2024-01-01 12:00:00 [ALERT] APP行为：获取设备信息
[*] 2024-01-01 12:00:00 [INFO] 行为主体：APP本身
[*] 2024-01-01 12:00:00 [INFO] 行为描述：获取设备ID(IMEI)
[*] 2024-01-01 12:00:00 [INFO] 传入参数：返回值: 863XXX...
[*] 2024-01-01 12:00:00 [INFO] 时间点：2024-01-01 12:00:00
调用堆栈：
   at com.example.app.MainActivity.onCreate(MainActivity.java:123)
   ...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Excel报告

生成的Excel报告包含以下列：
- 隐私政策状态
- 时间点
- 行为主体
- 操作行为
- 行为描述
- 传入参数
- 调用堆栈

## 常见问题

### 1. 找不到frida模块

```bash
# 安装frida
pip3 install frida frida-tools
```

### 2. 找不到进程

```bash
# 确保应用正在运行
adb shell "pm list packages | grep example"

# 查看正在运行的进程
frida-ps -U
```

### 3. frida-server版本不匹配

```bash
# 查看本地版本
pip3 show frida

# 下载匹配的frida-server
# https://github.com/frida/frida/releases
```

### 4. 权限被拒绝

```bash
# 确保frida-server有执行权限
adb shell "chmod 755 /data/local/tmp/frida-server"

# 使用root权限运行
adb shell "su -c '/data/local/tmp/frida-server &'"
```

### 5. 无法连接设备

```bash
# 检查adb连接
adb devices

# 检查frida连接
frida-ps -U

# 重启adb服务
adb kill-server
adb start-server
```

## 技术支持

- Frida官方文档：https://frida.re/docs/home/
- Camille项目：https://github.com/zhengjim/camille
- 问题反馈：请联系系统管理员

## 版本历史

### v1.0.0 (2024-01-01)
- 初始版本
- 基于camille项目改造
- 支持attach模式
- 支持Excel报告导出
- 集成到RuoYi系统

## 许可证

本脚本基于camille项目，遵循相同的开源许可证。


