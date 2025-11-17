package com.ruoyi.app.utils;

import java.io.File;
import java.io.FileInputStream;
import java.io.InputStream;
import java.util.Properties;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import com.jcraft.jsch.Channel;
import com.jcraft.jsch.ChannelSftp;
import com.jcraft.jsch.JSch;
import com.jcraft.jsch.Session;
import com.jcraft.jsch.SftpException;

/**
 * SFTP 文件上传工具类
 * 
 * @author ruoyi
 */
public class SftpUtils
{
    private static final Logger log = LoggerFactory.getLogger(SftpUtils.class);

    private String host;
    private int port;
    private String username;
    private String password;

    private Session session;
    private ChannelSftp channelSftp;

    public SftpUtils(String host, int port, String username, String password)
    {
        this.host = host;
        this.port = port;
        this.username = username;
        this.password = password;
    }

    /**
     * 连接SFTP服务器
     */
    public void connect() throws Exception
    {
        JSch jsch = new JSch();
        session = jsch.getSession(username, host, port);
        session.setPassword(password);

        Properties config = new Properties();
        config.put("StrictHostKeyChecking", "no");
        session.setConfig(config);
        session.setTimeout(30000);

        session.connect();
        log.info("SFTP session connected to {}:{}", host, port);

        Channel channel = session.openChannel("sftp");
        channel.connect();
        channelSftp = (ChannelSftp) channel;
        log.info("SFTP channel opened");
    }

    /**
     * 断开SFTP连接
     */
    public void disconnect()
    {
        if (channelSftp != null && channelSftp.isConnected())
        {
            channelSftp.disconnect();
            log.info("SFTP channel disconnected");
        }
        if (session != null && session.isConnected())
        {
            session.disconnect();
            log.info("SFTP session disconnected");
        }
    }

    /**
     * 上传文件
     * 
     * @param localFile 本地文件
     * @param remoteDir 远程目录
     * @param remoteFileName 远程文件名
     * @throws Exception
     */
    public void uploadFile(File localFile, String remoteDir, String remoteFileName) throws Exception
    {
        try (FileInputStream fis = new FileInputStream(localFile))
        {
            uploadFile(fis, remoteDir, remoteFileName);
        }
    }

    /**
     * 上传文件（使用输入流）
     * 
     * @param inputStream 输入流
     * @param remoteDir 远程目录
     * @param remoteFileName 远程文件名
     * @throws Exception
     */
    public void uploadFile(InputStream inputStream, String remoteDir, String remoteFileName) throws Exception
    {
        try
        {
            // 创建远程目录（如果不存在）
            createRemoteDir(remoteDir);

            // 切换到目标目录
            channelSftp.cd(remoteDir);

            // 上传文件
            channelSftp.put(inputStream, remoteFileName);
            log.info("File uploaded successfully: {}/{}", remoteDir, remoteFileName);
        }
        catch (SftpException e)
        {
            log.error("Failed to upload file to SFTP server", e);
            throw new Exception("SFTP上传失败: " + e.getMessage(), e);
        }
    }

    /**
     * 创建远程目录（递归创建）
     * 
     * @param remoteDir 远程目录路径
     * @throws SftpException
     */
    private void createRemoteDir(String remoteDir) throws SftpException
    {
        String[] dirs = remoteDir.split("/");
        String currentDir = "";

        for (String dir : dirs)
        {
            if (dir == null || dir.trim().isEmpty())
            {
                continue;
            }

            currentDir += "/" + dir;
            try
            {
                channelSftp.cd(currentDir);
            }
            catch (SftpException e)
            {
                // 目录不存在，创建它
                try
                {
                    channelSftp.mkdir(currentDir);
                    channelSftp.cd(currentDir);
                    log.info("Created remote directory: {}", currentDir);
                }
                catch (SftpException ex)
                {
                    log.error("Failed to create directory: {}", currentDir, ex);
                    throw ex;
                }
            }
        }
    }

    /**
     * 删除远程文件
     * 
     * @param remoteFilePath 远程文件路径
     * @throws Exception
     */
    public void deleteFile(String remoteFilePath) throws Exception
    {
        try
        {
            channelSftp.rm(remoteFilePath);
            log.info("File deleted successfully: {}", remoteFilePath);
        }
        catch (SftpException e)
        {
            log.error("Failed to delete file from SFTP server", e);
            throw new Exception("SFTP删除文件失败: " + e.getMessage(), e);
        }
    }

    /**
     * 检查文件是否存在
     * 
     * @param remoteFilePath 远程文件路径
     * @return true-存在, false-不存在
     */
    public boolean isFileExist(String remoteFilePath)
    {
        try
        {
            channelSftp.lstat(remoteFilePath);
            return true;
        }
        catch (SftpException e)
        {
            return false;
        }
    }
}

