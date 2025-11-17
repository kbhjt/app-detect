<template>
  <div class="app-container simulator-container">
    <el-row :gutter="20" class="simulator-row">
      <!-- 左侧：Android模拟器显示区域 -->
      <el-col :span="14" class="simulator-panel">
        <div class="device-frame">
          <div class="device-header">
            <span class="device-info">当前手机编号：HTC61a20841</span>
          </div>
          <div class="device-screen">
            <iframe
              ref="simulatorFrame"
              :src="vncUrl"
              frameborder="0"
              class="vnc-iframe"
              @load="handleIframeLoad"
            ></iframe>
          </div>
          <div class="device-controls">
            <el-button-group>
              <el-button size="small" icon="el-icon-back" @click="handleBack">返回</el-button>
              <el-button size="small" icon="el-icon-s-home" @click="handleHome">主页</el-button>
              <el-button size="small" icon="el-icon-menu" @click="handleMenu">菜单</el-button>
              <el-button size="small" icon="el-icon-refresh" @click="handleRefresh">刷新</el-button>
              <el-button size="small" icon="el-icon-picture" @click="handleScreenshot">截图</el-button>
            </el-button-group>
          </div>
        </div>
      </el-col>

      <!-- 右侧：控制面板 -->
      <el-col :span="10" class="control-panel">
        <el-card shadow="never" class="control-card">
          <!-- 操作按钮区域 -->
          <div class="button-group">
            <el-button type="primary" size="medium" @click="handleAll">全部</el-button>
            <el-button type="primary" size="medium" @click="handleSwitchPage">切换页面</el-button>
            <el-button type="primary" size="medium" @click="handleClearLocation">清空定位包</el-button>
          </div>

          <!-- 实时消息区域 -->
          <div class="message-section">
            <div class="section-header">
              <i class="el-icon-chat-dot-round"></i>
              <span>实时消息</span>
            </div>
            <div class="message-content">
              <div class="message-item">{{ currentStatus }}</div>
              <div class="message-item success">{{ successMessage }}</div>
              <div class="message-item info">{{ operationMessage }}</div>
            </div>
          </div>

          <!-- 日志输出区域 -->
          <div class="log-section">
            <div class="section-header">
              <i class="el-icon-document"></i>
              <span>日志输出</span>
            </div>
            <div class="log-content">
              <div v-for="(log, index) in logs" :key="index" class="log-item">
                <span class="log-time">{{ log.time }}</span>
                <span class="log-text">{{ log.text }}</span>
              </div>
            </div>
          </div>

          <!-- 连接状态 -->
          <div class="status-section">
            <el-tag :type="connectionStatus === 'connected' ? 'success' : 'danger'" size="medium">
              {{ connectionStatus === 'connected' ? '已连接' : '未连接' }}
            </el-tag>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
export default {
  name: 'SimulatorTest',
  data() {
    return {
      // VNC连接地址
      vncUrl: 'http://192.168.216.146:6080/vnc_lite.html',
      // 连接状态
      connectionStatus: 'disconnected',
      // 当前状态消息
      currentStatus: '直名连接客户端...',
      successMessage: '欢迎试用！',
      operationMessage: '正在等待操作指令...',
      // 日志列表
      logs: []
    }
  },
  created() {
    this.initLog()
  },
  mounted() {
    this.addLog('系统初始化完成')
    this.addLog('正在连接Android模拟器...')
  },
  beforeDestroy() {
    // 清理资源
    this.logs = []
  },
  methods: {
    // 初始化日志
    initLog() {
      this.logs = [
        { time: this.getCurrentTime(), text: '系统启动' }
      ]
    },

    // 添加日志
    addLog(text) {
      this.logs.push({
        time: this.getCurrentTime(),
        text: text
      })
      // 限制日志数量，避免过多
      if (this.logs.length > 100) {
        this.logs.shift()
      }
      // 自动滚动到底部
      this.$nextTick(() => {
        const logContent = document.querySelector('.log-content')
        if (logContent) {
          logContent.scrollTop = logContent.scrollHeight
        }
      })
    },

    // 获取当前时间
    getCurrentTime() {
      const now = new Date()
      const hours = String(now.getHours()).padStart(2, '0')
      const minutes = String(now.getMinutes()).padStart(2, '0')
      const seconds = String(now.getSeconds()).padStart(2, '0')
      return `${hours}:${minutes}:${seconds}`
    },

    // iframe加载完成
    handleIframeLoad() {
      this.connectionStatus = 'connected'
      this.currentStatus = '已成功连接到模拟器'
      this.addLog('VNC连接成功')
      this.$message.success('模拟器连接成功')
    },

    // 返回按钮
    handleBack() {
      this.addLog('执行返回操作')
      this.$message.info('返回')
    },

    // 主页按钮
    handleHome() {
      this.addLog('执行返回主页操作')
      this.$message.info('返回主页')
    },

    // 菜单按钮
    handleMenu() {
      this.addLog('执行打开菜单操作')
      this.$message.info('打开菜单')
    },

    // 刷新按钮
    handleRefresh() {
      this.addLog('刷新模拟器页面')
      this.$refs.simulatorFrame.src = this.vncUrl
      this.$message.info('刷新中...')
    },

    // 截图按钮
    handleScreenshot() {
      this.addLog('执行截图操作')
      this.$message.info('截图功能开发中')
    },

    // 全部按钮
    handleAll() {
      this.addLog('执行全部操作')
      this.operationMessage = '正在执行全部任务...'
      this.$message.success('开始执行全部任务')
    },

    // 切换页面
    handleSwitchPage() {
      this.addLog('执行切换页面操作')
      this.operationMessage = '正在切换页面...'
      this.$message.info('切换页面')
    },

    // 清空定位包
    handleClearLocation() {
      this.$modal.confirm('确认要清空定位包吗？').then(() => {
        this.addLog('清空定位包')
        this.operationMessage = '定位包已清空'
        this.$message.success('清空成功')
      }).catch(() => {
        this.addLog('取消清空定位包操作')
      })
    }
  }
}
</script>

<style scoped lang="scss">
.simulator-container {
  height: calc(100vh - 120px);
  padding: 20px;
  background-color: #f0f2f5;

  .simulator-row {
    height: 100%;
  }

  .simulator-panel {
    height: 100%;

    .device-frame {
      background: #fff;
      border-radius: 8px;
      box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
      height: 100%;
      display: flex;
      flex-direction: column;

      .device-header {
        padding: 15px 20px;
        border-bottom: 1px solid #e4e7ed;
        background: #fafafa;
        border-radius: 8px 8px 0 0;

        .device-info {
          font-size: 14px;
          color: #606266;
          font-weight: 500;
        }
      }

      .device-screen {
        flex: 1;
        position: relative;
        background: #000;
        overflow: hidden;

        .vnc-iframe {
          width: 100%;
          height: 100%;
          border: none;
        }
      }

      .device-controls {
        padding: 15px 20px;
        border-top: 1px solid #e4e7ed;
        background: #fafafa;
        border-radius: 0 0 8px 8px;
        text-align: center;
      }
    }
  }

  .control-panel {
    height: 100%;

    .control-card {
      height: 100%;
      border-radius: 8px;

      ::v-deep .el-card__body {
        height: 100%;
        display: flex;
        flex-direction: column;
      }

      .button-group {
        margin-bottom: 20px;
        display: flex;
        gap: 10px;
        flex-wrap: wrap;

        .el-button {
          flex: 1;
          min-width: 100px;
        }
      }

      .message-section,
      .log-section {
        margin-bottom: 20px;

        .section-header {
          display: flex;
          align-items: center;
          padding: 10px;
          background: #409eff;
          color: #fff;
          border-radius: 4px;
          margin-bottom: 10px;
          font-weight: 500;

          i {
            margin-right: 8px;
            font-size: 16px;
          }
        }

        .message-content {
          background: #f5f7fa;
          padding: 15px;
          border-radius: 4px;
          min-height: 100px;

          .message-item {
            padding: 5px 0;
            color: #606266;
            line-height: 1.6;

            &.success {
              color: #67c23a;
            }

            &.info {
              color: #909399;
            }
          }
        }

        .log-content {
          background: #f5f7fa;
          padding: 15px;
          border-radius: 4px;
          height: 250px;
          overflow-y: auto;
          font-family: 'Courier New', Courier, monospace;
          font-size: 12px;

          .log-item {
            padding: 3px 0;
            color: #606266;
            line-height: 1.6;

            .log-time {
              color: #909399;
              margin-right: 10px;
            }

            .log-text {
              color: #303133;
            }
          }

          &::-webkit-scrollbar {
            width: 6px;
          }

          &::-webkit-scrollbar-thumb {
            background: #dcdfe6;
            border-radius: 3px;
          }

          &::-webkit-scrollbar-track {
            background: #f5f7fa;
          }
        }
      }

      .status-section {
        margin-top: auto;
        text-align: center;
        padding-top: 15px;
        border-top: 1px solid #e4e7ed;
      }
    }
  }
}

// 响应式调整
@media screen and (max-width: 1366px) {
  .simulator-container {
    .simulator-panel .device-frame .device-screen {
      min-height: 500px;
    }
  }
}
</style>

