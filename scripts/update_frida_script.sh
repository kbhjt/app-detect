#!/bin/bash
# Frida隐私检测脚本更新脚本
# 用于将最新的frida_privacy_check.py上传到Ubuntu服务器并同步到Docker容器

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置
UBUNTU_USER="root"
UBUNTU_HOST=""  # 请填写您的Ubuntu服务器IP
UBUNTU_FRIDA_PATH="/opt/camille/frida_privacy_check.py"
DOCKER_CONTAINER="android-frida-container"
DOCKER_FRIDA_PATH="/opt/camille/frida_privacy_check.py"

# 本地脚本路径（相对于此脚本的位置）
LOCAL_SCRIPT="frida_privacy_check.py"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Frida隐私检测脚本 - 一键更新工具"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 检查Ubuntu IP是否配置
if [ -z "$UBUNTU_HOST" ]; then
    echo -e "${RED}❌ 错误：请先编辑此脚本，设置UBUNTU_HOST变量为您的Ubuntu服务器IP${NC}"
    exit 1
fi

# 检查本地脚本是否存在
if [ ! -f "$LOCAL_SCRIPT" ]; then
    echo -e "${RED}❌ 错误：找不到本地脚本文件: $LOCAL_SCRIPT${NC}"
    echo "   请确保在scripts目录下执行此脚本"
    exit 1
fi

echo -e "${YELLOW}📦 步骤1: 上传脚本到Ubuntu服务器...${NC}"
scp "$LOCAL_SCRIPT" "${UBUNTU_USER}@${UBUNTU_HOST}:${UBUNTU_FRIDA_PATH}"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 上传失败！请检查SSH连接${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 上传成功${NC}"
echo ""

echo -e "${YELLOW}🐳 步骤2: 同步脚本到Docker容器...${NC}"
ssh "${UBUNTU_USER}@${UBUNTU_HOST}" "docker cp ${UBUNTU_FRIDA_PATH} ${DOCKER_CONTAINER}:${DOCKER_FRIDA_PATH}"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 同步到容器失败！${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 同步成功${NC}"
echo ""

echo -e "${YELLOW}🔍 步骤3: 验证脚本版本...${NC}"
ssh "${UBUNTU_USER}@${UBUNTU_HOST}" "docker exec -u 0 ${DOCKER_CONTAINER} python3 ${DOCKER_FRIDA_PATH} -h 2>&1" | grep -E "\-d.*duration"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 脚本验证成功！支持-d参数${NC}"
else
    echo -e "${YELLOW}⚠️  警告：脚本可能没有-d参数支持${NC}"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✨ 更新完成！${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"


