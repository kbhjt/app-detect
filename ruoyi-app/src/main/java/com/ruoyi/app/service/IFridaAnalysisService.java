package com.ruoyi.app.service;

import java.util.Map;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

/**
 * Frida隐私合规分析服务接口
 * 
 * @author ruoyi
 */
public interface IFridaAnalysisService {
    
    /**
     * 启动Frida分析（5参数版本）
     * 
     * @param taskId 任务ID
     * @param packageName 包名
     * @param apkPath APK路径
     * @param useModule 使用的模块
     * @param waitTime 等待时间
     * @return 分析结果
     */
    Map<String, Object> startFridaAnalysis(String taskId, String packageName, String apkPath,
                                          String useModule, Integer waitTime);
    
    /**
     * 启动Frida分析（6参数版本，带日志级别）
     * 
     * @param taskId 任务ID
     * @param packageName 包名
     * @param apkPath APK路径
     * @param useModule 使用的模块
     * @param waitTime 等待时间
     * @param logLevel 日志级别
     * @return 分析结果
     */
    Map<String, Object> startFridaAnalysis(String taskId, String packageName, String apkPath,
                                          String useModule, Integer waitTime, String logLevel);
    
    /**
     * 停止Frida分析
     * 
     * @param taskId 任务ID
     * @return 是否成功停止
     */
    boolean stopFridaAnalysis(String taskId);
    
    /**
     * 获取分析报告
     * 
     * @param taskId 任务ID
     * @return 报告文件路径
     */
    String getAnalysisReport(String taskId);
    
    /**
     * 获取SSE发射器映射（用于实时日志推送）
     * 
     * @return SSE发射器映射
     */
    Map<String, SseEmitter> getEmitterMap();
}
