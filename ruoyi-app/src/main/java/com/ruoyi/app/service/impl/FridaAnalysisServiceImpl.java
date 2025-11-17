package com.ruoyi.app.service.impl;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.text.SimpleDateFormat;
import java.util.Date;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;
import com.jcraft.jsch.ChannelExec;
import com.jcraft.jsch.JSch;
import com.jcraft.jsch.Session;
import com.ruoyi.app.config.SftpConfig;
import com.ruoyi.app.service.IFridaAnalysisService;

@Service
public class FridaAnalysisServiceImpl implements IFridaAnalysisService {
    
    private static final Logger log = LoggerFactory.getLogger(FridaAnalysisServiceImpl.class);
    
    @Autowired
    private SftpConfig sftpConfig;
    
    private static final String FRIDA_SCRIPT_PATH = "/opt/camille/frida_privacy_check.py";
    private static final String REPORT_OUTPUT_DIR = "/opt/frida_reports";
    private static final String CONTAINER_NAME = "android-frida-container";
    
    private final Map<String, Boolean> stopFlagMap = new ConcurrentHashMap<>();
    private final Map<String, SseEmitter> emitterMap = new ConcurrentHashMap<>();
    
    private Session createSSHSession() {
        try {
            JSch jsch = new JSch();
            Session session = jsch.getSession(sftpConfig.getUsername(), sftpConfig.getHost(), sftpConfig.getPort());
            session.setPassword(sftpConfig.getPassword());
            session.setConfig("StrictHostKeyChecking", "no");
            session.setTimeout(30000);
            session.connect();
            return session;
        } catch (Exception e) {
            log.error("SSH连接失败: {}", e.getMessage());
            return null;
        }
    }
    
    public boolean startFridaAnalysis(String taskId, String packageName, String deviceId, 
                                    String modules, String attachMode, int delayTime) {
        try {
            stopFlagMap.put(taskId, false);
            sendLogWithControl(taskId, "🚀 启动Frida检测: " + packageName, "info");
            
            Thread analysisThread = new Thread(() -> {
                executeFridaAnalysis(taskId, packageName, modules, attachMode, delayTime);
            });
            analysisThread.start();
            
            return true;
        } catch (Exception e) {
            log.error("启动失败: {}", e.getMessage());
            sendLogWithControl(taskId, "❌ 启动失败: " + e.getMessage(), "error");
            return false;
        }
    }
    
    private void executeFridaAnalysis(String taskId, String packageName, String modules, 
                                    String attachMode, int delayTime) {
        Session session = null;
        ChannelExec channel = null;
        
        try {
            session = createSSHSession();
            if (session == null) {
                sendLogWithControl(taskId, "❌ SSH连接失败", "error");
                return;
            }
            
            // 创建final引用供lambda使用
            final Session finalSession = session;
            
            String command = buildCamilleCommand(taskId, packageName, modules, attachMode, delayTime);
            log.info("执行命令: {}", command);
            sendLogWithControl(taskId, "🔧 执行命令: " + command, "info");
            
            channel = (ChannelExec) session.openChannel("exec");
            channel.setCommand(command);
            
            InputStream inputStream = channel.getInputStream();
            InputStream errorStream = channel.getErrStream();
            channel.connect();
            
            sendLogWithControl(taskId, "✅ 命令已发送到服务器", "success");
            
            sendLogWithControl(taskId, "🔍 Docker容器中的Frida检测已启动，请在模拟器中操作应用", "info");
            sendLogWithControl(taskId, "💡 建议操作：登录、拍照、定位、通讯录、拨号等功能", "warn");
            
            // 直接处理脚本输出，实时传输到前端
            processFridaScriptOutput(taskId, inputStream, errorStream, channel);
            
        } catch (Exception e) {
            log.error("执行失败: {}", e.getMessage());
            sendLogWithControl(taskId, "❌ 执行失败: " + e.getMessage(), "error");
        } finally {
            if (channel != null) channel.disconnect();
            if (session != null) session.disconnect();
        }
    }
    
    private String buildCamilleCommand(String taskId, String packageName, String modules, 
                                     String attachMode, int delayTime) {
        StringBuilder cmd = new StringBuilder();
        
        // 在宿主机创建报告目录
        cmd.append("mkdir -p ").append(REPORT_OUTPUT_DIR).append(" && ");
        
        // 在Docker容器中以root身份执行frida_privacy_check.py
        cmd.append("docker exec -i -u 0 ").append(CONTAINER_NAME).append(" bash -c \"");
        
        // 执行frida_privacy_check.py脚本
        cmd.append("python3 ").append(FRIDA_SCRIPT_PATH).append(" ").append(packageName);
        
        // 添加检测时长参数
        int duration = delayTime > 0 ? delayTime : 300;
        cmd.append(" -d ").append(duration);
        
        // 添加Hook模式参数
        if ("attach".equals(attachMode)) {
            cmd.append(" -ia");  // --isattach
        }
        
        // 添加模块参数
        if (modules != null && !"all".equals(modules)) {
            cmd.append(" -u ").append(modules);  // --use
        }
        
        // 容器内的报告文件路径
        String reportFile = REPORT_OUTPUT_DIR + "/frida_report_" + taskId + ".xls";
        cmd.append(" -f ").append(reportFile);
        
        // 不重定向输出，让脚本输出直接通过SSH传递给Java后端
        // 这样可以实时显示到前端日志流
        
        // 结束Docker exec命令
        cmd.append("\"");
        
        return cmd.toString();
    }
    
    /**
     * 处理Frida脚本输出，实时传输到前端（优化版本）
     */
    private void processFridaScriptOutput(String taskId, InputStream inputStream, 
                                        InputStream errorStream, ChannelExec channel) {
        try {
            BufferedReader stdReader = new BufferedReader(new InputStreamReader(inputStream, StandardCharsets.UTF_8));
            BufferedReader errReader = new BufferedReader(new InputStreamReader(errorStream, StandardCharsets.UTF_8));
            
            String line;
            int totalLines = 0;
            int privacyEvents = 0;
            int sentLines = 0;
            long lastSendTime = System.currentTimeMillis();
            
            // 输出控制参数
            final int MAX_LINES_PER_SECOND = 10; // 每秒最多发送10行
            final int MAX_TOTAL_LINES = 200; // 总共最多发送200行到前端
            final long SEND_INTERVAL = 100; // 发送间隔100ms
            
            sendLogWithControl(taskId, "📡 开始接收Frida脚本输出...", "info");
            
            while (!stopFlagMap.getOrDefault(taskId, false) && !channel.isClosed()) {
                boolean hasNewOutput = false;
                
                // 读取标准输出
                while (stdReader.ready() && (line = stdReader.readLine()) != null) {
                    totalLines++;
                    hasNewOutput = true;
                    
                    // 统计隐私事件
                    if (isPrivacyEvent(line)) {
                        privacyEvents++;
                    }
                    
                    // 控制发送到前端的输出量
                    boolean shouldSend = shouldSendToFrontend(line, sentLines, lastSendTime, MAX_LINES_PER_SECOND, MAX_TOTAL_LINES);
                    
                    if (shouldSend) {
                        String logLevel = determineFridaLogLevel(line);
                        sendLogWithControl(taskId, line, logLevel);
                        sentLines++;
                        lastSendTime = System.currentTimeMillis();
                    }
                    
                    // 只记录重要日志到后端控制台
                    if (isImportantLog(line)) {
                        log.info("Frida重要输出: {}", line);
                    }
                }
                
                // 读取错误输出（错误输出总是发送）
                while (errReader.ready() && (line = errReader.readLine()) != null) {
                    sendLogWithControl(taskId, "❌ " + line, "error");
                    log.error("Frida脚本错误: {}", line);
                }
                
                // 如果没有新输出，适当延长等待时间
                if (!hasNewOutput) {
                    Thread.sleep(200);
                } else {
                    Thread.sleep(SEND_INTERVAL);
                }
            }
            
            // 发送最终统计
            sendLogWithControl(taskId, String.format("✅ 脚本执行完成！总输出%d行，隐私事件%d个，已显示%d行", 
                totalLines, privacyEvents, sentLines), "success");
            
            if (sentLines >= MAX_TOTAL_LINES) {
                sendLogWithControl(taskId, "💡 为防止页面卡顿，已限制显示行数。完整日志请查看后端控制台", "warn");
            }
            
        } catch (Exception e) {
            log.error("处理Frida脚本输出失败: {}", e.getMessage());
            sendLogWithControl(taskId, "❌ 处理脚本输出失败: " + e.getMessage(), "error");
        }
    }
    
    /**
     * 判断是否应该发送到前端
     */
    private boolean shouldSendToFrontend(String line, int sentLines, long lastSendTime, 
                                       int maxLinesPerSecond, int maxTotalLines) {
        // 超过总行数限制
        if (sentLines >= maxTotalLines) {
            return false;
        }
        
        // 重要日志总是发送
        if (isImportantLog(line)) {
            return true;
        }
        
        // 控制发送频率
        long currentTime = System.currentTimeMillis();
        if (currentTime - lastSendTime < (1000 / maxLinesPerSecond)) {
            return false;
        }
        
        return true;
    }
    
    /**
     * 判断是否为重要日志
     */
    private boolean isImportantLog(String line) {
        return line.contains("[ERROR]") || 
               line.contains("[SUCCESS]") || 
               line.contains("APP行为：") || 
               line.contains("隐私") || 
               line.contains("权限") || 
               line.contains("✅") || 
               line.contains("❌") || 
               line.contains("⚠️") || 
               line.contains("━━━") ||
               line.contains("Frida") ||
               line.contains("Hook") ||
               line.contains("检测");
    }
    
    /**
     * 根据Frida脚本输出内容确定日志级别
     */
    private String determineFridaLogLevel(String line) {
        if (line.contains("[ERROR]") || line.contains("❌")) {
            return "error";
        } else if (line.contains("[WARN]") || line.contains("⚠️")) {
            return "warn";
        } else if (line.contains("[SUCCESS]") || line.contains("✅")) {
            return "success";
        } else if (line.contains("[ALERT]") || line.contains("APP行为：") || line.contains("隐私")) {
            return "alert";
        } else if (line.contains("[INFO]") || line.contains("━━━")) {
            return "info";
        } else {
            return "info";
        }
    }
    
    
    private String formatOutput(String line) {
        String timestamp = new SimpleDateFormat("HH:mm:ss").format(new Date());
        
        if (line.contains("APP行为：") || line.contains("隐私")) {
            return String.format("[%s] 🔒 %s", timestamp, line);
        } else if (line.contains("调用堆栈：")) {
            return String.format("[%s] 📚 %s", timestamp, line);
        } else if (line.contains("权限")) {
            return String.format("[%s] 🛡️ %s", timestamp, line);
        } else {
            return String.format("[%s] %s", timestamp, line);
        }
    }
    
    private String getLogLevel(String line) {
        if (line.contains("错误") || line.contains("error")) return "error";
        if (line.contains("警告") || line.contains("warn")) return "warn";
        if (line.contains("完成") || line.contains("success")) return "success";
        if (line.contains("APP行为：") || line.contains("隐私")) return "alert";
        return "info";
    }
    
    private boolean isPrivacyEvent(String line) {
        return line.contains("APP行为：") || line.contains("隐私") || line.contains("权限") ||
               line.contains("位置") || line.contains("联系人") || line.contains("电话") ||
               line.contains("设备") || line.contains("调用堆栈：");
    }
    
    @Override
    public boolean stopFridaAnalysis(String taskId) {
        try {
            stopFlagMap.put(taskId, true);
            sendLogWithControl(taskId, "🛑 正在停止检测...", "info");
            
            Session session = createSSHSession();
            if (session != null) {
                ChannelExec channel = (ChannelExec) session.openChannel("exec");
                // 在Docker容器中以root身份停止frida进程
                String killCommand = "docker exec -u 0 " + CONTAINER_NAME + " bash -c \"" +
                    "pkill -f 'python3.*frida_privacy_check.py' || pkill -f frida || echo 'Frida进程已停止'\"";
                channel.setCommand(killCommand);
                channel.connect();
                Thread.sleep(2000);
                channel.disconnect();
                session.disconnect();
            }
            
            sendLogWithControl(taskId, "✅ 检测已停止", "success");
            return true;
        } catch (Exception e) {
            log.error("停止失败: {}", e.getMessage());
            return false;
        }
    }
    
    @Override
    public String getAnalysisReport(String taskId) {
        return String.format("%s/frida_report_%s.xls", REPORT_OUTPUT_DIR, taskId);
    }
    
    @Override
    public Map<String, SseEmitter> getEmitterMap() {
        return emitterMap;
    }
    
    private void sendLogWithControl(String taskId, String message, String level) {
        try {
            SseEmitter emitter = emitterMap.get(taskId);
            if (emitter != null) {
                Map<String, Object> logData = new HashMap<>();
                logData.put("message", message);
                logData.put("level", level);
                logData.put("timestamp", new SimpleDateFormat("HH:mm:ss").format(new Date()));
                
                // 指定事件名称为'log'，匹配前端期望
                emitter.send(SseEmitter.event()
                    .name("log")
                    .data(logData));
            }
        } catch (Exception e) {
            log.error("发送SSE日志失败，移除emitter: {}", e.getMessage());
            emitterMap.remove(taskId);
        }
    }
    
    @Override
    public Map<String, Object> startFridaAnalysis(String taskId, String packageName, String apkPath,
                                                  String useModule, Integer waitTime) {
        return startFridaAnalysis(taskId, packageName, apkPath, useModule, waitTime, "normal");
    }

    @Override
    public Map<String, Object> startFridaAnalysis(String taskId, String packageName, String apkPath,
                                                  String useModule, Integer waitTime, String logLevel) {
        Map<String, Object> result = new HashMap<>();
        try {
            boolean success = startFridaAnalysis(taskId, packageName, "", 
                useModule != null ? useModule : "all", "spawn", waitTime != null ? waitTime : 0);
            result.put("success", success);
            result.put("message", success ? "检测已启动" : "启动失败");
            result.put("taskId", taskId);
        } catch (Exception e) {
            result.put("success", false);
            result.put("message", "启动失败: " + e.getMessage());
        }
        return result;
    }
}
