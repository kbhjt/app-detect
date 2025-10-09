<template>
  <div class="app-container my-task-container">
    <!-- 搜索区域 -->
    <el-form :model="queryParams" ref="queryForm" size="small" :inline="true" v-show="showSearch" label-width="100px">
      <el-form-item label="任务名称" prop="taskName">
        <el-input
          v-model="queryParams.taskName"
          placeholder="请输入内容"
          clearable
          style="width: 200px"
          @keyup.enter.native="handleQuery"
        />
      </el-form-item>
      <el-form-item label="合规检测类型" prop="complianceType">
        <el-select
          v-model="queryParams.complianceType"
          placeholder="请选择合规性检测类型"
          clearable
          style="width: 200px"
        >
          <el-option label="个人信息保护法" value="pipl"></el-option>
          <el-option label="网络安全法" value="csl"></el-option>
          <el-option label="App违法违规收集使用个人信息行为认定方法" value="app_method"></el-option>
          <el-option label="移动互联网应用程序信息服务管理规定" value="app_regulation"></el-option>
        </el-select>
      </el-form-item>
      <el-form-item label="任务类型" prop="taskType">
        <el-select
          v-model="queryParams.taskType"
          placeholder="请选择任务类型"
          clearable
          style="width: 150px"
        >
          <el-option label="全自动" value="auto"></el-option>
          <el-option label="自动+人工" value="semi"></el-option>
          <el-option label="纯人工" value="manual"></el-option>
        </el-select>
      </el-form-item>
      <el-form-item label="日期范围" prop="dateRange">
        <el-date-picker
          v-model="dateRange"
          style="width: 280px"
          value-format="yyyy-MM-dd"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
        ></el-date-picker>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="el-icon-search" size="mini" @click="handleQuery">查询</el-button>
        <el-button icon="el-icon-refresh" size="mini" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <!-- 操作按钮区域 -->
    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button
          type="primary"
          plain
          icon="el-icon-plus"
          size="mini"
          @click="handleAdd"
          v-hasPermi="['app:task:add']"
        >新建任务</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button
          type="info"
          plain
          icon="el-icon-sort"
          size="mini"
          @click="handleCompare"
          :disabled="multiple"
        >应用对比</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button
          type="warning"
          plain
          icon="el-icon-download"
          size="mini"
          @click="handleDownloadOffline"
        >下载离线</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button
          type="success"
          plain
          icon="el-icon-s-promotion"
          size="mini"
          @click="handleCheckNew"
          :disabled="single"
        >查新检测</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button
          type="warning"
          plain
          icon="el-icon-edit"
          size="mini"
          @click="handleCorrect"
          :disabled="single"
        >修正任务</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button
          type="danger"
          plain
          icon="el-icon-delete"
          size="mini"
          @click="handleDelete"
          :disabled="multiple"
          v-hasPermi="['app:task:remove']"
        >删除</el-button>
      </el-col>
      <right-toolbar :showSearch.sync="showSearch" @queryTable="getList"></right-toolbar>
    </el-row>

    <!-- 数据表格 -->
    <el-table 
      v-loading="loading" 
      :data="taskList" 
      @selection-change="handleSelectionChange"
      :header-cell-style="{background: '#f5f7fa', color: '#606266'}"
    >
      <el-table-column type="selection" width="50" align="center" />
      <el-table-column label="序号" type="index" width="60" align="center">
        <template slot-scope="scope">
          <span>{{ (queryParams.pageNum - 1) * queryParams.pageSize + scope.$index + 1 }}</span>
        </template>
      </el-table-column>
      <el-table-column label="任务名称" prop="taskName" width="180" show-overflow-tooltip>
        <template slot-scope="scope">
          <span class="task-name-text">{{ scope.row.taskName }}</span>
        </template>
      </el-table-column>
      <el-table-column label="应用名称" prop="appName" width="200" align="center">
        <template slot-scope="scope">
          <div class="app-info">
            <img :src="scope.row.appIcon" class="app-icon" />
            <span class="app-name">{{ scope.row.appName }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="应用版本" prop="appVersion" width="120" align="center" />
      <el-table-column label="任务状态" prop="taskStatus" width="150" align="center">
        <template slot-scope="scope">
          <el-tag 
            :type="getTaskStatusType(scope.row.taskStatus)" 
            size="small"
            :icon="getTaskStatusIcon(scope.row.taskStatus)"
          >
            {{ scope.row.taskStatus }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="报告状态" prop="reportStatus" width="120" align="center">
        <template slot-scope="scope">
          <el-tag 
            :type="getReportStatusType(scope.row.reportStatus)" 
            size="small"
            effect="plain"
          >
            {{ scope.row.reportStatus }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" prop="createTime" width="160" align="center" />
      <el-table-column label="操作" align="center" class-name="small-padding fixed-width" min-width="280">
        <template slot-scope="scope">
          <el-button
            size="mini"
            type="text"
            icon="el-icon-view"
            @click="handleDetail(scope.row)"
          >详情</el-button>
          <el-button
            size="mini"
            type="text"
            icon="el-icon-video-pause"
            @click="handleStop(scope.row)"
            v-if="scope.row.taskStatus !== '已终止' && scope.row.taskStatus !== '已完成'"
          >终止</el-button>
          <el-button
            size="mini"
            type="text"
            icon="el-icon-data-analysis"
            @click="handleViewReport(scope.row)"
            :disabled="scope.row.reportStatus === '待完成'"
          >查看检测</el-button>
          <el-button
            size="mini"
            type="text"
            icon="el-icon-download"
            @click="handleDownload(scope.row)"
            :disabled="scope.row.reportStatus === '待完成'"
          >下载</el-button>
          <el-button
            size="mini"
            type="text"
            icon="el-icon-delete"
            @click="handleDelete(scope.row)"
            v-hasPermi="['app:task:remove']"
          >删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <pagination
      v-show="total > 0"
      :total="total"
      :page.sync="queryParams.pageNum"
      :limit.sync="queryParams.pageSize"
      @pagination="getList"
    />
  </div>
</template>

<script>
import { listTask, delTask, cancelTask, downloadReport } from '@/api/app/task'

export default {
  name: 'MyTask',
  data() {
    return {
      // 遮罩层
      loading: true,
      // 选中数组
      ids: [],
      // 非单个禁用
      single: true,
      // 非多个禁用
      multiple: true,
      // 显示搜索条件
      showSearch: true,
      // 总条数
      total: 0,
      // 任务表格数据
      taskList: [],
      // 日期范围
      dateRange: [],
      // 查询参数
      queryParams: {
        pageNum: 1,
        pageSize: 10,
        taskName: null,
        complianceType: null,
        taskType: null,
        startDate: null,
        endDate: null
      }
    }
  },
  created() {
    this.getList()
  },
  methods: {
    /** 查询任务列表 */
    getList() {
      this.loading = true
      
      // 处理日期范围
      if (this.dateRange && this.dateRange.length === 2) {
        this.queryParams.startDate = this.dateRange[0]
        this.queryParams.endDate = this.dateRange[1]
      } else {
        this.queryParams.startDate = null
        this.queryParams.endDate = null
      }

      // 模拟数据
      setTimeout(() => {
        this.taskList = this.getMockData()
        this.total = 20
        this.loading = false
      }, 300)

      // TODO: 实际应该调用API
      // listTask(this.queryParams).then(response => {
      //   this.taskList = response.rows
      //   this.total = response.total
      //   this.loading = false
      // })
    },

    // 获取模拟数据
    getMockData() {
      const mockData = [
        {
          id: 1,
          taskName: '口语轻松学',
          appName: '口语轻松学',
          appIcon: 'https://via.placeholder.com/40/FFD700/000000?text=口',
          appVersion: '1.3.4',
          taskStatus: '等人工',
          reportStatus: '待完成',
          createTime: '2025-10-08 14:30:25'
        },
        {
          id: 2,
          taskName: '小方出行',
          appName: '小方出行',
          appIcon: 'https://via.placeholder.com/40/FF8C00/000000?text=小',
          appVersion: '6.4.1',
          taskStatus: '等人工',
          reportStatus: '待完成',
          createTime: '2025-10-08 10:15:12'
        },
        {
          id: 3,
          taskName: '少儿趣配音',
          appName: '少儿趣配音',
          appIcon: 'https://via.placeholder.com/40/FFD700/000000?text=少',
          appVersion: '6.63.0',
          taskStatus: '等人工',
          reportStatus: '待完成',
          createTime: '2025-10-07 16:20:43'
        },
        {
          id: 4,
          taskName: '英语趣配音合规检测',
          appName: '趣配音',
          appIcon: 'https://via.placeholder.com/40/32CD32/000000?text=趣',
          appVersion: '7.59.2',
          taskStatus: '已终止',
          reportStatus: '待完成',
          createTime: '2025-10-07 09:50:18'
        },
        {
          id: 5,
          taskName: '财富天路',
          appName: '财富大路',
          appIcon: 'https://via.placeholder.com/40/1E90FF/FFFFFF?text=财',
          appVersion: '2.4.36',
          taskStatus: '已完成',
          reportStatus: '已完成',
          createTime: '2025-10-06 13:32:55'
        },
        {
          id: 6,
          taskName: '少儿趣配音',
          appName: '少儿趣配音',
          appIcon: 'https://via.placeholder.com/40/FFD700/000000?text=少',
          appVersion: '6.42.0',
          taskStatus: '已完成',
          reportStatus: '已完成',
          createTime: '2025-10-05 11:22:33'
        }
      ]
      return mockData
    },

    // 获取任务状态类型
    getTaskStatusType(status) {
      const statusMap = {
        '等人工': 'primary',
        '检测中': 'warning',
        '已完成': 'success',
        '已终止': 'info',
        '失败': 'danger'
      }
      return statusMap[status] || 'info'
    },

    // 获取任务状态图标
    getTaskStatusIcon(status) {
      const iconMap = {
        '等人工': 'el-icon-user',
        '检测中': 'el-icon-loading',
        '已完成': 'el-icon-circle-check',
        '已终止': 'el-icon-video-pause',
        '失败': 'el-icon-circle-close'
      }
      return iconMap[status] || ''
    },

    // 获取报告状态类型
    getReportStatusType(status) {
      return status === '已完成' ? 'success' : 'warning'
    },

    // 多选框选中数据
    handleSelectionChange(selection) {
      this.ids = selection.map(item => item.id)
      this.single = selection.length !== 1
      this.multiple = !selection.length
    },

    // 搜索按钮操作
    handleQuery() {
      this.queryParams.pageNum = 1
      this.getList()
    },

    // 重置按钮操作
    resetQuery() {
      this.dateRange = []
      this.resetForm('queryForm')
      this.handleQuery()
    },

    // 新建任务
    handleAdd() {
      this.$router.push('/app/task/new')
    },

    // 应用对比
    handleCompare() {
      if (this.ids.length < 2) {
        this.$message.warning('请至少选择两个任务进行对比')
        return
      }
      this.$message.info('应用对比功能开发中...')
      // TODO: 跳转到对比页面
    },

    // 下载离线
    handleDownloadOffline() {
      this.$message.info('下载离线包功能开发中...')
      // TODO: 实现离线包下载
    },

    // 查新检测
    handleCheckNew(row) {
      const id = row.id || this.ids[0]
      this.$confirm('是否对该应用进行查新检测？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        this.$message.success('已提交查新检测任务')
        // TODO: 调用查新检测API
      }).catch(() => {})
    },

    // 修正任务
    handleCorrect(row) {
      const id = row.id || this.ids[0]
      this.$message.info('修正任务功能开发中...')
      // TODO: 跳转到任务修正页面
    },

    // 查看详情
    handleDetail(row) {
      this.$message.info('查看任务详情功能开发中...')
      // TODO: 跳转到详情页面
      // this.$router.push('/app/task/detail/' + row.id)
    },

    // 终止任务
    handleStop(row) {
      this.$confirm('确认终止该检测任务吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        // TODO: 调用终止任务API
        // cancelTask(row.id).then(response => {
        //   this.$message.success('任务已终止')
        //   this.getList()
        // })
        this.$message.success('任务已终止')
        row.taskStatus = '已终止'
      }).catch(() => {})
    },

    // 查看检测报告
    handleViewReport(row) {
      if (row.reportStatus === '待完成') {
        this.$message.warning('报告尚未生成，请稍后查看')
        return
      }
      this.$message.info('查看检测报告功能开发中...')
      // TODO: 跳转到报告页面
      // this.$router.push('/app/report/' + row.id)
    },

    // 下载报告
    handleDownload(row) {
      if (row.reportStatus === '待完成') {
        this.$message.warning('报告尚未生成，无法下载')
        return
      }
      this.$message.success('开始下载报告...')
      // TODO: 调用下载报告API
      // downloadReport(row.id).then(response => {
      //   this.download(response.data)
      // })
    },

    // 删除按钮操作
    handleDelete(row) {
      const ids = row.id ? [row.id] : this.ids
      const names = row.taskName ? [row.taskName] : this.taskList
        .filter(item => this.ids.includes(item.id))
        .map(item => item.taskName)
      
      this.$confirm('是否确认删除任务"' + names.join('、') + '"？', '警告', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        // TODO: 调用删除API
        // return delTask(ids.join(','))
        this.$message.success('删除成功')
        this.getList()
      }).catch(() => {})
    }
  }
}
</script>

<style lang="scss" scoped>
.my-task-container {
  // 搜索表单样式
  ::v-deep .el-form {
    .el-form-item {
      margin-bottom: 15px;
    }
  }

  // 操作按钮区域
  .mb8 {
    margin-bottom: 12px;
  }

  // 表格样式优化
  ::v-deep .el-table {
    .task-name-text {
      color: #303133;
      font-weight: 500;
    }

    .app-info {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;

      .app-icon {
        width: 40px;
        height: 40px;
        border-radius: 8px;
        object-fit: cover;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      }

      .app-name {
        color: #409EFF;
        font-weight: 500;
      }
    }

    // 操作按钮样式
    .el-button--text {
      padding: 0 5px;
      margin: 0 3px;
    }
  }
}

// 响应式适配
@media screen and (max-width: 768px) {
  .my-task-container {
    ::v-deep .el-form {
      .el-form-item {
        margin-right: 0;
        width: 100%;

        .el-input,
        .el-select,
        .el-date-picker {
          width: 100% !important;
        }
      }
    }
  }
}
</style>

