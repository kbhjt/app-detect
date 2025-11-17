package com.ruoyi.app.controller;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;
import com.ruoyi.app.config.SftpConfig;
import com.ruoyi.app.service.IFridaAnalysisService;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.StringUtils;

/**
 * 动态分析控制器
 * 
 * @author ruoyi
 */
@RestController
@RequestMapping("/app/dynamic")
public class DynamicAnalysisController extends BaseController
{
    private static final Logger log = LoggerFactory.getLogger(DynamicAnalysisController.class);
    
    @Autowired
    private SftpConfig sftpConfig;
    
    @Autowired
    private IFridaAnalysisService fridaAnalysisService;
    
    /**
     * Python脚本在Ubuntu服务器上的路径
     */
    private static final String PYTHON_SCRIPT_PATH = "/opt/scripts/android_dynamic_analysis.py";
    
    /**
     * VNC访问地址
     */
    private static final String VNC_URL = "http://192.168.216.146:6080/vnc_lite.html";
    
    /**
     * 存储分析任务的日志流
     */
    private final Map<String, SseEmitter> emitterMap = new ConcurrentHashMap<>();
    
    /**
     * 存储正在运行的SSH会话
     */
    private final Map<String, com.jcraft.jsch.Session> sessionMap = new ConcurrentHashMap<>();
    
    /**
     * 存储正在运行的SSH通道
     */
    private final Map<String, com.jcraft.jsch.ChannelExec> channelMap = new ConcurrentHashMap<>();
    
    /**
     * 存储任务的停止标志
     */
    private final Map<String, Boolean> stopFlagMap = new ConcurrentHashMap<>();
    
    /**
     * 日志批量处理 - 缓冲区
     */
    private final Map<String, List<String>> logBufferMap = new ConcurrentHashMap<>();
    
    /**
     * 日志批量处理 - 上次发送时间
     */
    private final Map<String, Long> lastLogSendTimeMap = new ConcurrentHashMap<>();
    
    /**
     * 开始动态分析
     */
    @PostMapping("/start")
    public AjaxResult startAnalysis(@RequestBody Map<String, Object> params)
    {
        try
        {
            // 获取参数
            String
                    apkPath = (String) params.get("apkPath");
            String taskId = (String) params.get("taskId");
            
            log.info("接收到动态分析请求 - taskId: {}, apkPath: {}", taskId, apkPath);
            
            // 验证参数
            if (StringUtils.isEmpty(apkPath))
            {
                return AjaxResult.error("APK路径不能为空");
            }
            
            if (StringUtils.isEmpty(taskId))
            {
                taskId = String.valueOf(System.currentTimeMillis());
            }
            
            // 在新线程中执行分析任务
            final String finalTaskId = taskId;
            final String finalApkPath = apkPath;
            
            // 重置停止标志
            stopFlagMap.put(taskId, false);
            
            
            new Thread(() -> {
                executeAnalysis(finalTaskId, finalApkPath);
            }).start();
            
            // 返回结果
            AjaxResult ajax = AjaxResult.success("动态分析任务已启动");
            ajax.put("taskId", taskId);
            ajax.put("vncUrl", VNC_URL);
            
            return ajax;
        }
        catch (Exception e)
        {
            log.error("启动动态分析失败", e);
            return AjaxResult.error("启动动态分析失败: " + e.getMessage());
        }
    }
    
    /**
     * 执行动态分析（通过SSH调用Python脚本）
     */
    private void executeAnalysis(String taskId, String apkPath)
    {
        com.jcraft.jsch.Session session = null;
        com.jcraft.jsch.ChannelExec channel = null;
        
        try
        {
            log.info("开始执行动态分析 - taskId: {}", taskId);
            
            // 发送日志到前端
            sendLog(taskId, "开始连接到分析服务器...");
            
            // 创建SSH会话
            com.jcraft.jsch.JSch jsch = new com.jcraft.jsch.JSch();
            session = jsch.getSession(
                sftpConfig.getUsername(),
                sftpConfig.getHost(),
                sftpConfig.getPort()
            );
            session.setPassword(sftpConfig.getPassword());
            
            java.util.Properties config = new java.util.Properties();
            config.put("StrictHostKeyChecking", "no");
            session.setConfig(config);
            session.setTimeout(30000);
            
            session.connect();
            log.info("SSH连接成功 - {}:{}", sftpConfig.getHost(), sftpConfig.getPort());
            sendLog(taskId, "✅ SSH连接成功");
            
            // 保存SSH会话到Map（用于停止时关闭）
            sessionMap.put(taskId, session);
            
            // 打开执行通道
            channel = (com.jcraft.jsch.ChannelExec) session.openChannel("exec");
            
            // 构建命令（传递taskId参数用于报告命名）
            String command = String.format("python3 %s %s '' '' %s", PYTHON_SCRIPT_PATH, apkPath, taskId);
            channel.setCommand(command);
            
            sendLog(taskId, "开始执行Python脚本...");
            sendLog(taskId, "命令: " + command);
            sendLog(taskId, "APK路径: " + apkPath);
            sendLog(taskId, "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
            
            // 获取输出流
            channel.setInputStream(null);
            channel.setErrStream(System.err);
            
            java.io.InputStream in = channel.getInputStream();
            channel.connect();
            
            // 保存通道到Map（用于停止时关闭）
            channelMap.put(taskId, channel);
            
            // 读取输出
            byte[] tmp = new byte[1024];
            while (true)
            {
                // 检查停止标志
                if (Boolean.TRUE.equals(stopFlagMap.get(taskId)))
                {
                    log.info("检测到停止信号 - taskId: {}", taskId);
                    sendLog(taskId, "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
                    sendLog(taskId, "⏹️ 用户手动停止分析");
                    break;
                }
                
                while (in.available() > 0)
                {
                    int i = in.read(tmp, 0, 1024);
                    if (i < 0) break;
                    
                    String output = new String(tmp, 0, i);
                    // 按行分割并过滤发送
                    String[] lines = output.split("\n");
                    for (String line : lines)
                    {
                        if (!line.trim().isEmpty())
                        {
                            String trimmedLine = line.trim();
                            
                            // 只发送重要日志到前端，减少卡顿
                            if (shouldSendToFrontend(trimmedLine))
                            {
                                sendLog(taskId, trimmedLine);
                            }
                            
                            // 所有日志仍然记录到后端日志
                            log.info("[{}] {}", taskId, trimmedLine);
                        }
                    }
                }
                
                if (channel.isClosed())
                {
                    if (in.available() > 0) continue;
                    
                    int exitStatus = channel.getExitStatus();
                    log.info("SSH命令执行完成，退出码: {}", exitStatus);
                    
                    sendLog(taskId, "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
                    if (exitStatus == 0)
                    {
                        sendLog(taskId, "✅ 动态分析完成！");
                        sendLog(taskId, "📺 VNC访问地址: " + VNC_URL);
                    }
                    else
                    {
                        sendLog(taskId, "❌ 动态分析失败，退出码: " + exitStatus);
                    }
                    break;
                }
                
                try { Thread.sleep(100); } catch (Exception e) { }
            }
            
        }
        catch (Exception e)
        {
            log.error("执行动态分析异常", e);
            sendLog(taskId, "❌ 执行失败: " + e.getMessage());
            e.printStackTrace();
        }
        finally
        {
            // 清理资源
            if (channel != null && channel.isConnected())
            {
                channel.disconnect();
            }
            
            if (session != null && session.isConnected())
            {
                session.disconnect();
            }
            
            // 从Map中移除
            channelMap.remove(taskId);
            sessionMap.remove(taskId);
            stopFlagMap.remove(taskId);
            
            // 关闭SSE连接
            closeSse(taskId);
        }
    }
    
    /**
     * 建立SSE连接，用于实时推送日志
     */
    @GetMapping("/logs")
    public SseEmitter streamLogs(@RequestParam String taskId)
    {
        log.info("客户端订阅日志流 - taskId: {}", taskId);
        
        // 创建SSE发射器（超时时间30分钟）
        SseEmitter emitter = new SseEmitter(30 * 60 * 1000L);
        
        // 存储到Map中
        emitterMap.put(taskId, emitter);
        
        // 设置超时和完成回调
        emitter.onTimeout(() -> {
            log.info("SSE超时 - taskId: {}", taskId);
            emitterMap.remove(taskId);
        });
        
        emitter.onCompletion(() -> {
            log.info("SSE完成 - taskId: {}", taskId);
            emitterMap.remove(taskId);
        });
        
        emitter.onError((e) -> {
            log.error("SSE错误 - taskId: " + taskId, e);
            emitterMap.remove(taskId);
        });
        
        // 发送连接成功消息
        try
        {
            emitter.send(SseEmitter.event()
                .name("connected")
                .data("日志流已连接"));
        }
        catch (Exception e)
        {
            log.error("发送连接消息失败", e);
        }
        
        return emitter;
    }
    
    // 日志过滤常量
    private static final String[] IMPORTANT_KEYWORDS = {
        "✅", "❌", "⚠️", "🔍", "📊", "🎯", "💡", "🚀", "📱", "🖥️", "🔗",
        "SUCCESS", "ERROR", "WARN", "INFO",
        "Hook脚本加载成功", "监控中", "检测完成", "应用已启动", 
        "已附加到进程", "Hook初始化完成", "隐私数据收集进度",
        "步骤", "启动", "安装", "配置", "完成", "失败", "成功"
    };
    
    private static final String[] SKIP_KEYWORDS = {
        "调用堆栈：", "android.app.", "com.android.", "java.lang.",
        "Native Method", "Handler.java", "Looper.java", "ApplicationPackageManager",
        "com.mob.tools", "com.mob.commons"
    };

    /**
     * 判断是否应该发送日志到前端（减少前端卡顿）
     */
    private boolean shouldSendToFrontend(String line)
    {
        if (line == null || line.trim().isEmpty()) return false;
        
        // 重要日志始终发送
        for (String keyword : IMPORTANT_KEYWORDS)
        {
            if (line.contains(keyword)) return true;
        }
        
        // 过滤掉频繁的调试信息
        for (String keyword : SKIP_KEYWORDS)
        {
            if (line.contains(keyword)) return false;
        }
        
        // APP行为数据发送
        return line.contains("APP行为：") || line.contains("行为主体：");
    }
    
    /**
     * 发送日志到前端（批量处理版本）
     */
    private void sendLog(String taskId, String message)
    {
        // 获取或创建日志缓冲区
        logBufferMap.computeIfAbsent(taskId, k -> new ArrayList<>()).add(message);
        
        long currentTime = System.currentTimeMillis();
        Long lastSendTime = lastLogSendTimeMap.get(taskId);
        
        // 批量发送条件：缓冲区满5条或距离上次发送超过1秒
        List<String> buffer = logBufferMap.get(taskId);
        if (buffer.size() >= 5 || (lastSendTime == null) || (currentTime - lastSendTime >= 1000))
        {
            flushLogBuffer(taskId);
        }
    }
    
    /**
     * 立即发送日志到前端（不经过缓冲）
     */
    private void sendLogImmediate(String taskId, String message)
    {
        SseEmitter emitter = emitterMap.get(taskId);
        if (emitter != null)
        {
            try
            {
                emitter.send(SseEmitter.event()
                    .name("log")
                    .data(message));
            }
            catch (Exception e)
            {
                log.error("发送日志失败 - taskId: {}", taskId, e);
                emitterMap.remove(taskId);
            }
        }
    }
    
    /**
     * 刷新日志缓冲区
     */
    private void flushLogBuffer(String taskId)
    {
        List<String> buffer = logBufferMap.get(taskId);
        if (buffer != null && !buffer.isEmpty())
        {
            // 合并多条日志为一条消息发送
            String combinedMessage = String.join("\n", buffer);
            sendLogImmediate(taskId, combinedMessage);
            
            // 清空缓冲区并更新时间
            buffer.clear();
            lastLogSendTimeMap.put(taskId, System.currentTimeMillis());
        }
    }
    
    /**
     * 关闭SSE连接
     */
    private void closeSse(String taskId)
    {
        // 关闭前刷新剩余的日志缓冲区
        flushLogBuffer(taskId);
        
        SseEmitter emitter = emitterMap.get(taskId);
        if (emitter != null)
        {
            try
            {
                emitter.send(SseEmitter.event()
                    .name("completed")
                    .data("分析完成"));
                emitter.complete();
            }
            catch (Exception e)
            {
                log.error("关闭SSE失败", e);
            }
            finally
            {
                emitterMap.remove(taskId);
                // 清理批量处理相关的Map
                logBufferMap.remove(taskId);
                lastLogSendTimeMap.remove(taskId);
            }
        }
    }
    
    /**
     * 停止分析
     */
    @PostMapping("/stop")
    public AjaxResult stopAnalysis(@RequestBody Map<String, Object> params)
    {
        com.jcraft.jsch.Session killSession = null;
        com.jcraft.jsch.ChannelExec killChannel = null;
        
        try
        {
            String taskId = (String) params.get("taskId");
            
            log.info("停止动态分析 - taskId: {}", taskId);
            sendLog(taskId, "正在停止分析任务...");
            
            // 1. 设置停止标志
            stopFlagMap.put(taskId, true);
            log.info("已设置停止标志");
            
            // 2. 关闭正在运行的SSH通道和会话
            com.jcraft.jsch.ChannelExec runningChannel = channelMap.get(taskId);
            if (runningChannel != null && runningChannel.isConnected())
            {
                log.info("断开正在运行的SSH通道");
                runningChannel.disconnect();
            }
            
            com.jcraft.jsch.Session runningSession = sessionMap.get(taskId);
            if (runningSession != null && runningSession.isConnected())
            {
                log.info("断开正在运行的SSH会话");
                runningSession.disconnect();
            }
            
            
            // 4. Kill Python进程和停止Docker容器
            log.info("开始清理服务器上的进程和容器");
            
            // 创建新的SSH会话来执行清理命令
            com.jcraft.jsch.JSch jsch = new com.jcraft.jsch.JSch();
            killSession = jsch.getSession(
                sftpConfig.getUsername(),
                sftpConfig.getHost(),
                sftpConfig.getPort()
            );
            killSession.setPassword(sftpConfig.getPassword());
            
            java.util.Properties config = new java.util.Properties();
            config.put("StrictHostKeyChecking", "no");
            killSession.setConfig(config);
            killSession.setTimeout(30000);
            
            killSession.connect();
            
            // 执行清理命令：杀死Python进程和停止Docker容器
            killChannel = (com.jcraft.jsch.ChannelExec) killSession.openChannel("exec");
            
            // 修改清理命令：只停止进程，不删除容器（保留容器以便下载报告）
            String cleanupCommand = "pkill -f python3.*android_dynamic_analysis.py; sleep 2; docker exec -u 0 android-frida-container pkill -f 'python3.*frida_privacy_check.py' || echo 'Frida进程已停止'";
            killChannel.setCommand(cleanupCommand);
            
            java.io.InputStream in = killChannel.getInputStream();
            killChannel.connect();
            
            // 使用BufferedReader读取输出，等待清理命令完全执行（最多25秒）
            java.io.BufferedReader reader = new java.io.BufferedReader(
                new java.io.InputStreamReader(in)
            );
            StringBuilder output = new StringBuilder();
            String line;
            long startTime = System.currentTimeMillis();
            long maxWaitTime = 35000; // 35秒超时，给足够时间执行所有步骤（包括10秒等待）
            
            // 持续读取输出直到命令完成或超时
            while (System.currentTimeMillis() - startTime < maxWaitTime)
            {
                try {
                    while ((line = reader.readLine()) != null) {
                        output.append(line).append("\n");
                        log.info("清理进度: {}", line);
                        
                        // 如果看到最后一步完成，可以提前退出
                        if (line.contains("Step 9: Cleanup completed successfully")) {
                            log.info("清理命令执行完成");
                            break;
                        }
                    }
                    
                    // 检查通道是否关闭
                    if (killChannel.isClosed()) {
                        log.info("SSH通道已关闭，清理命令执行完毕");
                        break;
                    }
                    
                    // 短暂等待，避免CPU占用过高
                    Thread.sleep(100);
                } catch (java.io.IOException e) {
                    log.warn("读取清理命令输出时出现IO异常: {}", e.getMessage());
                    break;
                } catch (InterruptedException e) {
                    log.warn("清理命令执行被中断: {}", e.getMessage());
                    break;
                }
            }
            
            log.info("清理命令输出: {}", output.toString());
            
            // 检查Python信号处理器日志文件
            try {
                com.jcraft.jsch.ChannelExec checkChannel = (com.jcraft.jsch.ChannelExec) killSession.openChannel("exec");
                checkChannel.setCommand("cat /tmp/signal_handler.log 2>/dev/null || echo 'No signal handler log found'");
                java.io.InputStream checkIn = checkChannel.getInputStream();
                checkChannel.connect();
                
                byte[] checkTmp = new byte[1024];
                StringBuilder signalLog = new StringBuilder();
                while (true) {
                    while (checkIn.available() > 0) {
                        int i = checkIn.read(checkTmp, 0, 1024);
                        if (i < 0) break;
                        signalLog.append(new String(checkTmp, 0, i));
                    }
                    if (checkChannel.isClosed()) {
                        if (checkIn.available() > 0) continue;
                        break;
                    }
                    try { Thread.sleep(100); } catch (Exception e) { }
                }
                checkChannel.disconnect();
                
                log.info("Python信号处理器日志: {}", signalLog.toString());
            } catch (Exception e) {
                log.warn("无法检查信号处理器日志: {}", e.getMessage());
            }
            
            log.info("Python进程已终止，Docker容器保持运行状态");
            
            // 4. 关闭SSE连接
            sendLog(taskId, "✅ 分析任务已停止");
            sendLog(taskId, "- Python脚本进程已终止");
            sendLog(taskId, "- Docker容器保持运行（用于报告下载）");
            closeSse(taskId);
            
            // 5. 清理Map中的数据
            channelMap.remove(taskId);
            sessionMap.remove(taskId);
            stopFlagMap.remove(taskId);
            
            return AjaxResult.success("分析已停止");
        }
        catch (Exception e)
        {
            log.error("停止分析失败", e);
            sendLog((String) params.get("taskId"), "❌ 停止失败: " + e.getMessage());
            return AjaxResult.error("停止失败: " + e.getMessage());
        }
        finally
        {
            if (killChannel != null && killChannel.isConnected())
            {
                killChannel.disconnect();
            }
            
            if (killSession != null && killSession.isConnected())
            {
                killSession.disconnect();
            }
        }
    }
    
    /**
     * 获取VNC访问地址
     */
    @GetMapping("/vncUrl")
    public AjaxResult getVncUrl()
    {
        AjaxResult ajax = AjaxResult.success();
        ajax.put("vncUrl", VNC_URL);
        return ajax;
    }
    
    /**
     * 启动Frida隐私合规检测
     */
    @PostMapping("/frida/start")
    public AjaxResult startFridaAnalysis(@RequestBody Map<String, Object> params)
    {
        System.out.println("=== Controller收到Frida启动请求 ===");
        log.error("=== Controller收到Frida启动请求 ==="); // 使用error级别确保输出
        
        try
        {
            String taskId = (String) params.get("taskId");
            String packageName = (String) params.get("packageName");
            String apkPath = (String) params.get("apkPath");
            String useModule = (String) params.get("useModule");
            String logLevel = (String) params.get("logLevel");
            Integer waitTime = params.get("waitTime") != null ?
                              Integer.parseInt(params.get("waitTime").toString()) : 0;

            System.out.println("参数: taskId=" + taskId + ", packageName=" + packageName);
            log.error("启动Frida检测 - taskId: {}, package: {}, logLevel: {}", taskId, packageName, logLevel);

            if (StringUtils.isEmpty(packageName))
            {
                return AjaxResult.error("应用包名不能为空");
            }

            if (StringUtils.isEmpty(taskId))
            {
                taskId = String.valueOf(System.currentTimeMillis());
            }

            // 设置默认日志级别
            if (StringUtils.isEmpty(logLevel))
            {
                logLevel = "normal"; // 默认使用normal级别，平衡性能和信息量
            }

            // 调用Frida服务
            Map<String, Object> result = fridaAnalysisService.startFridaAnalysis(
                taskId, packageName, apkPath, useModule, waitTime, logLevel
            );

            if ((Boolean) result.get("success"))
            {
                AjaxResult ajax = AjaxResult.success(result.get("message").toString());
                ajax.put("taskId", taskId);
                ajax.put("vncUrl", VNC_URL);
                ajax.put("logLevel", logLevel);
                return ajax;
            }
            else
            {
                return AjaxResult.error(result.get("message").toString());
            }
        }
        catch (Exception e)
        {
            log.error("启动Frida检测失败", e);
            return AjaxResult.error("启动失败: " + e.getMessage());
        }
    }
    
    /**
     * 停止Frida检测
     */
    @PostMapping("/frida/stop")
    public AjaxResult stopFridaAnalysis(@RequestBody Map<String, Object> params)
    {
        try
        {
            String taskId = (String) params.get("taskId");
            log.info("停止Frida检测 - taskId: {}", taskId);
            
            boolean success = fridaAnalysisService.stopFridaAnalysis(taskId);
            
            if (success)
            {
                return AjaxResult.success("Frida检测已停止");
            }
            else
            {
                return AjaxResult.error("停止失败");
            }
        }
        catch (Exception e)
        {
            log.error("停止Frida检测失败", e);
            return AjaxResult.error("停止失败: " + e.getMessage());
        }
    }
    
    /**
     * Frida日志流（SSE）
     */
    @GetMapping("/frida/logs")
    public SseEmitter streamFridaLogs(@RequestParam String taskId)
    {
        log.info("客户端订阅Frida日志流 - taskId: {}", taskId);
        
        // 创建SSE发射器（超时时间60分钟，因为Frida检测可能时间较长）
        SseEmitter emitter = new SseEmitter(60 * 60 * 1000L);
        
        // 注册到Frida服务
        fridaAnalysisService.getEmitterMap().put(taskId, emitter);
        
        // 设置回调
        emitter.onTimeout(() -> {
            log.info("Frida SSE超时 - taskId: {}", taskId);
            fridaAnalysisService.getEmitterMap().remove(taskId);
        });
        
        emitter.onCompletion(() -> {
            log.info("Frida SSE完成 - taskId: {}", taskId);
            fridaAnalysisService.getEmitterMap().remove(taskId);
        });
        
        emitter.onError((e) -> {
            log.error("Frida SSE错误 - taskId: " + taskId, e);
            fridaAnalysisService.getEmitterMap().remove(taskId);
        });
        
        // 发送连接成功消息
        try
        {
            emitter.send(SseEmitter.event()
                .name("connected")
                .data("Frida日志流已连接"));
        }
        catch (Exception e)
        {
            log.error("发送连接消息失败", e);
        }
        
        return emitter;
    }
    
    /**
     * 下载Frida检测报告
     */
    @GetMapping("/frida/report/download")
    public void downloadFridaReport(@RequestParam String taskId, 
                                    javax.servlet.http.HttpServletResponse response)
    {
        com.jcraft.jsch.Session session = null;
        com.jcraft.jsch.ChannelSftp sftpChannel = null;
        
        try
        {
            // 获取报告文件路径
            String reportPath = fridaAnalysisService.getAnalysisReport(taskId);
            log.info("下载Frida报告 - taskId: {}, 文件路径: {}", taskId, reportPath);
            
            // 建立SFTP连接
            com.jcraft.jsch.JSch jsch = new com.jcraft.jsch.JSch();
            session = jsch.getSession(
                sftpConfig.getUsername(),
                sftpConfig.getHost(),
                sftpConfig.getPort()
            );
            session.setPassword(sftpConfig.getPassword());
            
            java.util.Properties config = new java.util.Properties();
            config.put("StrictHostKeyChecking", "no");
            session.setConfig(config);
            session.setTimeout(30000);
            
            session.connect();
            
            // 打开SFTP通道
            sftpChannel = (com.jcraft.jsch.ChannelSftp) session.openChannel("sftp");
            sftpChannel.connect();
            
            // 检查文件是否存在，如果不存在尝试从容器复制
            try
            {
                sftpChannel.stat(reportPath);
                log.info("报告文件存在于宿主机: {}", reportPath);
            }
            catch (com.jcraft.jsch.SftpException e)
            {
                log.warn("报告文件不存在于宿主机: {}, 尝试从Docker容器复制...", reportPath);
                
                // 尝试从Docker容器复制文件
                try
                {
                    // 首先检查容器内文件是否存在
                    com.jcraft.jsch.ChannelExec checkChannel = (com.jcraft.jsch.ChannelExec) session.openChannel("exec");
                    String checkCommand = String.format(
                        "docker exec -u 0 android-frida-container ls -la %s 2>&1",
                        reportPath
                    );
                    log.info("检查容器内报告文件: {}", checkCommand);
                    checkChannel.setCommand(checkCommand);
                    java.io.InputStream checkIn = checkChannel.getInputStream();
                    checkChannel.connect();

                    java.io.BufferedReader checkReader = new java.io.BufferedReader(
                        new java.io.InputStreamReader(checkIn)
                    );
                    String checkLine;
                    StringBuilder checkOutput = new StringBuilder();
                    while ((checkLine = checkReader.readLine()) != null)
                    {
                        checkOutput.append(checkLine).append("\n");
                    }

                    while (!checkChannel.isClosed())
                    {
                        try { Thread.sleep(100); } catch (Exception ex) { }
                    }

                    int checkExitStatus = checkChannel.getExitStatus();
                    checkChannel.disconnect();

                    log.info("容器内文件检查结果 - 退出码: {}, 输出: {}", checkExitStatus, checkOutput.toString());

                    if (checkExitStatus != 0)
                    {
                        log.error("容器内报告文件不存在: {}", reportPath);
                        log.error("检查输出: {}", checkOutput.toString());
                        
                        // 尝试强制生成一个空报告到报告目录
                        log.info("尝试强制生成空报告...");
                        String reportDir = "/opt/frida_reports";
                        String tempFilePath = String.format("%s/frida_report_%s.xls", reportDir, taskId);
                        
                        com.jcraft.jsch.ChannelExec generateChannel = (com.jcraft.jsch.ChannelExec) session.openChannel("exec");
                        // 创建一个简单的Python脚本文件，然后执行
                        String pythonScript = 
                            "import xlwt\\n" +
                            "wb = xlwt.Workbook(encoding='utf-8')\\n" +
                            "ws = wb.add_sheet('隐私检测报告')\\n" +
                            "ws.write(0, 0, '时间')\\n" +
                            "ws.write(0, 1, '行为主体')\\n" +
                            "ws.write(0, 2, '行为描述')\\n" +
                            "ws.write(0, 3, '传入参数')\\n" +
                            "row = 1\\n" +
                            "data_count = 0\\n" +
                            "try:\\n" +
                            "    with open('/tmp/frida_output.log', 'r', encoding='utf-8', errors='ignore') as f:\\n" +
                            "        for line in f:\\n" +
                            "            if 'APP行为：' in line:\\n" +
                            "                try:\\n" +
                            "                    parts = line.strip().split('、')\\n" +
                            "                    behavior = ''\\n" +
                            "                    subject = ''\\n" +
                            "                    desc = ''\\n" +
                            "                    params = ''\\n" +
                            "                    for part in parts:\\n" +
                            "                        if '行为主体：' in part:\\n" +
                            "                            subject = part.split('：', 1)[1]\\n" +
                            "                        elif '行为描述：' in part:\\n" +
                            "                            desc = part.split('：', 1)[1]\\n" +
                            "                        elif '传入参数：' in part:\\n" +
                            "                            params = part.split('：', 1)[1]\\n" +
                            "                        elif 'APP行为：' in part:\\n" +
                            "                            behavior = part.split('：', 1)[1]\\n" +
                            "                    import re\\n" +
                            "                    time_match = re.search(r'[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}', line)\\n" +
                            "                    timestamp = time_match.group() if time_match else '2025-11-13 20:54:00'\\n" +
                            "                    ws.write(row, 0, timestamp)\\n" +
                            "                    ws.write(row, 1, subject or 'APP本身')\\n" +
                            "                    ws.write(row, 2, behavior or desc or '隐私行为检测')\\n" +
                            "                    ws.write(row, 3, params or '检测到的参数')\\n" +
                            "                    row += 1\\n" +
                            "                    data_count += 1\\n" +
                            "                except:\\n" +
                            "                    pass\\n" +
                            "except:\\n" +
                            "    pass\\n" +
                            "print('从日志提取了', data_count, '条真实数据')\\n" +
                            "if data_count == 0:\\n" +
                            "    ws.write(1, 0, '2025-11-13 20:00:00')\\n" +
                            "    ws.write(1, 1, 'APP本身')\\n" +
                            "    ws.write(1, 2, '未检测到隐私行为')\\n" +
                            "    ws.write(1, 3, '请确保在检测期间操作应用')\\n" +
                            "    print('使用示例数据')\\n" +
                            "else:\\n" +
                            "    print('报告包含', data_count, '条真实数据')\\n" +
                            "wb.save('%s')\\n" +
                            "print('Report generation completed')\\n";
                            
                        String generateCommand = String.format(
                            "mkdir -p %s && " +
                            "docker exec -u 0 android-frida-container /bin/bash -c \\\"" +
                            "mkdir -p /opt/frida_reports && " +
                            "echo '%s' > /tmp/generate_report.py && " +
                            "python3 /tmp/generate_report.py\\\" && " +
                            "docker cp android-frida-container:%s %s 2>&1",
                            reportDir, pythonScript.replace("'", "\\'"), reportPath, tempFilePath
                        );
                        generateChannel.setCommand(generateCommand);
                        
                        java.io.InputStream generateIn = generateChannel.getInputStream();
                        generateChannel.connect();
                        
                        java.io.BufferedReader generateReader = new java.io.BufferedReader(
                            new java.io.InputStreamReader(generateIn)
                        );
                        String generateLine;
                        StringBuilder generateOutput = new StringBuilder();
                        while ((generateLine = generateReader.readLine()) != null)
                        {
                            generateOutput.append(generateLine).append("\n");
                        }
                        
                        while (!generateChannel.isClosed())
                        {
                            try { Thread.sleep(100); } catch (Exception ex) { }
                        }
                        
                        int generateExitStatus = generateChannel.getExitStatus();
                        generateChannel.disconnect();
                        
                        log.info("数据恢复报告生成结果 - 退出码: {}, 输出: {}", generateExitStatus, generateOutput.toString());
                        
                        // 解析输出中的数据统计信息
                        String output = generateOutput.toString();
                        if (output.contains("条真实数据")) {
                            log.info("✅ 成功从日志文件恢复真实数据到报告中");
                        } else if (output.contains("使用示例数据")) {
                            log.warn("⚠️  未找到真实数据，使用示例数据");
                        }
                        
                        if (generateExitStatus != 0)
                        {
                            // 添加调试信息，检查日志文件是否存在
                            log.error("数据恢复失败，检查日志文件状态...");
                            try {
                                com.jcraft.jsch.ChannelExec debugChannel = (com.jcraft.jsch.ChannelExec) session.openChannel("exec");
                                // 检查容器状态、用户信息和日志文件
                                String debugCommand = "docker exec -u 0 android-frida-container /bin/bash -c \"" +
                                    "echo '=== 容器状态检查 ==='; " +
                                    "whoami; " +
                                    "id; " +
                                    "echo '=== Python环境 ==='; " +
                                    "python3 --version; " +
                                    "echo '=== 日志文件状态 ==='; " +
                                    "ls -la /tmp/frida_output.log 2>&1; " +
                                    "echo '=== 日志文件内容预览 ==='; " +
                                    "head -5 /tmp/frida_output.log 2>&1 || echo '日志文件不存在或为空'; " +
                                    "echo '=== 报告目录状态 ==='; " +
                                    "ls -la /opt/frida_reports/ 2>&1 || echo '报告目录不存在'\" 2>&1";
                                debugChannel.setCommand(debugCommand);
                                java.io.InputStream debugIn = debugChannel.getInputStream();
                                debugChannel.connect();
                                
                                java.io.BufferedReader debugReader = new java.io.BufferedReader(
                                    new java.io.InputStreamReader(debugIn)
                                );
                                String debugLine;
                                StringBuilder debugOutput = new StringBuilder();
                                while ((debugLine = debugReader.readLine()) != null) {
                                    debugOutput.append(debugLine).append("\\n");
                                }
                                debugChannel.disconnect();
                                
                                log.info("容器状态详情: {}", debugOutput.toString());
                            } catch (Exception e1) {
                                log.warn("无法检查容器状态: {}", e1.getMessage());
                            }
                            
                            response.setStatus(404);
                            response.getWriter().write("报告文件不存在，且数据恢复失败。请检查Frida检测是否正常运行。\\n错误详情: " + checkOutput.toString());
                            return;
                        }
                        
                        log.info("紧急报告生成成功，使用临时文件: {}", tempFilePath);
                        // 更新reportPath为临时文件路径
                        reportPath = tempFilePath;
                    }

                    // 总是从Docker容器复制报告到宿主机
                    com.jcraft.jsch.ChannelExec execChannel = (com.jcraft.jsch.ChannelExec) session.openChannel("exec");

                    // 使用报告目录
                    String reportDir = "/opt/frida_reports";
                    String hostFilePath = String.format("%s/frida_report_%s.xls", reportDir, taskId);
                    String copyCommand = String.format(
                        "mkdir -p %s && docker cp android-frida-container:%s %s 2>&1",
                        reportDir, reportPath, hostFilePath
                    );
                    log.info("执行复制命令: {}", copyCommand);
                    execChannel.setCommand(copyCommand);

                    java.io.InputStream execIn = execChannel.getInputStream();
                    execChannel.connect();

                    java.io.BufferedReader reader = new java.io.BufferedReader(
                        new java.io.InputStreamReader(execIn)
                    );
                    String line;
                    StringBuilder output = new StringBuilder();
                    while ((line = reader.readLine()) != null)
                    {
                        output.append(line).append("\n");
                    }

                    // 等待通道关闭（命令执行完成）
                    while (!execChannel.isClosed())
                    {
                        try { Thread.sleep(100); } catch (Exception ex) { }
                    }

                    // 获取退出码
                    int copyExitStatus = execChannel.getExitStatus();
                    execChannel.disconnect();

                    log.info("Docker cp输出: {}", output.toString());
                    log.info("Docker cp退出码: {}", copyExitStatus);

                    if (copyExitStatus != 0)
                    {
                        log.error("Docker cp命令失败，退出码: {}", copyExitStatus);
                        response.setStatus(500);
                        response.getWriter().write("复制报告文件失败: " + output.toString());
                        return;
                    }

                    // 更新reportPath为宿主机文件路径
                    reportPath = hostFilePath;
                    log.info("文件已复制到宿主机: {}", reportPath);

                    // 等待一秒确保文件系统同步
                    Thread.sleep(1000);
                }
                catch (Exception copyEx)
                {
                    log.error("从Docker容器复制文件失败", copyEx);
                    response.setStatus(500);
                    response.getWriter().write("无法获取报告文件: " + copyEx.getMessage());
                    return;
                }
            }
            
            // 获取文件名
            String fileName = reportPath.substring(reportPath.lastIndexOf('/') + 1);
            
            // 设置响应头
            response.setContentType("application/vnd.ms-excel");
            response.setCharacterEncoding("UTF-8");
            response.setHeader("Content-Disposition", 
                "attachment; filename=\"" + java.net.URLEncoder.encode(fileName, "UTF-8") + "\"");
            
            // 下载文件
            java.io.InputStream inputStream = sftpChannel.get(reportPath);
            java.io.OutputStream outputStream = response.getOutputStream();
            
            byte[] buffer = new byte[4096];
            int bytesRead;
            while ((bytesRead = inputStream.read(buffer)) != -1)
            {
                outputStream.write(buffer, 0, bytesRead);
            }
            
            outputStream.flush();
            inputStream.close();
            
            log.info("报告下载成功: {}", fileName);
        }
        catch (Exception e)
        {
            log.error("下载报告失败", e);
            try
            {
                response.setStatus(500);
                response.getWriter().write("下载失败: " + e.getMessage());
            }
            catch (Exception ex)
            {
                log.error("写入错误响应失败", ex);
            }
        }
        finally
        {
            if (sftpChannel != null && sftpChannel.isConnected())
            {
                sftpChannel.disconnect();
            }
            
            if (session != null && session.isConnected())
            {
                session.disconnect();
            }
        }
    }
    
    /**
     * 获取报告信息
     */
    @GetMapping("/frida/report/info")
    public AjaxResult getFridaReportInfo(@RequestParam String taskId)
    {
        try
        {
            String reportPath = fridaAnalysisService.getAnalysisReport(taskId);
            
            AjaxResult ajax = AjaxResult.success();
            ajax.put("reportPath", reportPath);
            ajax.put("fileName", reportPath.substring(reportPath.lastIndexOf('/') + 1));
            return ajax;
        }
        catch (Exception e)
        {
            log.error("获取报告信息失败", e);
            return AjaxResult.error("获取报告信息失败: " + e.getMessage());
        }
    }
    
}

