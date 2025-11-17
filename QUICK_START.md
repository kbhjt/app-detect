# Frida隐私合规检测 - 快速开始指南

## 5分钟快速上手

### 前置条件

- ✅ Ubuntu服务器（已配置SSH）
- ✅ Android设备或模拟器（已root）
- ✅ RuoYi-Vue项目已运行

### 步骤1：部署服务器环境（2分钟）

```bash
# 1. 上传部署脚本到服务器
scp scripts/deploy_frida.sh ubuntu@192.168.216.146:/tmp/

# 2. SSH登录服务器
ssh ubuntu@192.168.216.146

# 3. 执行部署脚本
cd /tmp
chmod +x deploy_frida.sh
./deploy_frida.sh
```

**期望输出**：看到 "✅ 安装完成！" 消息

### 步骤2：上传项目文件（1分钟）

```bash
# 在本地开发机上执行

# 1. 上传camille项目文件
scp -r camille/* ubuntu@192.168.216.146:/opt/camille/

# 2. 上传Frida检测脚本
scp scripts/frida_privacy_check.py ubuntu@192.168.216.146:/opt/camille/

# 3. 设置执行权限
ssh ubuntu@192.168.216.146 "chmod +x /opt/camille/frida_privacy_check.py"
```

### 步骤3：准备Android环境（1分钟）

```bash
# 1. 查看本地frida版本
pip3 show frida
# 假设版本为 16.0.0

# 2. 下载对应的frida-server
# 访问: https://github.com/frida/frida/releases/tag/16.0.0
# 下载: frida-server-16.0.0-android-arm64.xz

# 3. 解压并推送到设备
unxz frida-server-16.0.0-android-arm64.xz
adb push frida-server-16.0.0-android-arm64 /data/local/tmp/frida-server
adb shell "chmod 755 /data/local/tmp/frida-server"

# 4. 启动frida-server
adb shell "su -c '/data/local/tmp/frida-server &'"

# 5. 验证连接
frida-ps -U
```

**期望输出**：看到设备上运行的进程列表

### 步骤4：测试脚本（30秒）

```bash
# 1. SSH到服务器
ssh ubuntu@192.168.216.146

# 2. 在Android设备上启动要测试的应用
# 例如：浏览器应用 com.android.chrome

# 3. 执行测试
cd /opt/camille
python3 frida_privacy_check.py com.android.chrome -ia

# 4. 看到Hook成功的日志后，按Ctrl+C停止
```

**期望输出**：
```
[*] 正在连接Frida设备...
[*] 已连接USB设备: ...
[*] Frida版本: 16.0.0
[*] ✅ Hook脚本加载成功，开始监控...
```

### 步骤5：在RuoYi系统中使用（30秒）

```bash
# 1. 启动RuoYi系统（如果还没启动）
cd ruoyi-admin
mvn spring-boot:run

# 在另一个终端
cd ruoyi-ui
npm run dev
```

1. 浏览器访问：`http://localhost:80`
2. 登录系统
3. 进入：**动态分析** 页面
4. 点击：**Frida合规检测** 按钮
5. 填写配置：
   - 应用包名：`com.android.chrome`
   - 检测模块：`全部模块`
   - 延迟Hook：`0`
6. 点击：**开始检测**
7. 查看实时日志！

## 完整示例：检测一个APP

### 场景：检测微信

```bash
# 1. 在Android设备上打开微信应用

# 2. 在RuoYi前端操作
# - 点击"Frida合规检测"
# - 输入包名: com.tencent.mm
# - 选择模块: 全部模块
# - 点击"开始检测"

# 3. 在微信中进行操作
# - 发送消息
# - 查看朋友圈
# - 打开设置
# - 等等...

# 4. 观察日志面板
# - 会看到实时的隐私行为告警
# - 例如：读取设备信息、访问位置、读取联系人等

# 5. 停止检测
# - 点击"停止Frida"按钮
# - 查看生成的Excel报告
```

### 预期检测结果

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔔 APP行为：获取设备信息
📦 行为主体：APP本身
📄 行为描述：获取设备ID(IMEI)
📝 传入参数：返回值: 863...
⏰ 时间点：2024-01-01 12:00:00
📚 调用堆栈：
   at com.tencent.mm.sdk.platformtools.MMHandler.sendMessage(...)
   at com.tencent.mm.plugin.messenger.foundation.a(...)
   ...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 常见问题快速解决

### ❌ 问题1：找不到进程

```bash
# 原因：应用未运行
# 解决：
adb shell "pm list packages | grep tencent"  # 确认包名
# 然后手动启动应用
```

### ❌ 问题2：Frida连接失败

```bash
# 原因：frida-server未运行
# 解决：
adb shell "ps | grep frida"  # 检查是否运行
adb shell "su -c '/data/local/tmp/frida-server &'"  # 重新启动
```

### ❌ 问题3：版本不匹配

```bash
# 原因：frida和frida-server版本不一致
# 解决：
pip3 show frida  # 查看本地版本
# 下载匹配的frida-server版本
```

### ❌ 问题4：SSH连接失败

```yaml
# 原因：application.yml配置错误
# 解决：检查配置
sftp:
  host: 192.168.216.146  # 改为实际服务器IP
  port: 22
  username: ubuntu       # 改为实际用户名
  password: your_pass    # 改为实际密码
```

## 配置文件速查

### application.yml

```yaml
# SFTP配置（用于SSH连接）
sftp:
  host: 192.168.216.146
  port: 22
  username: ubuntu
  password: your_password
```

### FridaAnalysisServiceImpl.java

```java
// Frida脚本路径（服务器上）
private static final String FRIDA_SCRIPT_PATH = "/opt/camille/frida_privacy_check.py";

// 报告输出目录（服务器上）
private static final String REPORT_OUTPUT_DIR = "/opt/reports";
```

### DynamicAnalysisController.java

```java
// VNC访问地址（如果有）
private static final String VNC_URL = "http://192.168.216.146:6080/vnc_lite.html";
```

## 目录结构速查

### 服务器端

```
/opt/
├── camille/
│   ├── camille.py                  # 原始camille脚本
│   ├── script.js                   # Frida Hook脚本
│   ├── frida_privacy_check.py      # 集成版脚本
│   └── utlis/                      # 工具库
│       ├── __init__.py
│       ├── device.py
│       ├── third_party_sdk.py
│       └── sdk.json
└── reports/                         # 报告输出目录
    └── frida_report_*.xls
```

### Android设备

```
/data/local/tmp/
└── frida-server                     # Frida服务端
```

### 项目端

```
RuoYi-Vue/
├── ruoyi-app/
│   └── src/main/java/com/ruoyi/app/
│       ├── controller/
│       │   └── DynamicAnalysisController.java    # 新增Frida API
│       └── service/
│           ├── IFridaAnalysisService.java        # 服务接口
│           └── impl/
│               └── FridaAnalysisServiceImpl.java # 服务实现
├── ruoyi-ui/
│   └── src/views/app/task/dynamic/
│       └── index.vue                              # 增强UI
├── scripts/
│   ├── frida_privacy_check.py                     # Frida脚本
│   ├── deploy_frida.sh                            # 部署脚本
│   └── README.md                                  # 脚本说明
├── docs/
│   └── FRIDA_INTEGRATION.md                       # 详细文档
└── FRIDA_INTEGRATION_SUMMARY.md                   # 集成总结
```

## 快速命令参考

### 服务器操作

```bash
# SSH登录
ssh ubuntu@192.168.216.146

# 查看进程
ps aux | grep python

# 查看日志
tail -f /opt/reports/frida_*.xls

# 手动执行脚本
cd /opt/camille
python3 frida_privacy_check.py com.example.app -ia -f /opt/reports/test.xls
```

### Android操作

```bash
# 查看设备
adb devices

# 查看应用包名
adb shell "pm list packages | grep keyword"

# 查看正在运行的应用
adb shell "ps | grep app_process"

# 启动应用
adb shell "am start -n com.example.app/.MainActivity"

# 查看frida-server是否运行
adb shell "ps | grep frida"

# 重启frida-server
adb shell "su -c 'killall frida-server'"
adb shell "su -c '/data/local/tmp/frida-server &'"
```

### Frida操作

```bash
# 查看版本
frida --version

# 列出USB设备上的进程
frida-ps -U

# 列出USB设备上的应用
frida-ps -Uai

# 手动attach测试
frida -U -f com.example.app
```

## 测试清单

在部署完成后，按以下清单测试：

- [ ] Python3和pip安装正确
- [ ] Frida安装正确
- [ ] 服务器目录创建成功
- [ ] camille文件上传完整
- [ ] frida-server在设备上运行
- [ ] 可以用frida-ps查看进程
- [ ] Python脚本可以手动运行
- [ ] Spring Boot后端启动成功
- [ ] Vue前端启动成功
- [ ] 可以打开动态分析页面
- [ ] 可以点击Frida按钮
- [ ] 日志流连接成功
- [ ] 可以看到实时日志
- [ ] 可以停止检测
- [ ] 生成了Excel报告

## 视频教程（建议）

如果需要更直观的教程，建议录制以下视频：

1. **环境部署** (5分钟)
   - 执行deploy_frida.sh
   - 上传项目文件
   - 准备Android设备

2. **功能演示** (3分钟)
   - 启动检测
   - 查看日志
   - 停止检测
   - 查看报告

3. **故障排查** (5分钟)
   - 常见问题及解决方案

## 下一步

完成快速开始后，建议：

1. 阅读完整文档：`docs/FRIDA_INTEGRATION.md`
2. 查看集成总结：`FRIDA_INTEGRATION_SUMMARY.md`
3. 了解camille原理：`camille/README.md`
4. 自定义Hook脚本：修改 `script.js`
5. 添加第三方SDK：编辑 `utlis/sdk.json`

## 技术支持

遇到问题？

1. 查看文档：`docs/FRIDA_INTEGRATION.md`
2. 查看日志：后端日志 + Python输出
3. 查看issue：camille项目issues
4. 咨询管理员

---

**祝你使用愉快！开始检测隐私合规吧！** 🚀


