<template>
  <div class="app-container new-task-container">
    <el-card class="task-card">
      <div slot="header" class="card-header">
        <span class="header-title">
          <i class="el-icon-upload"></i>
          上传应用
        </span>
      </div>

      <el-form ref="taskForm" :model="taskForm" :rules="rules" label-width="140px">
        <!-- 本地上传区域 -->
        <div class="upload-section">

          <!-- 文件上传区域 -->
          <el-upload
            ref="upload"
            class="upload-area"
            drag
            :action="uploadUrl"
            :headers="uploadHeaders"
            :file-list="fileList"
            :on-success="handleUploadSuccess"
            :on-error="handleUploadError"
            :on-remove="handleRemove"
            :before-upload="beforeUpload"
            :limit="50"
            :on-exceed="handleExceed"
            accept=".apk,.ipa"
            multiple
          >
            <div class="upload-content">
              <i class="el-icon-upload"></i>
              <div class="upload-text">
                <p class="main-text">将文件拖到此处，或<em>点击上传</em></p>
                <p class="sub-text">暂无数据</p>
              </div>
            </div>
          </el-upload>

          <div class="file-actions" v-if="fileList.length > 0">
            <el-checkbox v-model="selectAll" @change="handleSelectAll">
              全选 (已选: {{ selectedCount }}项)
            </el-checkbox>
            <div class="action-buttons">
              <el-button size="small" @click="handleAddFiles">添加</el-button>
              <el-button size="small" @click="handleViewSelected">查看选中</el-button>
            </div>
          </div>
        </div>

        <!-- 检测任务名称 -->
        <el-form-item label="检测任务名称" prop="taskName">
          <el-input
            v-model="taskForm.taskName"
            placeholder="请输入检测任务名称"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>

        <!-- 检测任务类型 -->
        <el-form-item label="检测任务类型" prop="taskType">
          <el-radio-group v-model="taskForm.taskType">
            <el-radio label="auto">
              <el-tooltip content="系统自动完成所有检测流程" placement="top">
                <span>全自动 <i class="el-icon-question"></i></span>
              </el-tooltip>
            </el-radio>
            <el-radio label="semi">自动+人工</el-radio>
            <el-radio label="manual">纯人工</el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- 运行系统版本 -->
        <el-form-item label="运行系统版本" prop="systemVersion">
          <el-radio-group v-model="taskForm.systemVersion">
            <el-radio label="default">
              <el-tooltip content="根据应用兼容版本本自动选择" placement="top">
                <span>系统默认（根据应用兼容版本本自动选择）<i class="el-icon-question"></i></span>
              </el-tooltip>
            </el-radio>
            <el-radio label="android8">Android 8</el-radio>
            <el-radio label="android10">Android 10</el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- 应用基础检测 -->
        <el-form-item label="应用基础检测">
          <el-checkbox-group v-model="taskForm.basicCheck">
            <el-checkbox label="basic">基本信息</el-checkbox>
            <el-checkbox label="sdk">SDK信息</el-checkbox>
            <el-checkbox label="data">数据分析</el-checkbox>
            <el-checkbox label="behavior">行为分析</el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <!-- 应用安全漏洞 -->
        <el-form-item label="应用安全漏洞">
          <el-checkbox v-model="taskForm.securityCheck">漏洞信息</el-checkbox>
        </el-form-item>

        <!-- 合规标准模板 -->
        <el-form-item label="合规标准模板">
          <el-select
            v-model="taskForm.complianceTemplate"
            placeholder="请选择合规标准模板"
            style="width: 100%"
          >
            <el-option label="无" value=""></el-option>
            <el-option label="个人信息保护法" value="pipl"></el-option>
            <el-option label="网络安全法" value="csl"></el-option>
            <el-option label="App违法违规收集使用个人信息行为认定方法" value="app_method"></el-option>
            <el-option label="移动互联网应用程序信息服务管理规定" value="app_regulation"></el-option>
          </el-select>
        </el-form-item>

        <!-- 输出报告样式 -->
        <el-form-item label="输出报告样式" prop="reportStyle">
          <el-select
            v-model="taskForm.reportStyle"
            placeholder="请选择报告样式"
            style="width: 100%"
          >
            <el-option label="默认报告模板" value="default"></el-option>
            <el-option label="详细报告模板" value="detail"></el-option>
            <el-option label="简洁报告模板" value="simple"></el-option>
          </el-select>
        </el-form-item>

        <!-- 输出报告内容 -->
        <el-form-item label="输出报告内容">
          <div class="report-content-wrapper">
            <!-- 第一行：检测项目 -->
            <div class="report-row">
              <span style="margin-right: 20px;">基础信息</span>
              <el-checkbox-group v-model="taskForm.reportContent">
                <el-checkbox label="base_info">基本信息</el-checkbox>
                <el-checkbox label="sdk_info">SDK信息</el-checkbox>
                <el-checkbox label="permission">权限分析</el-checkbox>
                <el-checkbox label="behavior">行为分析</el-checkbox>
              </el-checkbox-group>
            </div>

            <!-- 第二行：合规选项 -->
            <div class="report-row">
              <span style="margin-right: 20px">合规告警</span>
              <el-radio-group v-model="taskForm.complianceOption">
                <el-radio label="issue_only">
                  <el-tooltip content="仅输出存在问题的检测项" placement="top">
                    <span>仅含问题项 <i class="el-icon-question"></i></span>
                  </el-tooltip>
                </el-radio>
                <el-radio label="all">
                  <el-tooltip content="包含所有检测项的完整报告" placement="top">
                    <span>包含全部检测项 <i class="el-icon-question"></i></span>
                  </el-tooltip>
                </el-radio>
                <el-radio label="none">无</el-radio>
              </el-radio-group>
            </div>
          </div>
        </el-form-item>

        <!-- 提交按钮 -->
        <el-form-item style="margin-left: -140px">
          <el-button type="primary" @click="handleSubmit" :loading="submitLoading">
            提交检测任务
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script>
import { getToken } from '@/utils/auth'
import { submitTask } from '@/api/app/task'

export default {
  name: 'NewTask',
  data() {
    return {
      // 文件列表
      fileList: [],
      // 全选状态
      selectAll: false,
      // 提交加载状态
      submitLoading: false,
      // 已上传文件的路径信息
      uploadedFiles: [],
      // 表单数据
      taskForm: {
        taskName: '',
        taskType: 'auto',
        systemVersion: 'default',
        basicCheck: ['basic', 'sdk', 'data', 'behavior'],
        securityCheck: true,
        complianceTemplate: '',
        reportStyle: 'default',
        reportContent: ['base_info', 'sdk_info', 'permission', 'behavior'],
        complianceOption: 'all'
      },
      // 表单验证规则
      rules: {
        taskName: [
          { required: true, message: '请输入检测任务名称', trigger: 'blur' },
          { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
        ],
        taskType: [
          { required: true, message: '请选择检测任务类型', trigger: 'change' }
        ],
        systemVersion: [
          { required: true, message: '请选择运行系统版本', trigger: 'change' }
        ],
        reportStyle: [
          { required: true, message: '请选择报告样式', trigger: 'change' }
        ]
      }
    }
  },
  computed: {
    // 上传URL
    uploadUrl() {
      return process.env.VUE_APP_BASE_API + '/app/task/upload'
    },
    // 上传请求头
    uploadHeaders() {
      return {
        Authorization: 'Bearer ' + getToken()
      }
    },
    // 已选中文件数量
    selectedCount() {
      return this.fileList.filter(file => file.selected).length
    }
  },
  methods: {

    // 文件上传前验证
    beforeUpload(file) {
      const isAPK = file.name.endsWith('.apk')
      const isIPA = file.name.endsWith('.ipa')
      const isLt300M = file.size / 1024 / 1024 < 300

      if (!isAPK && !isIPA) {
        this.$message.error('只能上传 APK 或 IPA 格式的文件！')
        return false
      }
      if (!isLt300M) {
        this.$message.error('上传文件大小不能超过 300MB！')
        return false
      }
      return true
    },

    // 文件上传成功
    handleUploadSuccess(response, file, fileList) {
      console.log('上传成功，响应数据:', response)
      console.log('文件信息:', file)

      // 检查响应格式并保存文件信息
      let fileInfo = {
        uid: file.uid,
        name: file.name,
        fileName: '',
        filePath: '',
        fileSize: file.size,
        url: ''
      }

      // 根据不同的响应格式提取数据
      if (response && response.code === 200 && response.data) {
        // 后端正常响应
        fileInfo.fileName = response.data.fileName || ''
        fileInfo.filePath = response.data.filePath || ''
        fileInfo.fileSize = response.data.fileSize || file.size
        fileInfo.url = response.data.url || ''
        fileInfo.name = response.data.originalFilename || file.name

        this.$message.success('文件上传成功！')
      } else if (response && response.fileName) {
        // 兼容其他格式
        fileInfo.fileName = response.fileName
        fileInfo.filePath = response.filePath || ''
        fileInfo.url = response.url || ''

        this.$message.success('文件上传成功！')
      } else {
        // 即使响应格式不对，也记录文件（用于离线测试）
        // 使用模拟路径
        fileInfo.filePath = `/opt/apk/${file.name}`
        fileInfo.fileName = `/opt/apk/${file.name}`

        console.warn('响应格式异常，使用模拟路径:', fileInfo)
        this.$message.warning('文件已添加（后端服务未连接，使用模拟路径）')
      }

      // 添加到已上传文件列表
      this.uploadedFiles.push(fileInfo)

      // 更新文件列表
      this.fileList = fileList.map((item, index) => ({
        ...item,
        selected: false,
        uid: item.uid || index,
        response: item.response || response
      }))

      console.log('已上传文件列表:', this.uploadedFiles)
      console.log('当前文件列表:', this.fileList)
    },

    // 文件上传失败
    handleUploadError(err, file, fileList) {
      console.error('文件上传失败:', err)
      this.$message.error('文件上传失败：' + (err.message || '服务器连接失败'))
    },

    // 移除文件
    handleRemove(file, fileList) {
      this.fileList = fileList
      // 同时从已上传文件列表中移除
      const index = this.uploadedFiles.findIndex(f => f.uid === file.uid)
      if (index > -1) {
        this.uploadedFiles.splice(index, 1)
      }
      console.log('移除文件后，已上传文件列表:', this.uploadedFiles)
    },

    // 文件超出限制
    handleExceed(files, fileList) {
      this.$message.warning(`最多只能上传 50 个文件，当前已选择 ${fileList.length} 个文件`)
    },

    // 全选/取消全选
    handleSelectAll(val) {
      this.fileList.forEach(file => {
        file.selected = val
      })
    },

    // 添加文件
    handleAddFiles() {
      this.$refs.upload.$refs['upload-inner'].$refs.input.click()
    },

    // 查看选中的文件
    handleViewSelected() {
      const selected = this.fileList.filter(file => file.selected)
      if (selected.length === 0) {
        this.$message.warning('请先选择文件')
        return
      }
      console.log('选中的文件:', selected)
      this.$message.info(`已选中 ${selected.length} 个文件`)
    },

    // 提交任务
    handleSubmit() {
      this.$refs.taskForm.validate(valid => {
        if (!valid) {
          this.$message.error('请完善表单信息')
          return
        }

        // 验证是否上传了文件
        console.log('提交时检查 - fileList:', this.fileList)
        console.log('提交时检查 - uploadedFiles:', this.uploadedFiles)

        if (this.fileList.length === 0) {
          this.$message.warning('请先上传应用文件')
          return
        }

        // 如果 uploadedFiles 为空，但 fileList 不为空，说明可能是上传失败但文件还在列表中
        if (this.uploadedFiles.length === 0 && this.fileList.length > 0) {
          this.$message.error('文件上传失败，请重新上传或检查后端服务是否启动')
          return
        }

        this.$confirm('确认提交检测任务吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          this.submitLoading = true

          // 构造提交数据，包含文件路径信息
          const submitData = {
            ...this.taskForm,
            // 传递文件路径数组（用于后续安装APK）
            filePaths: this.uploadedFiles.map(f => f.filePath),
            fileNames: this.uploadedFiles.map(f => f.fileName),
            originalFilenames: this.uploadedFiles.map(f => f.name)
          }

          console.log('提交数据:', submitData)

          // 调用API提交任务
          submitTask(submitData).then(response => {
            this.$message.success('检测任务提交成功！')

            // 跳转到动态分析页面，携带必要参数
            this.$router.push({
              path: '/task/task/dynamic',
              query: {
                taskId: response.data?.taskId || Date.now(), // 任务ID
                apkPath: this.uploadedFiles[0].filePath, // 第一个APK的路径
                taskName: this.taskForm.taskName,
                filePaths: JSON.stringify(this.uploadedFiles.map(f => f.filePath)) // 所有文件路径
              }
            })
          }).catch(error => {
            console.error('任务提交失败:', error)
            this.$message.error(error.msg || '任务提交失败，请检查后端服务是否启动')
          }).finally(() => {
            this.submitLoading = false
          })
        }).catch(() => {
          this.$message.info('已取消提交')
        })
      })
    },

    // 重置表单
    handleReset() {
      this.$refs.taskForm.resetFields()
      this.fileList = []
      this.uploadedFiles = []
      this.selectAll = false
    },

    // 取消
    handleCancel() {
      this.$router.go(-1)
    }
  }
}
</script>

<style lang="scss" scoped>
.new-task-container {
  .task-card {
    max-width: 1500px;
    margin: 0 auto;

    .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;

      .header-title {
        font-size: 18px;
        font-weight: bold;
        color: #303133;

        i {
          margin-right: 8px;
          color: #409EFF;
        }
      }

      .header-tips {
        font-size: 12px;
        color: #909399;
      }
    }
  }

  .upload-section {
    margin-bottom: 30px;

    .upload-note {
      font-size: 12px;
      color: #909399;
      margin-bottom: 15px;
      text-align: right;
    }
  }

  // 文件上传区域
  .upload-area {
    width: 100%;

    ::v-deep .el-upload {
      width: 100%;

      .el-upload-dragger {
        width: 100%;
        height: 300px;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 2px dashed #d9d9d9;
        border-radius: 6px;
        background-color: #fafafa;
        transition: all 0.3s;

        &:hover {
          border-color: #409EFF;
        }
      }
    }

    .upload-content {
      text-align: center;

      i {
        font-size: 67px;
        color: #c0c4cc;
        margin-bottom: 16px;
      }

      .upload-text {
        .main-text {
          font-size: 14px;
          color: #606266;
          margin-bottom: 8px;

          em {
            color: #409EFF;
            font-style: normal;
          }
        }

        .sub-text {
          font-size: 12px;
          color: #909399;
        }
      }
    }
  }

  // 文件操作区域
  .file-actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 15px;
    padding: 10px;
    background-color: #f5f7fa;
    border-radius: 4px;

    .action-buttons {
      display: flex;
      gap: 10px;
    }
  }

  // 输出报告内容样式
  .report-content-wrapper {
    width: 100%;

    .report-row {
      margin-bottom: 10px;
      display: flex;      /* 开启弹性布局，子元素水平排列 */
      align-items: center; /* 子元素垂直居中对齐 */
      &:last-child {
        margin-bottom: 0;
      }

      &.compliance-row {
        padding-top: 10px;
        border-top: 1px dashed #E4E7ED;
      }
    }
  }

  // 表单项样式优化
  ::v-deep .el-form-item {
    margin-bottom: 25px;

    .el-form-item__label {
      font-weight: 500;
      color: #303133;

      &::before {
        color: #F56C6C;
      }
    }

    .el-radio,
    .el-checkbox {
      margin-right: 30px;

      .el-icon-question {
        color: #909399;
        cursor: help;
      }
    }
  }

  // 提交按钮区域
  ::v-deep .el-form-item:last-child {
    margin-top: 40px;
    padding-top: 20px;
    border-top: 1px solid #EBEEF5;

    .el-form-item__content {
      text-align: center;
    }

    .el-button {
      min-width: 120px;
    }
  }
}

// 响应式适配
@media screen and (max-width: 768px) {
  .new-task-container {
    .task-card .card-header {
      flex-direction: column;
      align-items: flex-start;

      .header-tips {
        margin-top: 8px;
      }
    }

    .file-actions {
      flex-direction: column;
      gap: 10px;

      .action-buttons {
        width: 100%;

        .el-button {
          flex: 1;
        }
      }
    }

    ::v-deep .el-form-item .el-radio,
    ::v-deep .el-form-item .el-checkbox {
      display: block;
      margin-bottom: 10px;
    }
  }
}
</style>
