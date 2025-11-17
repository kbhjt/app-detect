package com.ruoyi.app.controller;

import java.io.File;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;
import com.ruoyi.app.config.SftpConfig;
import com.ruoyi.app.utils.SftpUtils;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.StringUtils;
import com.ruoyi.common.utils.uuid.IdUtils;

/**
 * 应用检测任务控制器
 * 
 * @author ruoyi
 */
@RestController
@RequestMapping("/app/task")
public class AppTaskController extends BaseController
{
    private static final Logger log = LoggerFactory.getLogger(AppTaskController.class);
    
    @Autowired
    private SftpConfig sftpConfig;

    /**
     * APK/IPA文件上传（通过SFTP上传到Ubuntu服务器）
     */
    @PostMapping("/upload")
    public AjaxResult uploadApk(MultipartFile file) throws Exception
    {
        SftpUtils sftpUtils = null;
        try
        {
            // 验证文件类型
            String originalFilename = file.getOriginalFilename();
            if (StringUtils.isEmpty(originalFilename))
            {
                return AjaxResult.error("文件名不能为空");
            }

            // 检查文件扩展名
            String extension = originalFilename.substring(originalFilename.lastIndexOf(".") + 1).toLowerCase();
            if (!"apk".equals(extension) && !"ipa".equals(extension))
            {
                return AjaxResult.error("只支持上传 APK 或 IPA 格式的文件");
            }

            // 检查文件大小（限制300MB）
            long maxSize = 300 * 1024 * 1024L;
            if (file.getSize() > maxSize)
            {
                return AjaxResult.error("文件大小不能超过 300MB");
            }

            // 生成唯一文件名（保留原始扩展名）
            String uniqueFileName = IdUtils.fastSimpleUUID() + "_" + originalFilename;
            
            // 连接SFTP服务器
            sftpUtils = new SftpUtils(
                sftpConfig.getHost(),
                sftpConfig.getPort(),
                sftpConfig.getUsername(),
                sftpConfig.getPassword()
            );
            sftpUtils.connect();
            
            // 上传文件到Ubuntu服务器的 /opt/apk 目录
            sftpUtils.uploadFile(
                file.getInputStream(),
                sftpConfig.getApkUploadPath(),
                uniqueFileName
            );
            
            // 构建文件完整路径
            String remoteFilePath = sftpConfig.getApkUploadPath() + "/" + uniqueFileName;
            
            // 构建文件访问URL
            String fileUrl = sftpConfig.getApkUrlPrefix() + "/" + uniqueFileName;
            
            // 返回结果
            AjaxResult ajax = AjaxResult.success("文件上传成功");
            ajax.put("fileName", uniqueFileName);
            ajax.put("originalFilename", originalFilename);
            ajax.put("filePath", remoteFilePath); // Ubuntu服务器绝对路径
            ajax.put("fileSize", file.getSize());
            ajax.put("url", fileUrl);
            
            log.info("APK文件通过SFTP上传成功: {}, 远程路径: {}", originalFilename, remoteFilePath);
            
            return ajax;
        }
        catch (Exception e)
        {
            log.error("APK文件上传失败", e);
            return AjaxResult.error("文件上传失败: " + e.getMessage());
        }
        finally
        {
            // 断开SFTP连接
            if (sftpUtils != null)
            {
                sftpUtils.disconnect();
            }
        }
    }

    /**
     * 批量上传APK/IPA文件（通过SFTP上传到Ubuntu服务器）
     */
    @PostMapping("/uploads")
    public AjaxResult uploadApks(List<MultipartFile> files) throws Exception
    {
        SftpUtils sftpUtils = null;
        try
        {
            if (files == null || files.isEmpty())
            {
                return AjaxResult.error("请选择要上传的文件");
            }

            // 连接SFTP服务器
            sftpUtils = new SftpUtils(
                sftpConfig.getHost(),
                sftpConfig.getPort(),
                sftpConfig.getUsername(),
                sftpConfig.getPassword()
            );
            sftpUtils.connect();

            List<String> fileNames = new ArrayList<>();
            List<String> filePaths = new ArrayList<>();
            List<String> originalFilenames = new ArrayList<>();
            List<Long> fileSizes = new ArrayList<>();

            for (MultipartFile file : files)
            {
                // 验证文件
                String originalFilename = file.getOriginalFilename();
                if (StringUtils.isEmpty(originalFilename))
                {
                    continue;
                }

                String extension = originalFilename.substring(originalFilename.lastIndexOf(".") + 1).toLowerCase();
                if (!"apk".equals(extension) && !"ipa".equals(extension))
                {
                    log.warn("跳过非APK/IPA文件: {}", originalFilename);
                    continue;
                }

                // 生成唯一文件名
                String uniqueFileName = IdUtils.fastSimpleUUID() + "_" + originalFilename;
                
                // 上传文件到Ubuntu服务器
                sftpUtils.uploadFile(
                    file.getInputStream(),
                    sftpConfig.getApkUploadPath(),
                    uniqueFileName
                );
                
                String remoteFilePath = sftpConfig.getApkUploadPath() + "/" + uniqueFileName;
                
                fileNames.add(uniqueFileName);
                filePaths.add(remoteFilePath);
                originalFilenames.add(originalFilename);
                fileSizes.add(file.getSize());
            }

            if (fileNames.isEmpty())
            {
                return AjaxResult.error("没有有效的APK/IPA文件");
            }

            AjaxResult ajax = AjaxResult.success("成功上传 " + fileNames.size() + " 个文件");
            ajax.put("fileNames", fileNames);
            ajax.put("filePaths", filePaths);
            ajax.put("originalFilenames", originalFilenames);
            ajax.put("fileSizes", fileSizes);
            
            log.info("批量上传APK文件到SFTP成功，共 {} 个文件", fileNames.size());
            
            return ajax;
        }
        catch (Exception e)
        {
            log.error("批量上传APK文件失败", e);
            return AjaxResult.error("批量上传失败: " + e.getMessage());
        }
        finally
        {
            // 断开SFTP连接
            if (sftpUtils != null)
            {
                sftpUtils.disconnect();
            }
        }
    }

    /**
     * 提交检测任务
     */
    @PostMapping("/submit")
    public AjaxResult submitTask(@RequestBody Map<String, Object> taskData)
    {
        try
        {
            log.info("接收到任务提交请求: {}", taskData);
            
            // 提取任务信息
            String taskName = (String) taskData.get("taskName");
            
            // 提取文件路径信息（重要：用于后续安装APK）
            @SuppressWarnings("unchecked")
            List<String> filePaths = (List<String>) taskData.get("filePaths");
            
            // 验证必填项
            if (StringUtils.isEmpty(taskName))
            {
                return AjaxResult.error("任务名称不能为空");
            }
            
            if (filePaths == null || filePaths.isEmpty())
            {
                return AjaxResult.error("请先上传应用文件");
            }
            
            // 生成任务ID（实际项目中应该保存到数据库并返回真实ID）
            long taskId = System.currentTimeMillis();
            
            // 验证文件是否存在
            for (int i = 0; i < filePaths.size(); i++)
            {
                String filePath = filePaths.get(i);
                File file = new File(filePath);
                if (!file.exists())
                {
                    log.warn("文件不存在: {}", filePath);
                    // 注意：如果是模拟路径，文件可能不存在，这里只记录警告
                }
                else
                {
                    log.info("验证文件存在: {} (大小: {} bytes)", filePath, file.length());
                }
            }
            
            // TODO: 实际项目中应该：
            // 1. 保存任务信息到数据库
            // 2. 保存文件关联信息到数据库
            // 3. 触发异步分析任务
            // 4. 返回真实的任务ID
            
            log.info("任务创建成功 - 任务ID: {}, 任务名称: {}, 文件数: {}", 
                taskId, taskName, filePaths.size());
            
            // 返回成功结果
            AjaxResult ajax = AjaxResult.success("任务提交成功");
            ajax.put("taskId", taskId);
            ajax.put("taskName", taskName);
            ajax.put("apkPath", filePaths.get(0)); // 第一个APK路径
            ajax.put("fileCount", filePaths.size());
            
            return ajax;
        }
        catch (Exception e)
        {
            log.error("任务提交失败", e);
            return AjaxResult.error("任务提交失败: " + e.getMessage());
        }
    }
}

