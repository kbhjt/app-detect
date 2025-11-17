#!/bin/bash
# Frida隐私合规检测环境部署脚本
# 用于在Ubuntu服务器上快速部署Frida检测环境

set -e

echo "========================================="
echo "  Frida隐私合规检测环境部署脚本"
echo "========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否为root用户
if [ "$EUID" -eq 0 ]; then 
    echo -e "${YELLOW}警告: 建议使用普通用户运行此脚本${NC}"
    read -p "是否继续? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 1. 更新系统
echo -e "${GREEN}[1/7] 更新系统包...${NC}"
sudo apt update
echo ""

# 2. 安装Python3和pip
echo -e "${GREEN}[2/7] 安装Python3和pip...${NC}"
sudo apt install -y python3 python3-pip
python3 --version
pip3 --version
echo ""

# 3. 安装Frida
echo -e "${GREEN}[3/7] 安装Frida和相关依赖...${NC}"
pip3 install frida frida-tools xlwt click opencv-python
echo ""

# 4. 验证Frida安装
echo -e "${GREEN}[4/7] 验证Frida安装...${NC}"
frida --version
echo ""

# 5. 创建目录
echo -e "${GREEN}[5/7] 创建工作目录...${NC}"
sudo mkdir -p /opt/camille
sudo mkdir -p /opt/reports
echo "目录创建完成:"
echo "  - /opt/camille (Frida脚本目录)"
echo "  - /opt/reports (报告输出目录)"
echo ""

# 6. 设置权限
echo -e "${GREEN}[6/7] 设置目录权限...${NC}"
sudo chown -R $USER:$USER /opt/camille
sudo chown -R $USER:$USER /opt/reports
echo ""

# 7. 部署提示
echo -e "${GREEN}[7/7] 部署完成！${NC}"
echo ""
echo "========================================="
echo "  后续手动操作步骤"
echo "========================================="
echo ""
echo "1. 复制camille项目文件到服务器："
echo "   scp -r camille/* user@server:/opt/camille/"
echo ""
echo "2. 复制集成脚本："
echo "   scp scripts/frida_privacy_check.py user@server:/opt/camille/"
echo ""
echo "3. 设置脚本执行权限："
echo "   chmod +x /opt/camille/frida_privacy_check.py"
echo ""
echo "4. 准备Android设备/模拟器："
echo "   a. 下载frida-server (https://github.com/frida/frida/releases)"
echo "   b. adb push frida-server /data/local/tmp/"
echo "   c. adb shell \"chmod 755 /data/local/tmp/frida-server\""
echo "   d. adb shell \"su -c '/data/local/tmp/frida-server &'\""
echo ""
echo "5. 测试Frida连接："
echo "   frida-ps -U"
echo ""
echo "6. 测试脚本运行："
echo "   cd /opt/camille"
echo "   python3 frida_privacy_check.py com.example.app -ia"
echo ""
echo -e "${GREEN}安装完成！${NC}"
echo ""

# 显示ADB设备
echo "========================================="
echo "  检查ADB设备连接"
echo "========================================="
if command -v adb &> /dev/null; then
    echo "ADB已安装，正在检查连接的设备..."
    adb devices
    echo ""
else
    echo -e "${YELLOW}未安装ADB工具${NC}"
    echo "安装方法: sudo apt install adb"
    echo ""
fi

# 显示Frida版本信息
echo "========================================="
echo "  版本信息"
echo "========================================="
echo "Python版本: $(python3 --version)"
echo "Frida版本: $(frida --version)"
echo ""

echo -e "${GREEN}脚本执行完成！${NC}"


