<template>
  <div class="app-container task-detail-container">
    <!-- 顶部应用信息栏 -->
    <div class="app-header">
      <div class="app-info-section">
        <img :src="appInfo.icon" class="app-logo" />
        <span class="app-name">{{ appInfo.name }}</span>
      </div>
      <div class="header-actions">
        <el-button type="primary" size="small" @click="handleUploadNewVersion">
          上传新版本
        </el-button>
        <el-button type="danger" size="small" @click="handleStopTask">
          停止任务
        </el-button>
        <el-dropdown trigger="click" @command="handleMoreAction">
          <span class="el-dropdown-link">
            <i class="el-icon-more"></i>
          </span>
          <el-dropdown-menu slot="dropdown">
            <el-dropdown-item command="export">导出报告</el-dropdown-item>
            <el-dropdown-item command="share">分享链接</el-dropdown-item>
            <el-dropdown-item command="delete" divided>删除任务</el-dropdown-item>
          </el-dropdown-menu>
        </el-dropdown>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="content-wrapper">
      <!-- 左侧：动态数据采集 -->
      <div class="left-panel">
        <el-card class="panel-card">
          <div slot="header" class="card-header">
            <i class="el-icon-cpu"></i>
            <span>动态数据采集</span>
          </div>
          <div class="collect-options">
            <el-button 
              :type="collectMode === 'auto' ? 'primary' : 'default'"
              :plain="collectMode !== 'auto'"
              size="small"
              @click="collectMode = 'auto'"
            >
              自动采集
            </el-button>
            <el-button 
              :type="collectMode === 'manual' ? 'danger' : 'default'"
              :plain="collectMode !== 'manual'"
              size="small"
              @click="collectMode = 'manual'"
            >
              人工采集
            </el-button>
          </div>
          <div class="collect-status">
            <el-tag :type="collectMode === 'auto' ? 'success' : 'warning'" size="small">
              {{ collectMode === 'auto' ? '最高优先级(自选项)' : '人工采集中' }}
            </el-tag>
          </div>

          <!-- 手机截图预览区域 -->
          <div class="phone-preview">
            <div class="preview-placeholder">
              <i class="el-icon-mobile-phone"></i>
              <p>手机截图已不可展</p>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 中间：应用合规分析 -->
      <div class="middle-panel">
        <el-card class="panel-card">
          <div slot="header" class="card-header">
            <i class="el-icon-data-analysis"></i>
            <span>应用合规分析</span>
          </div>

          <!-- 分析标签页 -->
          <el-tabs v-model="activeTab" class="analysis-tabs">
            <el-tab-pane label="基本信息" name="basic"></el-tab-pane>
            <el-tab-pane label="SDK信息" name="sdk"></el-tab-pane>
            <el-tab-pane label="权限分析" name="permission"></el-tab-pane>
            <el-tab-pane label="行为分析" name="behavior"></el-tab-pane>
          </el-tabs>

          <!-- 存在线索 -->
          <div class="clue-section">
            <div class="clue-header">
              <i class="el-icon-warning"></i>
              <span>存在线索：</span>
              <el-tag type="warning" size="small">信息</el-tag>
            </div>
            <div class="clue-tip">
              当前手机信号：暂无
            </div>
          </div>

          <!-- 获取权限详情 -->
          <div class="permission-detail">
            <div class="permission-header">
              <span class="header-title">获取权限</span>
            </div>
            <div class="permission-content">
              <div class="permission-item">
                <p class="permission-title">正在连接云端服务...</p>
                <p class="permission-desc">需第3方连接！</p>
                <p class="permission-extra">正在等待检测结果...</p>
              </div>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 右侧：应用合规评估 + 行为列表 -->
      <div class="right-panel">
        <!-- 应用合规评估 -->
        <el-card class="panel-card assessment-card">
          <div slot="header" class="card-header">
            <i class="el-icon-s-data"></i>
            <span>应用合规评估</span>
          </div>
          <div class="assessment-content">
            <div class="assessment-item">
              <i class="el-icon-warning-outline"></i>
              <span>工信部抽查合规(2020) 164号检测</span>
            </div>
          </div>
        </el-card>

        <!-- 行为列表 -->
        <el-card class="panel-card behavior-card">
          <div slot="header" class="card-header-tabs">
            <el-radio-group v-model="behaviorTab" size="small">
              <el-radio-button label="download">下载行为</el-radio-button>
              <el-radio-button label="action">行为内容</el-radio-button>
              <el-radio-button label="other">其他日期</el-radio-button>
              <el-radio-button label="screenshot">截屏日期</el-radio-button>
              <el-radio-button label="log">检查日期</el-radio-button>
            </el-radio-group>
          </div>

          <!-- 行为数据表格 -->
          <el-table
            :data="behaviorList"
            height="500"
            size="small"
            :header-cell-style="{background: '#f5f7fa', color: '#606266'}"
          >
            <el-table-column label="时间" width="180">
              <template slot-scope="scope">
                <div class="time-cell">
                  <div>{{ scope.row.date }}</div>
                  <div class="time-detail">{{ scope.row.time }}</div>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="行为" prop="action" width="120" />
            <el-table-column label="个人信息" width="80">
              <template slot-scope="scope">
                <el-tag type="info" size="mini">{{ scope.row.personalInfo }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="检测状态">
              <template slot-scope="scope">
                <div class="status-cell">
                  <span>{{ scope.row.status }}</span>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TaskDetail',
  data() {
    return {
      // 应用信息
      appInfo: {
        name: '小方出行',
        icon: 'https://via.placeholder.com/50/FF8C00/FFFFFF?text=小方',
        version: '6.4.1'
      },
      // 采集模式
      collectMode: 'auto',
      // 活动标签页
      activeTab: 'permission',
      // 行为标签页
      behaviorTab: 'download',
      // 行为列表数据
      behaviorList: [
        {
          date: '2025-04-22 11:0',
          time: '9:58.322',
          action: '停止收听',
          personalInfo: '否',
          status: '隐私政策问题自检列表'
        },
        {
          date: '2025-04-22 11:0',
          time: '9:57.161',
          action: '注册流盘广播',
          personalInfo: '否',
          status: '隐私政策问题自检列表'
        },
        {
          date: '2025-04-22 11:0',
          time: '9:56.884',
          action: '注册流盘广播',
          personalInfo: '否',
          status: '隐私政策问题自检列表'
        },
        {
          date: '2025-04-22 11:0',
          time: '9:56.270',
          action: '注册流盘广播',
          personalInfo: '否',
          status: '隐私政策问题自检列表'
        },
        {
          date: '2025-04-22 11:0',
          time: '9:56.004',
          action: '注册流盘广播',
          personalInfo: '否',
          status: '隐私政策问题自检列表'
        },
        {
          date: '2025-04-22 11:0',
          time: '9:54.522',
          action: '注册流盘广播',
          personalInfo: '否',
          status: '隐私政策问题自检列表'
        },
        {
          date: '2025-04-22 11:0',
          time: '9:53.511',
          action: '注册流盘广播',
          personalInfo: '否',
          status: '隐私政策问题自检列表'
        }
      ]
    }
  },
  created() {
    this.loadTaskDetail()
  },
  methods: {
    // 加载任务详情
    loadTaskDetail() {
      // TODO: 从API获取任务详情数据
      const taskId = this.$route.params.id
      console.log('加载任务详情:', taskId)
    },

    // 上传新版本
    handleUploadNewVersion() {
      this.$message.info('跳转到上传新版本页面...')
      // this.$router.push('/app/task/upload')
    },

    // 停止任务
    handleStopTask() {
      this.$confirm('确认停止该检测任务吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        this.$message.success('任务已停止')
        // TODO: 调用停止任务API
      }).catch(() => {})
    },

    // 更多操作
    handleMoreAction(command) {
      switch (command) {
        case 'export':
          this.$message.success('开始导出报告...')
          break
        case 'share':
          this.$message.success('分享链接已复制到剪贴板')
          break
        case 'delete':
          this.$confirm('确认删除该任务吗？删除后无法恢复。', '警告', {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }).then(() => {
            this.$message.success('删除成功')
            this.$router.push('/app/task/my-task')
          }).catch(() => {})
          break
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.task-detail-container {
  background: #f0f2f5;
  min-height: calc(100vh - 84px);

  // 顶部应用信息栏
  .app-header {
    background: #fff;
    padding: 15px 20px;
    margin-bottom: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);

    .app-info-section {
      display: flex;
      align-items: center;
      gap: 15px;

      .app-logo {
        width: 50px;
        height: 50px;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      }

      .app-name {
        font-size: 20px;
        font-weight: bold;
        color: #303133;
      }
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: 10px;

      .el-dropdown-link {
        cursor: pointer;
        font-size: 20px;
        color: #606266;
        padding: 0 10px;

        &:hover {
          color: #409EFF;
        }
      }
    }
  }

  // 主要内容区域
  .content-wrapper {
    display: flex;
    gap: 20px;
    align-items: flex-start;

    // 左侧面板
    .left-panel {
      width: 280px;
      flex-shrink: 0;
    }

    // 中间面板
    .middle-panel {
      flex: 1;
      min-width: 0;
    }

    // 右侧面板
    .right-panel {
      width: 400px;
      flex-shrink: 0;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }
  }

  // 卡片样式
  .panel-card {
    margin-bottom: 0;

    .card-header {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: bold;
      font-size: 15px;

      i {
        color: #409EFF;
        font-size: 16px;
      }
    }

    .card-header-tabs {
      ::v-deep .el-radio-group {
        display: flex;
        flex-wrap: wrap;
        gap: 5px;

        .el-radio-button__inner {
          padding: 8px 12px;
          font-size: 12px;
        }
      }
    }
  }

  // 采集选项
  .collect-options {
    display: flex;
    gap: 10px;
    margin-bottom: 15px;

    .el-button {
      flex: 1;
    }
  }

  .collect-status {
    margin-bottom: 20px;
  }

  // 手机预览区域
  .phone-preview {
    .preview-placeholder {
      background: #f5f7fa;
      border: 2px dashed #dcdfe6;
      border-radius: 8px;
      padding: 60px 20px;
      text-align: center;
      color: #909399;

      i {
        font-size: 48px;
        margin-bottom: 10px;
      }

      p {
        margin: 0;
        font-size: 14px;
      }
    }
  }

  // 分析标签页
  .analysis-tabs {
    margin-bottom: 20px;

    ::v-deep .el-tabs__header {
      margin-bottom: 20px;
    }
  }

  // 线索区域
  .clue-section {
    background: #fff9e6;
    border-left: 4px solid #E6A23C;
    padding: 15px;
    margin-bottom: 20px;

    .clue-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 10px;

      i {
        color: #E6A23C;
        font-size: 18px;
      }

      span {
        font-weight: bold;
        color: #303133;
      }
    }

    .clue-tip {
      color: #606266;
      font-size: 14px;
    }
  }

  // 权限详情
  .permission-detail {
    .permission-header {
      background: #409EFF;
      color: #fff;
      padding: 10px 15px;
      border-radius: 4px 4px 0 0;
      font-weight: bold;
    }

    .permission-content {
      background: #ecf5ff;
      padding: 20px;
      border-radius: 0 0 4px 4px;

      .permission-item {
        p {
          margin: 0 0 10px 0;
          color: #303133;
          line-height: 1.6;

          &.permission-title {
            font-weight: bold;
            color: #409EFF;
          }

          &.permission-desc {
            color: #E6A23C;
          }

          &:last-child {
            margin-bottom: 0;
          }
        }
      }
    }
  }

  // 应用合规评估
  .assessment-card {
    .assessment-content {
      .assessment-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 15px;
        background: #fff9e6;
        border-radius: 4px;
        border-left: 4px solid #E6A23C;

        i {
          color: #E6A23C;
          font-size: 20px;
        }

        span {
          color: #606266;
          font-size: 14px;
        }
      }
    }
  }

  // 行为卡片
  .behavior-card {
    flex: 1;

    ::v-deep .el-card__body {
      padding: 0;
    }

    .el-table {
      .time-cell {
        .time-detail {
          color: #909399;
          font-size: 12px;
          margin-top: 4px;
        }
      }

      .status-cell {
        color: #606266;
        font-size: 13px;
      }
    }
  }
}

// 响应式适配
@media screen and (max-width: 1400px) {
  .task-detail-container {
    .content-wrapper {
      flex-direction: column;

      .left-panel,
      .right-panel {
        width: 100%;
      }
    }
  }
}

@media screen and (max-width: 768px) {
  .task-detail-container {
    .app-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 15px;

      .header-actions {
        width: 100%;
        justify-content: flex-end;
      }
    }
  }
}
</style>

