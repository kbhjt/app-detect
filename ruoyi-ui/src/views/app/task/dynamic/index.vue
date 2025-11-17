<template>
  <div class="app-container dynamic-analysis-container">
    <!-- 顶部任务信息和操作栏 -->
    <el-card class="header-card" shadow="never">
      <div class="header-content">
        <div class="task-info-brief">
          <h3>
            <i class="el-icon-monitor"></i>
            动态分析
          </h3>
          <div v-if="taskInfo.taskName" class="task-details">
            <el-tag size="small" type="info">{{ taskInfo.taskId }}</el-tag>
            <span class="task-name">{{ taskInfo.taskName }}</span>
            <span class="apk-path">{{ taskInfo.apkPath }}</span>
          </div>
        </div>
        <div class="action-buttons">
          <el-button-group>
            <el-button
              v-if="!fridaStarted"
              type="primary"
              icon="el-icon-magic-stick"
              @click="openFridaDialog"
              :disabled="!taskInfo.apkPath"
            >
              开始Frida检测
            </el-button>
            <el-button
              v-else
              type="danger"
              icon="el-icon-video-pause"
              @click="stopFridaAnalysis"
              :loading="stopping"
            >
              停止检测
            </el-button>
          </el-button-group>
          <el-button
            icon="el-icon-refresh"
            @click="refreshPage"
          >
            刷新
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 无任务信息时的提示 -->
    <el-empty v-if="!taskInfo.apkPath" description="暂无分析任务" style="margin-top: 50px;">
      <el-button type="primary" @click="goToNewTask">创建新任务</el-button>
    </el-empty>

    <!-- 主要内容区域：左边模拟器，右边日志 -->
    <el-row v-else :gutter="20" class="main-content">
      <!-- 左侧：Android模拟器 -->
      <el-col :span="10" class="simulator-panel">
        <el-card shadow="never" class="simulator-card">
          <div slot="header" class="card-header">
            <span><i class="el-icon-mobile-phone"></i> Android 模拟器</span>
            <el-tag v-if="vncConnected" type="success" size="small">已连接</el-tag>
            <el-tag v-else type="info" size="small">未连接</el-tag>
          </div>
          <div class="simulator-wrapper">
            <div v-if="analysisStarted && vncUrl" class="vnc-container">
              <iframe
                ref="vncIframe"
                :src="vncUrl"
                frameborder="0"
                class="vnc-iframe"
                @load="handleVncLoad"
              ></iframe>
            </div>
            <div v-else class="vnc-placeholder">
              <i class="el-icon-mobile-phone"></i>
              <p>点击"开始分析"启动模拟器</p>
            </div>
          </div>
          <div class="simulator-controls">
            <el-button-group>
              <el-button size="small" icon="el-icon-refresh" @click="refreshVnc">刷新</el-button>
              <el-button size="small" icon="el-icon-full-screen" @click="fullscreen">全屏</el-button>
            </el-button-group>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：日志信息 -->
      <el-col :span="14" class="log-panel">
        <el-card shadow="never" class="log-card">
          <div slot="header" class="card-header">
            <span><i class="el-icon-document"></i> 分析日志</span>
            <div>
              <el-button
                size="mini"
                type="success"
                icon="el-icon-download"
                @click="downloadFridaReport"
                :disabled="!taskInfo.taskId"
              >
                下载Frida报告
              </el-button>
              <el-button
                size="mini"
                icon="el-icon-delete"
                @click="clearLogs"
              >
                清空
              </el-button>
            </div>
          </div>

          <!-- 连接状态 -->
          <div class="connection-status">
            <el-tag v-if="logConnected" type="success" size="small">
              <i class="el-icon-connection"></i> 日志流已连接
            </el-tag>
            <el-tag v-else type="info" size="small">
              <i class="el-icon-loading"></i> 等待连接...
            </el-tag>
          </div>

          <!-- 日志内容 -->
          <div class="log-content" ref="logContent">
            <div
              v-for="(log, index) in logs"
              :key="index"
              class="log-item"
              :class="getLogClass(log)"
            >
              <span class="log-time">{{ log.time }}</span>
              <span class="log-text">{{ log.text }}</span>
            </div>
            <div v-if="logs.length === 0" class="log-empty">
              <i class="el-icon-document"></i>
              <p>暂无日志信息</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

  </div>
</template>

<script>
import request from '@/utils/request'

export default {
  name: 'DynamicAnalysis',
  data() {
    return {
      // 任务信息
      taskInfo: {
        taskId: '',
        taskName: '',
        apkPath: '',
        createTime: ''
      },
      // 分析状态（整合后只需要这些）
      analysisStarted: false,
      stopping: false,
      // VNC相关
      vncUrl: '',
      vncConnected: false,
      // 日志相关
      logs: [],
      logConnected: false,
      eventSource: null,
      scrollThrottled: false, // 滚动节流标志
      // Frida相关（整合后简化）
      fridaStarted: false,
      fridaStarting: false,
      fridaEventSource: null
    }
  },
  created() {
    // 从路由参数中获取任务信息
    this.loadTaskInfo()
  },
  beforeDestroy() {
    // 关闭SSE连接
    this.closeLogStream()
    this.closeFridaLogStream()
  },
  methods: {
    // 加载任务信息
    loadTaskInfo() {
      const { taskId, apkPath, taskName } = this.$route.query

      if (!apkPath) {
        console.log('未接收到任务信息')
        return
      }

      this.taskInfo = {
        taskId: taskId || Date.now().toString(),
        taskName: taskName || '未命名任务',
        apkPath: apkPath,
        createTime: this.formatDateTime(new Date())
      }

      console.log('接收到任务信息:', this.taskInfo)
    },

    // ==================== 整合后的核心方法 ====================

    // 建立SSE日志流连接
    connectLogStream() {
      if (this.eventSource) {
        this.eventSource.close()
      }

      const baseURL = process.env.VUE_APP_BASE_API || 'http://localhost:8080/dev-api'
      const url = `${baseURL}/app/dynamic/logs?taskId=${this.taskInfo.taskId}`

      this.addLog('正在连接日志流...')

      this.eventSource = new EventSource(url)

      this.eventSource.addEventListener('connected', (e) => {
        this.logConnected = true
        this.addLog('✅ 日志流已连接')
      })

      this.eventSource.addEventListener('log', (e) => {
        this.addLog(e.data)
      })

      this.eventSource.addEventListener('completed', (e) => {
        this.addLog('✅ 分析完成')
        this.logConnected = false
        this.eventSource.close()
      })

      this.eventSource.onerror = (error) => {
        console.error('SSE错误:', error)
        this.logConnected = false
        if (this.eventSource) {
          this.eventSource.close()
        }
      }
    },

    // 关闭日志流
    closeLogStream() {
      if (this.eventSource) {
        this.eventSource.close()
        this.eventSource = null
        this.logConnected = false
      }
    },

    // 添加日志（优化版本）
    addLog(text) {
      // 防止空日志
      if (!text || text.trim() === '') {
        return
      }

      const log = {
        time: this.formatTime(),
        text: text
      }
      this.logs.push(log)

      // 更严格的日志数量限制，防止内存溢出
      const MAX_LOGS = 300
      if (this.logs.length > MAX_LOGS) {
        // 删除前面的日志，保留最新的
        this.logs.splice(0, this.logs.length - MAX_LOGS)
      }

      // 节流自动滚动，避免频繁DOM操作
      if (!this.scrollThrottled) {
        this.scrollThrottled = true
        this.$nextTick(() => {
          const logContent = this.$refs.logContent
          if (logContent) {
            logContent.scrollTop = logContent.scrollHeight
          }
          // 200ms后重置节流标志
          setTimeout(() => {
            this.scrollThrottled = false
          }, 200)
        })
      }
    },

    // 清空日志
    clearLogs() {
      this.logs = []
      this.$message.success('日志已清空')
    },

    // 获取日志样式类
    getLogClass(log) {
      if (log.text.includes('✅') || log.text.includes('成功')) {
        return 'log-success'
      } else if (log.text.includes('❌') || log.text.includes('失败') || log.text.includes('ERROR')) {
        return 'log-error'
      } else if (log.text.includes('WARN') || log.text.includes('警告')) {
        return 'log-warn'
      } else if (log.text.includes('INFO') || log.text.includes('步骤')) {
        return 'log-info'
      }
      return ''
    },

    // VNC加载完成
    handleVncLoad() {
      this.vncConnected = true
      this.addLog('✅ VNC连接成功')
      this.addLog('📱 Android模拟器已就绪，可以开始操作应用')
      this.$message.success('模拟器连接成功')
    },

    // 刷新VNC
    refreshVnc() {
      if (this.$refs.vncIframe) {
        this.$refs.vncIframe.src = this.vncUrl
        this.addLog('刷新VNC连接')
        this.$message.info('刷新中...')
      }
    },

    // 全屏
    fullscreen() {
      if (this.$refs.vncIframe) {
        const iframe = this.$refs.vncIframe
        if (iframe.requestFullscreen) {
          iframe.requestFullscreen()
        } else if (iframe.webkitRequestFullscreen) {
          iframe.webkitRequestFullscreen()
        } else if (iframe.mozRequestFullScreen) {
          iframe.mozRequestFullScreen()
        }
      }
    },

    // 刷新页面
    refreshPage() {
      this.$router.go(0)
    },

    // 跳转到新建任务页面
    goToNewTask() {
      this.$router.push('/app/task/new')
    },

    // 格式化日期时间
    formatDateTime(date) {
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      const hours = String(date.getHours()).padStart(2, '0')
      const minutes = String(date.getMinutes()).padStart(2, '0')
      const seconds = String(date.getSeconds()).padStart(2, '0')
      return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
    },

    // 格式化时间
    formatTime() {
      const now = new Date()
      const hours = String(now.getHours()).padStart(2, '0')
      const minutes = String(now.getMinutes()).padStart(2, '0')
      const seconds = String(now.getSeconds()).padStart(2, '0')
      return `${hours}:${minutes}:${seconds}`
    },

    // ==================== Frida相关方法 ====================

    // 开始完整的Frida检测流程（整合了原来的开始分析功能）
    openFridaDialog() {
      this.$confirm(
        '即将开始完整的Frida动态检测，包括：\n\n' +
        '1. 启动Android模拟器容器\n' +
        '2. 安装APK到模拟器\n' +
        '3. 配置Frida Server\n' +
        '4. 启动Frida Hook监控\n' +
        '5. 生成检测报告\n\n' +
        '检测期间请手动操作应用以触发更多行为！\n' +
        '建议操作：登录、拍照、定位、通讯录、拨号等',
        '开始Frida检测',
        {
          confirmButtonText: '开始检测',
          cancelButtonText: '取消',
          type: 'info',
          dangerouslyUseHTMLString: true
        }
      ).then(() => {
        this.performIntegratedFridaAnalysis()
      }).catch(() => {
        this.$message.info('已取消检测')
      })
    },


    // 执行整合的Frida检测（包含完整的分析流程）
    async performIntegratedFridaAnalysis() {
      try {
        this.fridaStarting = true
        this.fridaStarted = true
        this.addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
        this.addLog('🚀 开始完整的Frida动态检测流程...')
        this.addLog('📋 流程包括：容器启动 → APK安装 → Frida配置 → Hook监控')
        this.addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')

        // 生成新的taskId，确保每次检测都有唯一标识
        const newTaskId = Date.now().toString()
        this.taskInfo.taskId = newTaskId
        this.addLog(`🆔 生成新的任务ID: ${newTaskId}`)

        // 建立日志流连接（使用新的taskId）
        this.connectFridaLogStream()

        // 调用后端的完整分析API（原来的startAnalysis功能）
        const response = await request({
          url: '/app/dynamic/start',
          method: 'post',
          data: {
            taskId: newTaskId,
            apkPath: this.taskInfo.apkPath
          }
        })

        if (response.code === 200) {
          this.addLog('✅ 完整检测流程已启动')
          this.addLog('⏱️  预计检测时长：5分钟')
          this.addLog('💡 检测期间请手动操作应用以触发更多行为')
          this.addLog('🎯 建议操作：登录、拍照、定位、通讯录、拨号等')
          this.addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')

          // 设置VNC连接信息，显示模拟器界面
          this.analysisStarted = true
          this.vncUrl = 'http://192.168.216.146:6080/vnc_lite.html'
          this.addLog('🖥️  正在启动VNC模拟器界面...')
          this.addLog('🔗 VNC地址: ' + this.vncUrl)

          // 延迟设置VNC连接状态，等待容器完全启动
          setTimeout(() => {
            this.addLog('⏳ 等待模拟器启动完成...')
            this.addLog('📱 请在左侧模拟器中手动操作应用')
          }, 3000)

          this.$message.success('Frida检测已启动')
        } else {
          throw new Error(response.msg || '启动失败')
        }
      } catch (error) {
        console.error('启动Frida检测失败:', error)
        this.addLog(`❌ 启动失败: ${error.message}`)
        this.$message.error('启动Frida检测失败: ' + error.message)
        this.fridaStarted = false
      } finally {
        this.fridaStarting = false
      }
    },


    // 停止Frida检测
    async stopFridaAnalysis() {
      try {
        this.stopping = true
        this.addLog('正在停止Frida检测...')

        const response = await request({
          url: '/app/dynamic/stop',
          method: 'post',
          data: {
            taskId: this.taskInfo.taskId
          }
        })

        if (response.code === 200) {
          this.addLog('✅ Frida检测已停止')
          this.$message.success('Frida检测已停止')
          this.fridaStarted = false
          this.analysisStarted = false
          this.vncConnected = false
          this.closeFridaLogStream()

          // 停止后提示下载报告
          setTimeout(() => {
            this.$confirm('检测已停止！是否立即下载报告查看检测结果？', '下载报告', {
              confirmButtonText: '下载报告',
              cancelButtonText: '稍后下载',
              type: 'info'
            }).then(() => {
              this.downloadFridaReport(true) // 跳过确认对话框
            }).catch(() => {
              this.$message.info('可随时通过"下载Frida报告"按钮获取报告')
            })
          }, 1000)
        } else {
          this.addLog('❌ 停止失败: ' + response.msg)
          this.$message.error(response.msg || '停止失败')
        }
      } catch (error) {
        console.error('停止Frida检测失败:', error)
        this.addLog('❌ 停止失败: ' + error.message)
        this.$message.error('停止失败: ' + error.message)
      } finally {
        this.stopping = false
      }
    },

    // 建立Frida SSE日志流连接
    connectFridaLogStream() {
      if (this.fridaEventSource) {
        this.fridaEventSource.close()
      }

      const baseURL = process.env.VUE_APP_BASE_API || 'http://localhost:8080/dev-api'
      const url = `${baseURL}/app/dynamic/logs?taskId=${this.taskInfo.taskId}`

      this.addLog('正在连接日志流...')

      this.fridaEventSource = new EventSource(url)

      this.fridaEventSource.addEventListener('connected', (e) => {
        this.addLog('✅ 日志流已连接')
      })

      this.fridaEventSource.addEventListener('log', (e) => {
        try {
          let message = e.data
          let level = 'info'

          // 尝试解析JSON格式（兼容性处理）
          try {
            const logData = JSON.parse(e.data)
            message = logData.message || e.data
            level = logData.level || 'info'
          } catch (jsonError) {
            // 如果不是JSON格式，直接使用原始字符串
            message = e.data

            // 根据消息内容推断日志级别
            if (message.includes('❌') || message.includes('ERROR') || message.includes('失败')) {
              level = 'error'
            } else if (message.includes('⚠️') || message.includes('WARN') || message.includes('警告')) {
              level = 'warn'
            } else if (message.includes('✅') || message.includes('SUCCESS') || message.includes('成功') || message.includes('完成')) {
              level = 'success'
            } else if (message.includes('🔒') || message.includes('APP行为') || message.includes('隐私')) {
              level = 'alert'
            }
          }

          // 过滤过长的日志，防止页面卡顿
          if (message.length > 1000) {
            this.addLog(`📝 [日志过长已截断] ${message.substring(0, 200)}...`)
            return
          }

          // 直接添加日志（消息中已包含样式标识）
          this.addLog(message)
        } catch (error) {
          console.warn('处理日志失败:', error)
          // 如果处理失败，直接使用原始数据（但要限制长度）
          const rawData = e.data.length > 500 ? e.data.substring(0, 500) + '...' : e.data
          this.addLog(rawData)
        }
      })

      this.fridaEventSource.addEventListener('completed', (e) => {
        this.addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
        this.addLog('✅ Frida检测完成')
        this.addLog('📊 可通过报告功能查看完整检测结果')
        this.addLog('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
        this.fridaStarted = false
        this.fridaEventSource.close()

        // 显示检测完成提示
        this.$confirm('Frida检测已完成！如果报告为空，可能是因为：\n\n1. 应用未触发隐私API调用\n2. 检测期间未手动操作应用\n3. 应用使用了反Hook技术\n\n是否立即下载报告？', '检测完成', {
          confirmButtonText: '下载报告',
          cancelButtonText: '稍后下载',
          type: 'success',
          dangerouslyUseHTMLString: true
        }).then(() => {
          this.downloadFridaReport(true) // 跳过确认对话框
        }).catch(() => {
          this.$message.info('可随时通过"下载Frida报告"按钮获取报告')
        })
      })

      this.fridaEventSource.onerror = (error) => {
        console.error('Frida SSE错误:', error)
        if (this.fridaEventSource) {
          this.fridaEventSource.close()
        }
      }
    },

    // 关闭Frida日志流
    closeFridaLogStream() {
      if (this.fridaEventSource) {
        this.fridaEventSource.close()
        this.fridaEventSource = null
      }
    },

    // 下载Frida报告
    downloadFridaReport(skipConfirm = false) {
      if (!this.taskInfo.taskId) {
        this.$message.warning('任务ID不存在')
        return
      }

      const doDownload = () => {
        this.addLog('📥 正在下载Frida检测报告...')

        // 构建下载URL，添加时间戳防止缓存
        const timestamp = new Date().getTime()
        const downloadUrl = `${process.env.VUE_APP_BASE_API || 'http://localhost:8080/dev-api'}/app/dynamic/frida/report/download?taskId=${this.taskInfo.taskId}&t=${timestamp}`

        // 使用fetch检查文件是否存在
        fetch(downloadUrl, { method: 'HEAD' })
          .then(response => {
            if (response.ok) {
              // 文件存在，开始下载
              const link = document.createElement('a')
              link.href = downloadUrl
              const downloadTime = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
              link.setAttribute('download', `frida_report_${this.taskInfo.taskId}_${downloadTime}.xls`)
              document.body.appendChild(link)
              link.click()
              document.body.removeChild(link)

              this.$message.success('开始下载报告')
              this.addLog('✅ 报告下载已开始')
            } else if (response.status === 404) {
              this.addLog('❌ 报告文件不存在')
              this.$message.error('报告文件不存在，请确保Frida检测已完成')

              // 提供生成空报告的选项
              this.$confirm('报告文件不存在，是否生成空报告？', '文件不存在', {
                confirmButtonText: '生成空报告',
                cancelButtonText: '取消',
                type: 'warning'
              }).then(() => {
                this.generateEmptyReport()
              }).catch(() => {
                this.addLog('用户取消生成空报告')
              })
            } else {
              this.addLog(`❌ 下载失败: HTTP ${response.status}`)
              this.$message.error(`下载失败: HTTP ${response.status}`)
            }
          })
          .catch(error => {
            console.error('下载检查失败:', error)
            this.addLog('❌ 下载检查失败: ' + error.message)
            this.$message.error('下载检查失败，请稍后重试')
          })
      }

      if (skipConfirm) {
        doDownload()
      } else {
        this.$confirm('确认下载Frida检测报告？', '下载报告', {
          confirmButtonText: '下载',
          cancelButtonText: '取消',
          type: 'info'
        }).then(() => {
          doDownload()
        }).catch(() => {
          this.$message.info('已取消下载')
        })
      }
    },

    // 生成空报告
    generateEmptyReport() {
      this.addLog('正在尝试生成空报告...')

      // 直接尝试下载，后端会自动生成空报告
      const downloadUrl = `${process.env.VUE_APP_BASE_API || 'http://localhost:8080/dev-api'}/app/dynamic/frida/report/download?taskId=${this.taskInfo.taskId}&force=true`

      const link = document.createElement('a')
      link.href = downloadUrl
      link.setAttribute('download', `frida_report_${this.taskInfo.taskId}_empty.xls`)
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)

      this.$message.info('正在生成空报告，请稍候...')
      this.addLog('📄 已请求生成空报告')
    }
  }
}
</script>

<style lang="scss" scoped>
.dynamic-analysis-container {
  padding: 0;

  // 顶部头部卡片
  .header-card {
    margin-bottom: 20px;
    border-radius: 8px;

    .header-content {
      display: flex;
      align-items: center;
      justify-content: space-between;

      .task-info-brief {
        flex: 1;

        h3 {
          margin: 0 0 10px 0;
          font-size: 20px;
          font-weight: 600;
          color: #303133;

          i {
            margin-right: 8px;
            color: #409EFF;
          }
        }

        .task-details {
          display: flex;
          align-items: center;
          gap: 12px;
          font-size: 14px;

          .task-name {
            font-weight: 500;
            color: #606266;
          }

          .apk-path {
            font-family: 'Courier New', Courier, monospace;
            font-size: 12px;
            color: #909399;
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }
        }
      }

      .action-buttons {
        display: flex;
        gap: 10px;
        align-items: center;
      }
    }
  }

  // 主要内容区域
  .main-content {
    height: calc(100vh - 240px);
    min-height: 600px;

    // 模拟器面板
    .simulator-panel {
      height: 100%;

      .simulator-card {
        height: 100%;
        border-radius: 8px;

        ::v-deep .el-card__header {
          padding: 15px 20px;
          background: #fafafa;
          border-bottom: 1px solid #e4e7ed;

          .card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-weight: 500;

            i {
              margin-right: 6px;
              color: #409EFF;
            }
          }
        }

        ::v-deep .el-card__body {
          padding: 0;
          height: calc(100% - 52px);
          display: flex;
          flex-direction: column;
        }

        .simulator-wrapper {
          flex: 1;
          position: relative;
          background: #000;
          display: flex;
          justify-content: center;
          align-items: center;

          .vnc-container {
            width: 450px;
            height: 100%;
            position: relative;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            border-radius: 8px;

            .vnc-iframe {
              height: 100%;
              width: 450px;
              border: none;
              display: block;
              outline: none;
            }
          }

          .vnc-placeholder {
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: #909399;

            i {
              font-size: 80px;
              margin-bottom: 20px;
              opacity: 0.3;
            }

            p {
              font-size: 16px;
            }
          }
        }

        .simulator-controls {
          padding: 15px 20px;
          background: #fafafa;
          border-top: 1px solid #e4e7ed;
          text-align: center;
        }
      }
    }

    // 日志面板
    .log-panel {
      height: 100%;

      .log-card {
        height: 100%;
        border-radius: 8px;

        ::v-deep .el-card__header {
          padding: 15px 20px;
          background: #fafafa;
          border-bottom: 1px solid #e4e7ed;

          .card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-weight: 500;

            i {
              margin-right: 6px;
              color: #67C23A;
            }
          }
        }

        ::v-deep .el-card__body {
          padding: 15px;
          height: calc(100% - 52px);
          display: flex;
          flex-direction: column;
        }

        .connection-status {
          margin-bottom: 15px;
          text-align: center;
        }

        .log-content {
          flex: 1;
          overflow-y: auto;
          background: #1e1e1e;
          border-radius: 4px;
          padding: 15px;
          font-family: 'Courier New', Courier, monospace;
          font-size: 13px;
          line-height: 1.8;

          .log-item {
            padding: 3px 0;
            color: #d4d4d4;

            .log-time {
              color: #858585;
              margin-right: 10px;
            }

            .log-text {
              color: #d4d4d4;
            }

            &.log-success {
              .log-text {
                color: #4ec9b0;
              }
            }

            &.log-error {
              .log-text {
                color: #f48771;
              }
            }

            &.log-warn {
              .log-text {
                color: #dcdcaa;
              }
            }

            &.log-info {
              .log-text {
                color: #569cd6;
              }
            }
          }

          .log-empty {
            height: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: #606266;
            opacity: 0.5;

            i {
              font-size: 60px;
              margin-bottom: 15px;
            }

            p {
              font-size: 14px;
              font-family: Arial, sans-serif;
            }
          }

          &::-webkit-scrollbar {
            width: 8px;
          }

          &::-webkit-scrollbar-track {
            background: #2d2d2d;
          }

          &::-webkit-scrollbar-thumb {
            background: #555;
            border-radius: 4px;

            &:hover {
              background: #666;
            }
          }
        }
      }
    }
  }
}

// Frida对话框样式
.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
  line-height: 1.5;
}

// 响应式调整
@media screen and (max-width: 1366px) {
  .dynamic-analysis-container {
    .main-content {
      min-height: 500px;
    }
  }
}
</style>
