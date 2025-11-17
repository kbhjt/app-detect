package com.ruoyi.app.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

/**
 * SFTP配置类
 * 
 * @author ruoyi
 */
@Component
@ConfigurationProperties(prefix = "sftp")
public class SftpConfig
{
    /**
     * SFTP服务器地址
     */
    private String host;

    /**
     * SFTP端口
     */
    private int port = 22;

    /**
     * 用户名
     */
    private String username;

    /**
     * 密码
     */
    private String password;

    /**
     * APK上传目录
     */
    private String apkUploadPath;

    /**
     * APK访问URL前缀
     */
    private String apkUrlPrefix;

    public String getHost()
    {
        return host;
    }

    public void setHost(String host)
    {
        this.host = host;
    }

    public int getPort()
    {
        return port;
    }

    public void setPort(int port)
    {
        this.port = port;
    }

    public String getUsername()
    {
        return username;
    }

    public void setUsername(String username)
    {
        this.username = username;
    }

    public String getPassword()
    {
        return password;
    }

    public void setPassword(String password)
    {
        this.password = password;
    }

    public String getApkUploadPath()
    {
        return apkUploadPath;
    }

    public void setApkUploadPath(String apkUploadPath)
    {
        this.apkUploadPath = apkUploadPath;
    }

    public String getApkUrlPrefix()
    {
        return apkUrlPrefix;
    }

    public void setApkUrlPrefix(String apkUrlPrefix)
    {
        this.apkUrlPrefix = apkUrlPrefix;
    }

    @Override
    public String toString()
    {
        return "SftpConfig{" +
                "host='" + host + '\'' +
                ", port=" + port +
                ", username='" + username + '\'' +
                ", apkUploadPath='" + apkUploadPath + '\'' +
                ", apkUrlPrefix='" + apkUrlPrefix + '\'' +
                '}';
    }
}

