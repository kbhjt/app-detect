# Frida隐私合规检测集成文档

## 功能概述

本文档描述了如何将 Camille（Android App隐私合规检测工具）的 Frida Hook 功能集成到 RuoYi-Vue 项目中。

### 主要功能

1. **实时Hook监控**：使用 Frida 动态Hook Android 应用的敏感API
2. **隐私合规检测**：监控应用访问：
   - 设备信息（IMEI、IMSI、MAC地址等）
   - 位置信息
   - 联系人
   - 通话记录
   - 短信
   - 剪贴板
   - 摄像头/麦克风
   - 文件访问
   - 网络请求

3. **第三方SDK识别**：自动识别第三方SDK的行为
4. **实时日志推送**：通过SSE将检测结果实时推送到前端
5. **报告生成**：生成详细的Excel格式检测报告

## 架构设计

```
┌──────────────┐      HTTP      ┌──────────────┐     SSH     ┌──────────────┐
│              │  ──────────>    │              │ ─────────>  │              │
│   前端Vue    │                 │   Spring     │             │   Ubuntu     │
│   (浏览器)   │  <──────────    │   Boot       │ <─────────  │   服务器     │
│              │      SSE        │   后端       │    stdout   │              │
└──────────────┘                 └──────────────┘             └──────────────┘
                                                                     │
                                                                     │ Frida
                                                                     ↓
                                                              ┌──────────────┐
                                                              │   Android    │
                                                              │   设备/模拟器 │
                                                              └──────────────┘
```

## 集成内容

### 1. 后端（Java）

#### 新增文件

- `ruoyi-app/src/main/java/com/ruoyi/app/service/IFridaAnalysisService.java`
  - Frida分析服务接口

- `ruoyi-app/src/main/java/com/ruoyi/app/service/impl/FridaAnalysisServiceImpl.java`
  - Frida分析服务实现
  - 通过SSH连接到Ubuntu服务器
  - 执行Python脚本
  - 捕获输出并通过SSE推送到前端

#### 修改文件

- `ruoyi-app/src/main/java/com/ruoyi/app/controller/DynamicAnalysisController.java`
  - 新增Frida相关的Controller方法：
    - `POST /app/dynamic/frida/start` - 启动Frida检测
    - `POST /app/dynamic/frida/stop` - 停止Frida检测
    - `GET /app/dynamic/frida/logs` - SSE日志流
    - `GET /app/dynamic/frida/report` - 获取检测报告

### 2. Python脚本

- `scripts/frida_privacy_check.py`
  - 集成版Frida隐私合规检测脚本
  - 基于camille项目改造
  - 支持实时日志输出
  - 支持Excel报告导出

### 3. 前端（Vue）

#### 修改文件

- `ruoyi-ui/src/views/app/task/dynamic/index.vue`
  - 新增"Frida合规检测"按钮
  - 新增Frida配置对话框
  - 新增Frida日志流连接
  - 增强日志展示，支持Frida格式化输出

## 部署步骤

### 1. 服务器环境准备

#### 安装依赖

```bash
# 在Ubuntu服务器上执行

# 1. 安装Python3和pip
sudo apt update
sudo apt install python3 python3-pip -y

# 2. 安装Frida
pip3 install frida frida-tools

# 3. 安装其他Python依赖
pip3 install xlwt click opencv-python

# 4. 验证安装
frida --version
python3 --version
```

#### 准备Android设备/模拟器

```bash
# 1. 下载对应架构的frida-server
# 从 https://github.com/frida/frida/releases 下载

# 2. 推送到Android设备
adb push frida-server /data/local/tmp/
adb shell "chmod 755 /data/local/tmp/frida-server"

# 3. 启动frida-server（需要root权限）
adb shell "su -c '/data/local/tmp/frida-server &'"

# 4. 验证连接
frida-ps -U
```

### 2. 部署脚本文件

```bash
# 1. 创建目录
sudo mkdir -p /opt/camille
sudo mkdir -p /opt/reports

# 2. 复制camille项目文件到服务器
# 将以下文件上传到 /opt/camille/
# - camille.py
# - script.js
# - utlis/ (整个目录)

# 3. 复制集成脚本
# 将 scripts/frida_privacy_check.py 上传到 /opt/camille/

# 4. 设置权限
sudo chmod +x /opt/camille/frida_privacy_check.py
sudo chown -R ubuntu:ubuntu /opt/camille
sudo chown -R ubuntu:ubuntu /opt/reports
```

### 3. 测试脚本

```bash
# 测试脚本是否可以正常运行
cd /opt/camille

# 确保有Android应用正在运行
# 假设包名为 com.example.testapp

python3 frida_privacy_check.py com.example.testapp -ia
```

### 4. 配置后端

确保 `application.yml` 中配置了正确的SFTP连接信息：

```yaml
sftp:
  host: 192.168.216.146
  port: 22
  username: ubuntu
  password: your_password
```

### 5. 启动服务

```bash
# 1. 启动Spring Boot后端
cd ruoyi-admin
mvn spring-boot:run

# 2. 启动Vue前端
cd ruoyi-ui
npm run dev
```

## 使用方法

### 1. 创建分析任务

1. 登录系统
2. 进入"动态分析"页面
3. 确保有APK任务信息

### 2. 启动Frida检测

1. 点击"Frida合规检测"按钮
2. 在弹出的对话框中配置：
   - **应用包名**：要检测的Android应用包名（如：com.example.app）
   - **检测模块**：选择要检测的隐私模块（全部/电话/位置等）
   - **延迟Hook**：设置延迟时间（用于规避加壳检测）
3. 点击"开始检测"

### 3. 查看实时日志

- 检测过程中，日志会实时显示在右侧日志面板
- 日志包含：
  - Hook状态信息
  - 隐私行为告警（红色高亮）
  - 调用堆栈
  - 第三方SDK识别

### 4. 停止检测

- 点击"停止Frida"按钮即可停止检测
- 系统会自动生成Excel报告

### 5. 下载报告

- 报告保存在服务器：`/opt/reports/frida_report_[taskId]_[packageName].xls`
- 包含详细的隐私合规检测结果

## 日志格式说明

### 隐私行为告警格式

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[*] 2024-01-01 12:00:00 [ALERT] APP行为：获取设备信息
[*] 2024-01-01 12:00:00 [INFO] 行为主体：APP本身
[*] 2024-01-01 12:00:00 [INFO] 行为描述：获取设备ID(IMEI)
[*] 2024-01-01 12:00:00 [INFO] 传入参数：返回值: 863XXX...
[*] 2024-01-01 12:00:00 [INFO] 时间点：2024-01-01 12:00:00
调用堆栈：
   at com.example.app.MainActivity.onCreate(MainActivity.java:123)
   at android.app.Activity.performCreate(Activity.java:7224)
   ...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 日志级别

- `[INFO]` - 普通信息
- `[SUCCESS]` - 成功消息（绿色）
- `[WARN]` - 警告消息（黄色）
- `[ERROR]` - 错误消息（红色）
- `[ALERT]` - 隐私行为告警（红色高亮）

## 常见问题

### 1. 找不到进程

**问题**：`未找到进程: com.example.app，请确保应用正在运行`

**解决**：
- 确保目标应用已在Android设备/模拟器中启动
- 使用 `adb shell pm list packages | grep example` 确认包名正确
- 使用 `frida-ps -U` 查看正在运行的进程

### 2. Frida Server未运行

**问题**：`Frida Server未运行，请在设备上启动frida-server`

**解决**：
```bash
# 在设备上启动frida-server
adb shell "su -c '/data/local/tmp/frida-server &'"

# 验证是否运行
adb shell "ps | grep frida-server"
```

### 3. 版本不匹配

**问题**：`frida-server与frida版本不一致`

**解决**：
```bash
# 查看本地frida版本
pip3 show frida

# 下载匹配版本的frida-server
# https://github.com/frida/frida/releases
```

### 4. SSH连接失败

**问题**：`SSH连接失败`

**解决**：
- 检查服务器IP、端口、用户名、密码是否正确
- 确保服务器SSH服务正在运行
- 检查防火墙设置

### 5. 权限问题

**问题**：`Permission denied`

**解决**：
```bash
# 确保脚本有执行权限
chmod +x /opt/camille/frida_privacy_check.py

# 确保报告目录有写权限
sudo chown -R ubuntu:ubuntu /opt/reports
```

## 检测模块说明

### 全部模块（all）
- 检测所有敏感API调用

### 电话信息（phone）
- TelephonyManager（IMEI、IMSI、手机号等）
- 通话记录
- 短信

### 位置信息（location）
- GPS定位
- 网络定位
- 基站定位

### 联系人（contact）
- 读取联系人
- 修改联系人

### 剪贴板（clipboard）
- 读取剪贴板内容
- 写入剪贴板

### 设备信息（device）
- 设备ID
- MAC地址
- 序列号
- AndroidID

### 网络请求（network）
- HTTP/HTTPS请求
- Socket连接

## 报告说明

### Excel报告内容

| 列名 | 说明 |
|------|------|
| 隐私政策状态 | 同意隐私政策前/后 |
| 时间点 | 行为发生时间 |
| 行为主体 | APP本身/第三方SDK名称 |
| 操作行为 | 具体的操作类型 |
| 行为描述 | 详细描述 |
| 传入参数 | API调用参数 |
| 调用堆栈 | 完整的Java调用栈 |

### 合规判断依据

根据《App违法违规收集使用个人信息行为认定方法》：

1. **首次打开前收集信息** - 违规
2. **未经同意收集敏感信息** - 违规
3. **第三方SDK过度收集** - 违规
4. **超范围收集信息** - 违规

## 技术细节

### Frida Hook原理

Frida是一个动态插桩工具，可以在运行时修改应用程序的行为：

1. **注入**：将Frida Agent注入到目标进程
2. **Hook**：拦截特定的函数调用
3. **监控**：记录函数参数、返回值、调用栈
4. **上报**：将结果发送给控制端

### 集成流程

```
用户点击"Frida检测"
    ↓
前端发送请求到后端 (/app/dynamic/frida/start)
    ↓
后端通过SSH连接到Ubuntu服务器
    ↓
执行Python脚本 (frida_privacy_check.py)
    ↓
Python脚本使用Frida attach到Android应用
    ↓
加载Hook脚本 (script.js)
    ↓
实时监控敏感API调用
    ↓
输出日志到stdout
    ↓
后端捕获日志并通过SSE推送到前端
    ↓
前端实时显示日志
```

### SSE推送机制

使用Server-Sent Events (SSE) 实现实时日志推送：

- **优势**：单向推送，自动重连，简单易用
- **格式**：`event: log\ndata: 日志内容\n\n`
- **前端**：使用EventSource接收

## 扩展开发

### 添加自定义Hook

编辑 `script.js` 或 `frida_privacy_check.py`：

```javascript
// 在script.js中添加自定义Hook
try {
    var MyClass = Java.use('com.example.MyClass');
    MyClass.myMethod.implementation = function(arg) {
        var result = this.myMethod(arg);
        alertSend('自定义行为', '描述', '参数: ' + arg);
        return result;
    };
} catch(e) {
    console.log('Hook失败: ' + e);
}
```

### 添加第三方SDK识别

编辑 `utlis/sdk.json`：

```json
[
    {
        "sdk_name": "我的SDK",
        "package_name": "com.mysdk"
    }
]
```

## 性能考虑

- Frida Hook会增加应用运行开销（约10-30%）
- 建议在测试环境进行检测
- 长时间运行可能影响设备性能
- 适时停止检测以释放资源

## 安全注意事项

1. **仅用于合法合规检测**
2. **需要目标应用的合法授权**
3. **保护检测结果数据安全**
4. **不要在生产环境使用**

## 参考资料

- [Frida官方文档](https://frida.re/docs/home/)
- [Camille项目](https://github.com/zhengjim/camille)
- [App违法违规收集使用个人信息行为认定方法](https://www.miit.gov.cn/)

## 技术支持

如有问题，请查看：
- 后端日志：`ruoyi-admin/logs/`
- Python输出：通过前端日志面板查看
- Frida日志：设备上的frida-server输出

## 更新日志

### v1.0.0 (2024-01-01)
- 初始版本
- 集成Camille的Frida检测功能
- 支持实时日志推送
- 支持Excel报告导出


