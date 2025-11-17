<template>
  <div class="app-container task-detail-container">
    <!-- 顶部区域 -->
    <div class="top-section">
      <!-- 第一行：APP名称和操作按钮 -->
      <div class="header-row">
        <div class="app-info">
          <span class="app-label">APP名称</span>
          <el-button size="small" plain>上传隐私政策</el-button>
        </div>
        <div class="header-actions">
          <el-button type="primary" size="small" @click="handleCompare">
            应用对比
          </el-button>
          <el-button type="danger" size="small" @click="handleStopTask">
            终止任务
          </el-button>
        </div>
      </div>

      <!-- 第二行：三个功能区域标题和按钮 -->
      <div class="function-areas">
        <!-- 动态数据采集区 -->
        <div class="function-area">
          <div class="area-title">
            <i class="el-icon-s-data"></i>
            <span>动态数据采集</span>
          </div>
          <div class="area-buttons">
            <el-button
              :type="collectMode === 'auto' ? 'primary' : 'default'"
              size="small"
              @click="handleCollectModeChange('auto')"
            >
              自动采集
            </el-button>
            <el-button
              :type="collectMode === 'manual' ? 'primary' : 'default'"
              size="small"
              @click="handleCollectModeChange('manual')"
            >
              人工采集
            </el-button>
          </div>
          <!-- 任务播报 -->
          <div class="task-broadcast">
            <transition name="slide-up" mode="out-in">
              <div :key="currentTaskIndex" class="broadcast-text">
                {{ taskBroadcasts[currentTaskIndex] }}
              </div>
            </transition>
          </div>
        </div>

        <!-- 应用合规分析区 -->
        <div class="function-area">
          <div class="area-title">
            <i class="el-icon-document"></i>
            <span>应用合规分析</span>
          </div>
          <div class="area-buttons">
            <el-button
              v-for="tab in analysisTabs"
              :key="tab.value"
              :type="activeTab === tab.value ? 'primary' : 'default'"
              size="small"
              @click="handleTabChange(tab.value)"
            >
              {{ tab.label }}
            </el-button>
          </div>
        </div>

        <!-- 应用合规评估区 -->
        <div class="function-area">
          <div class="area-title">
            <i class="el-icon-s-marketing"></i>
            <span>应用合规评估</span>
          </div>
          <div class="assessment-text">
            工信部抽查合规(2020) 164号合规检测
          </div>
        </div>
      </div>
    </div>

    <!-- 橙色提示区域 - 只在自动采集模式下显示 -->
    <div v-if="collectMode === 'auto' && !activeTab" class="warning-banner">
      <span class="warning-label">任务状态：</span>
      <div class="warning-text-wrapper">
        <i class="el-icon-bell"></i>
        <div class="scrolling-text">
          <span class="warning-text">自动采集任务进行中，无法启动手机，请于20-30分钟后，请等待合个子任务完成</span>
        </div>
      </div>
    </div>

    <!-- 底部内容区域 -->
    <div class="content-wrapper">
      <!-- 自动采集模式：显示三列布局 -->
      <template v-if="collectMode === 'auto' && !activeTab">
        <!-- 左侧：手机信息和预览 -->
        <div class="left-column">
          <div class="phone-info-box">
            <div class="info-item">
              <i class="el-icon-mobile-phone" style="color: #409EFF;"></i>
              <span class="info-label">当前手机编号：</span>
              <span class="info-value">HT7C61ACC841</span>
            </div>
          </div>
          <div class="phone-preview">
            <iframe
              src="http://192.168.216.146:6080/vnc_lite.html?scale=true"
              frameborder="0"
              class="vnc-iframe"
            ></iframe>
          </div>
        </div>

        <!-- 中间：实时数据区域 -->
        <div class="middle-column">
          <div class="realtime-box">
            <div class="realtime-header">
              <i class="el-icon-loading"></i>
              <span>实时数据</span>
            </div>
            <div class="realtime-content">
              <p>正在连接服务器...</p>
              <p>服务器已连接！</p>
              <p>正在等待数据传输...</p>
            </div>
          </div>
        </div>

        <!-- 右侧：行为数据表格 -->
        <div class="right-column">
          <div class="behavior-header">
            <el-button
              type="primary"
              size="mini"
            >
              下载行为数据
            </el-button>
            <span class="behavior-label">行为内容</span>
          </div>
          <el-table
            :data="behaviorList"
            height="450"
            size="small"
            :header-cell-style="{background: '#f5f7fa', color: '#606266', fontSize: '13px'}"
            :cell-style="{fontSize: '12px'}"
          >
            <el-table-column label="时间" width="140">
              <template slot-scope="scope">
                <div>{{ scope.row.date }}</div>
                <div style="color: #909399; font-size: 11px;">{{ scope.row.time }}</div>
              </template>
            </el-table-column>
            <el-table-column label="行为" prop="action" width="100" />
            <el-table-column label="个人信息" width="80" align="center">
              <template slot-scope="scope">
                <span>{{ scope.row.personalInfo }}</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </template>

      <!-- 基本信息 -->
      <div v-else-if="activeTab === 'basic'" class="info-panel">
        <div class="info-title">基本信息</div>
        <div class="info-content">
          <div class="info-row">
            <span class="info-label">软件名称</span>
            <span class="info-value">口语轻松学</span>
          </div>
          <div class="info-row">
            <span class="info-label">包名</span>
            <span class="info-value">com.couyuxue</span>
          </div>
          <div class="info-row">
            <span class="info-label">类型</span>
            <span class="info-value">学习</span>
          </div>
          <div class="info-row">
            <span class="info-label">软件大小</span>
            <span class="info-value">130.29MB</span>
          </div>
          <div class="info-row">
            <span class="info-label">软件版本</span>
            <span class="info-value">1.3.4</span>
          </div>
          <div class="info-row">
            <span class="info-label">安装包文件名</span>
            <span class="info-value">com.couyuxue_1.3.4.apk</span>
          </div>
          <div class="info-row">
            <span class="info-label">安装包MD5</span>
            <span class="info-value">c638sd283dcd93bjkkc</span>
          </div>
          <div class="info-row">
            <span class="info-label">安装包SHA-1</span>
            <span class="info-value">c638sd283dcd93bjkkc</span>
          </div>
          <div class="info-row">
            <span class="info-label">安装包SHA-256</span>
            <span class="info-value">c638sd283dcd93bjkkc</span>
          </div>
          <div class="info-row">
            <span class="info-label">签名信息</span>
            <span class="info-value">c638sd283dcd93bjkkc</span>
          </div>
          <div class="info-row">
            <span class="info-label">证书MD5</span>
            <span class="info-value">c638sd283dcd93bjkkc</span>
          </div>
          <div class="info-row">
            <span class="info-label">targetSdkVersion</span>
            <span class="info-value">30</span>
          </div>
        </div>
      </div>

      <!-- SDK信息 -->
      <div v-else-if="activeTab === 'sdk'" class="sdk-panel">
        <div class="sdk-search">
          <el-input
            v-model="sdkSearchText"
            placeholder="请输入搜索内容"
            style="width: 300px;"
          ></el-input>
          <el-button style="margin-left: 10px;">重置</el-button>
          <el-button type="primary" style="margin-left: 10px;">查询</el-button>
        </div>
        <el-table
          :data="sdkList"
          border
          style="width: 100%; margin-top: 20px;"
          :header-cell-style="{background: '#f5f7fa', color: '#606266'}"
        >
          <el-table-column prop="name" label="SDK名称" width="180"></el-table-column>
          <el-table-column prop="packageName" label="包名" width="180"></el-table-column>
          <el-table-column prop="developer" label="开发者" width="150"></el-table-column>
          <el-table-column prop="type" label="类别" width="120"></el-table-column>
          <el-table-column prop="description" label="描述" min-width="200"></el-table-column>
          <el-table-column prop="location" label="地址" width="150"></el-table-column>
        </el-table>
        <el-pagination
          @size-change="handleSdkSizeChange"
          @current-change="handleSdkPageChange"
          :current-page="sdkPagination.currentPage"
          :page-sizes="[10, 20, 50, 100]"
          :page-size="sdkPagination.pageSize"
          layout="total, sizes, prev, pager, next, jumper"
          :total="sdkPagination.total"
          style="margin-top: 20px; text-align: right;"
        >
        </el-pagination>
      </div>

      <!-- 权限分析 -->
      <div v-else-if="activeTab === 'permission'" class="permission-panel">
        <div class="permission-title">声明权限</div>
        <div class="permission-filters">
          <el-select v-model="permissionFilters.name" placeholder="请选择权限名称" size="small" clearable style="width: 200px; margin-right: 10px;">
            <el-option
              v-for="item in permissionNameOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value">
            </el-option>
          </el-select>
          <el-select v-model="permissionFilters.meaning" placeholder="请选择权限含义" size="small" clearable style="width: 200px; margin-right: 10px;">
            <el-option
              v-for="item in permissionMeaningOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value">
            </el-option>
          </el-select>
          <el-select v-model="permissionFilters.protectionLevel" placeholder="请选择保护级别" size="small" clearable style="width: 150px; margin-right: 10px;">
            <el-option
              v-for="item in protectionLevelOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value">
            </el-option>
          </el-select>
          <el-button size="small" @click="resetPermissionFilters">重置</el-button>
          <el-button type="primary" size="small" @click="searchPermissions">查询</el-button>
        </div>
        <el-table
          :data="permissionList"
          border
          style="width: 100%; margin-top: 20px;"
          :header-cell-style="{background: '#f5f7fa', color: '#606266'}"
        >
          <el-table-column prop="index" label="序号" width="80"></el-table-column>
          <el-table-column prop="name" label="权限名称" width="200"></el-table-column>
          <el-table-column prop="meaning" label="权限含义" width="150"></el-table-column>
          <el-table-column prop="type" label="权限类型" width="120"></el-table-column>
          <el-table-column prop="protectionLevel" label="保护级别" width="120"></el-table-column>
          <el-table-column prop="collectPersonalInfo" label="可收集个人信息权限" width="150"></el-table-column>
          <el-table-column prop="isUsed" label="是否使用" width="100"></el-table-column>
          <el-table-column prop="sensitivePermission" label="敏感权限" width="100"></el-table-column>
          <el-table-column prop="notRecommendApply" label="不建议申请权限" width="130"></el-table-column>
          <el-table-column prop="minRequiredPermission" label="最小必要权限" width="130"></el-table-column>
        </el-table>
        <el-pagination
          @size-change="handlePermissionSizeChange"
          @current-change="handlePermissionPageChange"
          :current-page="permissionPagination.currentPage"
          :page-sizes="[10, 20, 50, 100]"
          :page-size="permissionPagination.pageSize"
          layout="total, sizes, prev, pager, next, jumper"
          :total="permissionPagination.total"
          style="margin-top: 20px; text-align: right;"
        >
        </el-pagination>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TaskDetail',
  mounted() {
    // 启动任务播报循环
    this.startTaskBroadcast()
  },
  beforeDestroy() {
    // 清理定时器
    if (this.broadcastTimer) {
      clearInterval(this.broadcastTimer)
    }
  },
  data() {
    return {
      collectMode: 'auto',
      activeTab: '',
      behaviorTab: 'download',
      sdkSearchText: '',
      sdkPagination: {
        currentPage: 1,
        pageSize: 10,
        total: 0
      },
      permissionPagination: {
        currentPage: 1,
        pageSize: 10,
        total: 0
      },
      sdkList: [],
      permissionList: [],
      permissionFilters: {
        name: '',
        meaning: '',
        protectionLevel: ''
      },
      permissionNameOptions: [
        { value: 'CAMERA', label: '相机权限' },
        { value: 'LOCATION', label: '位置权限' },
        { value: 'CONTACTS', label: '通讯录权限' },
        { value: 'PHONE', label: '电话权限' },
        { value: 'SMS', label: '短信权限' },
        { value: 'STORAGE', label: '存储权限' }
      ],
      permissionMeaningOptions: [
        { value: 'camera_access', label: '访问相机' },
        { value: 'location_access', label: '获取位置信息' },
        { value: 'contacts_access', label: '访问通讯录' },
        { value: 'phone_access', label: '拨打电话' },
        { value: 'sms_access', label: '发送短信' },
        { value: 'storage_access', label: '访问存储' }
      ],
      protectionLevelOptions: [
        { value: 'normal', label: '普通' },
        { value: 'dangerous', label: '危险' },
        { value: 'signature', label: '签名' },
        { value: 'system', label: '系统' }
      ],
      analysisTabs: [
        { label: '基本信息', value: 'basic' },
        { label: 'SDK信息', value: 'sdk' },
        { label: '权限分析', value: 'permission' },
        { label: '行为分析', value: 'behavior' }
      ],
      taskBroadcasts: [
        '合规评估（进行中）',
        '基本信息（进行中）',
        '人工采集（待人工）',
        '深度（进行中）'
      ],
      currentTaskIndex: 0,
      behaviorList: [
        {
          date: '2025-11-15',
          time: '14.15:03',
          action: '应用启动',
          personalInfo: '否'
        },
        {
          date: '2025-11-15',
          time: '14.15:18',
          action: '启动应用',
          personalInfo: '否'
        },
        {
          date: '2025-11-15',
          time: '14.15:18',
          action: '同意隐私',
          personalInfo: '否'
        },
        {
          date: '2025-11-15',
          time: '14.15:18',
          action: '同意隐私',
          personalInfo: '否'
        },
        {
          date: '2025-11-15',
          time: '14.15:18',
          action: '功能通历',
          personalInfo: '是'
        }
      ]
    }
  },
  created() {
    this.loadTaskDetail()
  },
  methods: {
    loadTaskDetail() {
      // TODO: 从API获取任务详情数据
      const taskId = this.$route.params.id
      console.log('加载任务详情:', taskId)
    },

    startTaskBroadcast() {
      // 每2秒切换一次任务播报
      this.broadcastTimer = setInterval(() => {
        this.currentTaskIndex = (this.currentTaskIndex + 1) % this.taskBroadcasts.length
      }, 2000)
    },

    handleCompare() {
      this.$message.info('跳转到应用对比页面...')
    },

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
    },

    handleSdkSizeChange(val) {
      this.sdkPagination.pageSize = val
      this.loadSdkList()
    },

    handleSdkPageChange(val) {
      this.sdkPagination.currentPage = val
      this.loadSdkList()
    },

    loadSdkList() {
      // TODO: 从API获取SDK列表数据
      console.log('加载SDK列表')
    },

    handlePermissionSizeChange(val) {
      this.permissionPagination.pageSize = val
      this.loadPermissionList()
    },

    handlePermissionPageChange(val) {
      this.permissionPagination.currentPage = val
      this.loadPermissionList()
    },

    loadPermissionList() {
      // TODO: 从API获取权限列表数据
      console.log('加载权限列表')
    },

    resetPermissionFilters() {
      this.permissionFilters = {
        name: '',
        meaning: '',
        protectionLevel: ''
      }
      this.loadPermissionList()
    },

    searchPermissions() {
      console.log('搜索权限:', this.permissionFilters)
      this.loadPermissionList()
    },

    handleCollectModeChange(mode) {
      this.collectMode = mode
      this.activeTab = '' // 清空分析标签
    },

    handleTabChange(tab) {
      this.activeTab = tab
      this.collectMode = '' // 清空采集模式
    }
  }
}
</script>

<style lang="scss" scoped>
.task-detail-container {
  background: #fff;
  padding: 20px;

  // 顶部区域
  .top-section {
    padding: 15px;
    margin-bottom: 15px;

    // 第一行
    .header-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;

      .app-info {
        display: flex;
        align-items: center;
        gap: 15px;

        .app-label {
          font-size: 16px;
          font-weight: bold;
          color: #303133;
        }
      }

      .header-actions {
        display: flex;
        gap: 10px;
      }
    }

    // 第二行：三个功能区域
    .function-areas {
      display: flex;
      gap: 20px;

      .function-area {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 10px;

        .area-title {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          font-weight: bold;
          font-size: 14px;
          color: #303133;

          i {
            color: #409EFF;
            font-size: 18px;
          }
        }

        .area-buttons {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
          justify-content: center;
        }

        .task-broadcast {
          margin-top: 10px;
          height: 20px;
          display: flex;
          align-items: center;
          justify-content: center;
          overflow: hidden;

          .broadcast-text {
            font-size: 12px;
            color: #409EFF;
            text-align: center;
          }
        }

        .slide-up-enter-active,
        .slide-up-leave-active {
          transition: all 0.3s ease;
        }

        .slide-up-enter {
          transform: translateY(20px);
          opacity: 0;
        }

        .slide-up-leave-to {
          transform: translateY(-20px);
          opacity: 0;
        }

        .assessment-text {
          padding: 10px;
          background: transparent;
          border: 1px solid #dcdfe6;
          border-radius: 4px;
          font-size: 13px;
          color: #606266;
          line-height: 1.6;
          text-align: center;
          max-width: 280px;
          margin: 0 auto;
        }
      }
    }
  }

  // 橙色提示区域
  .warning-banner {
    background: #f5f7fa;
    padding: 12px 15px;
    margin-bottom: 15px;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    overflow: hidden;
    position: relative;

    .warning-label {
      font-weight: bold;
      color: #303133;
      flex-shrink: 0;
    }

    .warning-text-wrapper {
      position: absolute;
      left: 50%;
      transform: translateX(-50%);
      display: flex;
      align-items: center;
      gap: 8px;
      overflow: hidden;
      max-width: 60%;

      > i {
        color: #ff9800;
        font-size: 16px;
        flex-shrink: 0;
      }

      .scrolling-text {
        flex: 1;
        overflow: hidden;
        white-space: nowrap;

        .warning-text {
          display: inline-block;
          color: #ff9800;
          animation: scroll-left 15s linear infinite;
          padding-left: 100%;
        }
      }
    }
  }

  @keyframes scroll-left {
    0% {
      transform: translateX(0);
    }
    100% {
      transform: translateX(-100%);
    }
  }

  // 底部三列内容区域
  .content-wrapper {
    display: flex;
    gap: 15px;
    align-items: stretch;
    min-height: calc(100vh - 400px);

    // 左列 (40%)
    .left-column {
      flex: 4;
      min-width: 0;
      padding: 15px;
      display: flex;
      flex-direction: column;

      .phone-info-box {
        margin-bottom: 15px;
        flex-shrink: 0;

        .info-item {
          display: flex;
          align-items: center;
          gap: 5px;
          font-size: 13px;

          .info-label {
            color: #606266;
          }

          .info-value {
            color: #303133;
            font-weight: 500;
          }
        }
      }

      .phone-preview {
        flex: 1;
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 0;
        overflow: hidden;
        background: transparent;
        border-radius: 4px;
        border: 1px solid #e0e0e0;

        .vnc-iframe {
          width: 100%;
          height: 100%;
          min-height: 600px;
          border: none;
          border-radius: 4px;
          overflow: hidden;
        }
      }
    }

    // 中列 (40%)
    .middle-column {
      flex: 4;
      min-width: 0;
      padding: 15px;
      display: flex;
      flex-direction: column;

      .realtime-box {
        display: flex;
        flex-direction: column;
        height: 100%;

        .realtime-header {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 15px;
          background: #409EFF;
          color: #fff;
          border-radius: 4px;
          margin-bottom: 15px;
          font-weight: bold;
          flex-shrink: 0;

          i {
            font-size: 16px;
          }
        }

        .realtime-content {
          background: #ecf5ff;
          padding: 20px;
          border-radius: 4px;
          font-size: 14px;
          line-height: 2;
          flex: 1;
          overflow-y: auto;

          p {
            margin: 0 0 10px 0;
            color: #303133;

            &:last-child {
              margin-bottom: 0;
            }
          }
        }
      }
    }

    // 右列 (20%)
    .right-column {
      flex: 2;
      min-width: 0;
      padding: 15px;
      display: flex;
      flex-direction: column;

      .behavior-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 15px;
        flex-shrink: 0;

        .behavior-label {
          padding: 5px 12px;
          background: #f5f7fa;
          border-radius: 3px;
          font-size: 12px;
          color: #606266;
        }
      }

      .el-table {
        border: 1px solid #e0e0e0;
        flex: 1;
      }
    }

    // 基本信息面板
    .info-panel {
      width: 100%;
      padding: 20px;
      border-radius: 4px;

      .info-title {
        font-size: 18px;
        font-weight: bold;
        color: #303133;
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 2px solid #e0e0e0;
      }

      .info-content {
        .info-row {
          display: flex;
          padding: 12px 0;
          border-bottom: 1px solid #f0f0f0;

          &:last-child {
            border-bottom: none;
          }

          .info-label {
            width: 200px;
            color: #606266;
            font-size: 14px;
            flex-shrink: 0;
          }

          .info-value {
            flex: 1;
            color: #303133;
            font-size: 14px;
          }
        }
      }
    }

    // SDK信息面板
    .sdk-panel {
      width: 100%;
      padding: 20px;
      border-radius: 4px;

      .sdk-search {
        display: flex;
        align-items: center;
      }
    }

    // 权限分析面板
    .permission-panel {
      width: 100%;
      padding: 20px;
      border-radius: 4px;

      .permission-title {
        font-size: 18px;
        font-weight: bold;
        color: #303133;
        margin-bottom: 15px;
      }

      .permission-filters {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 15px;
        flex-wrap: wrap;
      }
    }
  }
}

// 响应式适配
@media screen and (max-width: 1400px) {
  .task-detail-container {
    .content-wrapper {
      flex-direction: column;

      .left-column,
      .right-column {
        width: 100%;
      }
    }
  }
}
</style>

