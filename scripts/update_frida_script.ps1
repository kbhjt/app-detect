# Frida隐私检测脚本更新脚本 (PowerShell版本)
# 用于将最新的frida_privacy_check.py上传到Ubuntu服务器并同步到Docker容器

# 配置
$UBUNTU_USER = "root"
$UBUNTU_HOST = ""  # 请填写您的Ubuntu服务器IP，例如: "192.168.1.100"
$UBUNTU_FRIDA_PATH = "/opt/camille/frida_privacy_check.py"
$DOCKER_CONTAINER = "android-frida-container"
$DOCKER_FRIDA_PATH = "/opt/camille/frida_privacy_check.py"

# 本地脚本路径
$LOCAL_SCRIPT = "$PSScriptRoot\frida_privacy_check.py"

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  Frida隐私检测脚本 - 一键更新工具" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

# 检查Ubuntu IP是否配置
if ([string]::IsNullOrEmpty($UBUNTU_HOST)) {
    Write-Host "❌ 错误：请先编辑此脚本，设置UBUNTU_HOST变量为您的Ubuntu服务器IP" -ForegroundColor Red
    Write-Host "   例如：`$UBUNTU_HOST = `"192.168.1.100`"" -ForegroundColor Yellow
    exit 1
}

# 检查本地脚本是否存在
if (-not (Test-Path $LOCAL_SCRIPT)) {
    Write-Host "❌ 错误：找不到本地脚本文件: $LOCAL_SCRIPT" -ForegroundColor Red
    Write-Host "   请确保在scripts目录下执行此脚本" -ForegroundColor Yellow
    exit 1
}

# 检查是否安装了scp命令（OpenSSH客户端）
$scpCommand = Get-Command scp -ErrorAction SilentlyContinue
if (-not $scpCommand) {
    Write-Host "❌ 错误：未找到scp命令" -ForegroundColor Red
    Write-Host "   Windows 10/11 用户请启用OpenSSH客户端：" -ForegroundColor Yellow
    Write-Host "   设置 -> 应用 -> 可选功能 -> 添加功能 -> OpenSSH 客户端" -ForegroundColor Yellow
    exit 1
}

Write-Host "📦 步骤1: 上传脚本到Ubuntu服务器..." -ForegroundColor Yellow
$scpTarget = "${UBUNTU_USER}@${UBUNTU_HOST}:${UBUNTU_FRIDA_PATH}"
scp $LOCAL_SCRIPT $scpTarget

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 上传失败！请检查SSH连接" -ForegroundColor Red
    Write-Host "   提示：首次连接可能需要确认指纹信息" -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ 上传成功" -ForegroundColor Green
Write-Host ""

Write-Host "🐳 步骤2: 同步脚本到Docker容器..." -ForegroundColor Yellow
$sshTarget = "${UBUNTU_USER}@${UBUNTU_HOST}"
$dockerCpCmd = "docker cp ${UBUNTU_FRIDA_PATH} ${DOCKER_CONTAINER}:${DOCKER_FRIDA_PATH}"
ssh $sshTarget $dockerCpCmd

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 同步到容器失败！" -ForegroundColor Red
    exit 1
}
Write-Host "✅ 同步成功" -ForegroundColor Green
Write-Host ""

Write-Host "🔍 步骤3: 验证脚本版本..." -ForegroundColor Yellow
$verifyCmd = "docker exec -u 0 ${DOCKER_CONTAINER} python3 ${DOCKER_FRIDA_PATH} -h 2>&1 | grep -E '\-d.*duration'"
$verifyResult = ssh $sshTarget $verifyCmd 2>$null

if ($verifyResult) {
    Write-Host "✅ 脚本验证成功！支持-d参数" -ForegroundColor Green
    Write-Host "   $verifyResult" -ForegroundColor Gray
} else {
    Write-Host "⚠️  警告：脚本可能没有-d参数支持" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "✨ 更新完成！" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 提示：现在可以在RuoYi系统中启动Frida检测了" -ForegroundColor Cyan


