<template>
  <div class="privacy-dashboard">
    <!-- 顶部标题区 -->
    <div class="dashboard-header">
      <div class="header-content">
        <div class="title-wrapper">
          <div class="main-title">
            <i class="el-icon-s-data"></i>
            移动应用隐私合规检测平台
          </div>
          <div class="sub-title">Mobile Application Privacy Compliance Detection Platform</div>
        </div>
        <div class="current-time">{{ currentTime }}</div>
      </div>
    </div>

    <!-- 核心数据概览 -->
    <div class="overview-section">
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="6" v-for="(item, index) in overviewData" :key="index">
          <div class="stat-card" :class="'card-' + index">
            <div class="card-icon">
              <i :class="item.icon"></i>
            </div>
            <div class="card-content">
              <div class="card-value">{{ item.value }}</div>
              <div class="card-label">{{ item.label }}</div>
              <div class="card-trend" :class="item.trend > 0 ? 'up' : 'down'">
                <i :class="item.trend > 0 ? 'el-icon-top' : 'el-icon-bottom'"></i>
                {{ Math.abs(item.trend) }}%
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 主要数据展示区 -->
    <el-row :gutter="20" class="chart-section">
      <!-- 左侧列 -->
      <el-col :xs="24" :lg="8">
        <!-- 合规率统计 -->
        <div class="chart-card">
          <div class="card-header">
            <span class="header-title">
              <i class="el-icon-pie-chart"></i>
              应用合规率统计
            </span>
          </div>
          <div class="card-body">
            <div ref="complianceChart" class="chart-container"></div>
          </div>
        </div>

        <!-- 风险等级分布 -->
        <div class="chart-card">
          <div class="card-header">
            <span class="header-title">
              <i class="el-icon-warning-outline"></i>
              风险等级分布
            </span>
          </div>
          <div class="card-body">
            <div ref="riskChart" class="chart-container"></div>
          </div>
        </div>
      </el-col>

      <!-- 中间列 -->
      <el-col :xs="24" :lg="8">
        <!-- 检测趋势 -->
        <div class="chart-card chart-card-large">
          <div class="card-header">
            <span class="header-title">
              <i class="el-icon-data-line"></i>
              近30天检测趋势
            </span>
          </div>
          <div class="card-body">
            <div ref="trendChart" class="chart-container-large"></div>
          </div>
        </div>
      </el-col>

      <!-- 右侧列 -->
      <el-col :xs="24" :lg="8">
        <!-- 违规类型分析 -->
        <div class="chart-card">
          <div class="card-header">
            <span class="header-title">
              <i class="el-icon-s-data"></i>
              违规类型TOP5
            </span>
          </div>
          <div class="card-body">
            <div ref="violationChart" class="chart-container"></div>
          </div>
        </div>

        <!-- 最近检测记录 -->
        <div class="chart-card">
          <div class="card-header">
            <span class="header-title">
              <i class="el-icon-document"></i>
              最近检测记录
            </span>
          </div>
          <div class="card-body">
            <div class="recent-list">
              <div
                v-for="(record, index) in recentRecords"
                :key="index"
                class="record-item"
              >
                <div class="record-left">
                  <div class="record-name">{{ record.appName }}</div>
                  <div class="record-time">{{ record.time }}</div>
                </div>
                <div class="record-right">
                  <el-tag
                    :type="record.status === '合规' ? 'success' : 'danger'"
                    size="small"
                  >
                    {{ record.status }}
                  </el-tag>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 底部数据表格区 -->
    <div class="table-section">
      <div class="chart-card">
        <div class="card-header">
          <span class="header-title">
            <i class="el-icon-tickets"></i>
            应用检测详情
          </span>
        </div>
        <div class="card-body">
          <el-table
            :data="tableData"
            style="width: 100%"
            :header-cell-style="{background: '#1a2332', color: '#fff'}"
          >
            <el-table-column prop="appName" label="应用名称" width="200"></el-table-column>
            <el-table-column prop="version" label="版本号" width="120"></el-table-column>
            <el-table-column prop="platform" label="平台" width="100">
              <template slot-scope="scope">
                <el-tag :type="scope.row.platform === 'Android' ? 'success' : 'primary'" size="small">
                  {{ scope.row.platform }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="checkTime" label="检测时间" width="180"></el-table-column>
            <el-table-column prop="complianceRate" label="合规率" width="120">
              <template slot-scope="scope">
                <el-progress
                  :percentage="scope.row.complianceRate"
                  :color="scope.row.complianceRate >= 80 ? '#67C23A' : '#F56C6C'"
                ></el-progress>
              </template>
            </el-table-column>
            <el-table-column prop="riskLevel" label="风险等级" width="120">
              <template slot-scope="scope">
                <el-tag
                  :type="getRiskType(scope.row.riskLevel)"
                  size="small"
                >
                  {{ scope.row.riskLevel }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="violations" label="违规项" width="100"></el-table-column>
            <el-table-column label="操作" fixed="right" width="150">
              <template slot-scope="scope">
                <el-button type="text" size="small" @click="viewDetail(scope.row)">查看详情</el-button>
                <el-button type="text" size="small" @click="downloadReport(scope.row)">下载报告</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as echarts from 'echarts'

export default {
  name: 'PrivacyDashboard',
  data() {
    return {
      currentTime: '',
      timeInterval: null,
      overviewData: [
        {
          label: '累计检测应用',
          value: '1,248',
          icon: 'el-icon-mobile-phone',
          trend: 12.5
        },
        {
          label: '今日检测数',
          value: '86',
          icon: 'el-icon-data-analysis',
          trend: 8.3
        },
        {
          label: '平均合规率',
          value: '87.6%',
          icon: 'el-icon-success',
          trend: 5.2
        },
        {
          label: '待处理问题',
          value: '23',
          icon: 'el-icon-warning',
          trend: -15.8
        }
      ],
      recentRecords: [
        { appName: '某社交APP', time: '2分钟前', status: '合规' },
        { appName: '某购物平台', time: '15分钟前', status: '不合规' },
        { appName: '某视频应用', time: '32分钟前', status: '合规' },
        { appName: '某游戏应用', time: '1小时前', status: '合规' },
        { appName: '某出行APP', time: '2小时前', status: '不合规' },
        { appName: '某金融应用', time: '3小时前', status: '合规' }
      ],
      tableData: [
        {
          appName: '微信',
          version: '8.0.32',
          platform: 'Android',
          checkTime: '2025-10-09 14:30:25',
          complianceRate: 95,
          riskLevel: '低风险',
          violations: 2
        },
        {
          appName: '抖音',
          version: '23.5.0',
          platform: 'iOS',
          checkTime: '2025-10-09 14:15:12',
          complianceRate: 78,
          riskLevel: '中风险',
          violations: 8
        },
        {
          appName: '淘宝',
          version: '10.23.0',
          platform: 'Android',
          checkTime: '2025-10-09 14:05:43',
          complianceRate: 88,
          riskLevel: '低风险',
          violations: 4
        },
        {
          appName: '美团',
          version: '12.15.203',
          platform: 'Android',
          checkTime: '2025-10-09 13:50:18',
          complianceRate: 65,
          riskLevel: '高风险',
          violations: 15
        },
        {
          appName: '支付宝',
          version: '10.5.0',
          platform: 'iOS',
          checkTime: '2025-10-09 13:32:55',
          complianceRate: 92,
          riskLevel: '低风险',
          violations: 3
        }
      ]
    }
  },
  mounted() {
    this.updateTime()
    this.timeInterval = setInterval(this.updateTime, 1000)
    this.$nextTick(() => {
      this.initCharts()
      window.addEventListener('resize', this.handleResize)
    })
  },
  beforeDestroy() {
    if (this.timeInterval) {
      clearInterval(this.timeInterval)
    }
    window.removeEventListener('resize', this.handleResize)
    // 销毁图表实例
    if (this.complianceChartInstance) this.complianceChartInstance.dispose()
    if (this.riskChartInstance) this.riskChartInstance.dispose()
    if (this.trendChartInstance) this.trendChartInstance.dispose()
    if (this.violationChartInstance) this.violationChartInstance.dispose()
  },
  methods: {
    updateTime() {
      const now = new Date()
      const year = now.getFullYear()
      const month = String(now.getMonth() + 1).padStart(2, '0')
      const day = String(now.getDate()).padStart(2, '0')
      const hours = String(now.getHours()).padStart(2, '0')
      const minutes = String(now.getMinutes()).padStart(2, '0')
      const seconds = String(now.getSeconds()).padStart(2, '0')
      const weekDays = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']
      const weekDay = weekDays[now.getDay()]

      this.currentTime = `${year}-${month}-${day} ${hours}:${minutes}:${seconds} ${weekDay}`
    },
    initCharts() {
      this.initComplianceChart()
      this.initRiskChart()
      this.initTrendChart()
      this.initViolationChart()
    },
    // 合规率统计饼图
    initComplianceChart() {
      this.complianceChartInstance = echarts.init(this.$refs.complianceChart)
      const option = {
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {
          orient: 'vertical',
          right: 10,
          top: 'center',
          textStyle: {
            color: '#fff'
          }
        },
        series: [
          {
            name: '合规状态',
            type: 'pie',
            radius: ['40%', '70%'],
            avoidLabelOverlap: false,
            itemStyle: {
              borderRadius: 10,
              borderColor: '#0f1722',
              borderWidth: 2
            },
            label: {
              show: false,
              position: 'center'
            },
            emphasis: {
              label: {
                show: true,
                fontSize: 20,
                fontWeight: 'bold',
                color: '#fff'
              }
            },
            labelLine: {
              show: false
            },
            data: [
              { value: 1095, name: '完全合规', itemStyle: { color: '#67C23A' } },
              { value: 98, name: '基本合规', itemStyle: { color: '#E6A23C' } },
              { value: 55, name: '不合规', itemStyle: { color: '#F56C6C' } }
            ]
          }
        ]
      }
      this.complianceChartInstance.setOption(option)
    },
    // 风险等级分布图
    initRiskChart() {
      this.riskChartInstance = echarts.init(this.$refs.riskChart)
      const option = {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'value',
          axisLabel: {
            color: '#8c9db5'
          },
          splitLine: {
            lineStyle: {
              color: '#1a2332'
            }
          }
        },
        yAxis: {
          type: 'category',
          data: ['高风险', '中风险', '低风险', '无风险'],
          axisLabel: {
            color: '#8c9db5'
          },
          splitLine: {
            show: false
          }
        },
        series: [
          {
            name: '应用数量',
            type: 'bar',
            data: [
              { value: 55, itemStyle: { color: '#F56C6C' } },
              { value: 98, itemStyle: { color: '#E6A23C' } },
              { value: 523, itemStyle: { color: '#409EFF' } },
              { value: 572, itemStyle: { color: '#67C23A' } }
            ],
            barWidth: '60%',
            itemStyle: {
              borderRadius: [0, 5, 5, 0]
            }
          }
        ]
      }
      this.riskChartInstance.setOption(option)
    },
    // 检测趋势折线图
    initTrendChart() {
      this.trendChartInstance = echarts.init(this.$refs.trendChart)
      const dates = []
      const checkData = []
      const passData = []

      // 生成近30天数据
      for (let i = 29; i >= 0; i--) {
        const date = new Date()
        date.setDate(date.getDate() - i)
        dates.push(`${date.getMonth() + 1}/${date.getDate()}`)
        checkData.push(Math.floor(Math.random() * 50 + 50))
        passData.push(Math.floor(Math.random() * 40 + 40))
      }

      const option = {
        tooltip: {
          trigger: 'axis'
        },
        legend: {
          data: ['检测总数', '合规数量'],
          textStyle: {
            color: '#fff'
          },
          top: 10
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          top: '15%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: dates,
          axisLabel: {
            color: '#8c9db5',
            interval: 4
          },
          splitLine: {
            show: false
          }
        },
        yAxis: {
          type: 'value',
          axisLabel: {
            color: '#8c9db5'
          },
          splitLine: {
            lineStyle: {
              color: '#1a2332'
            }
          }
        },
        series: [
          {
            name: '检测总数',
            type: 'line',
            smooth: true,
            data: checkData,
            itemStyle: {
              color: '#409EFF'
            },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(64, 158, 255, 0.5)' },
                { offset: 1, color: 'rgba(64, 158, 255, 0.1)' }
              ])
            }
          },
          {
            name: '合规数量',
            type: 'line',
            smooth: true,
            data: passData,
            itemStyle: {
              color: '#67C23A'
            },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(103, 194, 58, 0.5)' },
                { offset: 1, color: 'rgba(103, 194, 58, 0.1)' }
              ])
            }
          }
        ]
      }
      this.trendChartInstance.setOption(option)
    },
    // 违规类型柱状图
    initViolationChart() {
      this.violationChartInstance = echarts.init(this.$refs.violationChart)
      const option = {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: ['未经同意\n收集信息', '超范围\n收集信息', '强制授权', '未明示\n隐私政策', '未提供\n注销功能'],
          axisLabel: {
            color: '#8c9db5',
            interval: 0,
            fontSize: 11
          },
          splitLine: {
            show: false
          }
        },
        yAxis: {
          type: 'value',
          axisLabel: {
            color: '#8c9db5'
          },
          splitLine: {
            lineStyle: {
              color: '#1a2332'
            }
          }
        },
        series: [
          {
            name: '违规次数',
            type: 'bar',
            data: [
              { value: 156, itemStyle: { color: '#F56C6C' } },
              { value: 132, itemStyle: { color: '#E6A23C' } },
              { value: 98, itemStyle: { color: '#409EFF' } },
              { value: 87, itemStyle: { color: '#9C27B0' } },
              { value: 65, itemStyle: { color: '#00BCD4' } }
            ],
            barWidth: '50%',
            itemStyle: {
              borderRadius: [5, 5, 0, 0]
            }
          }
        ]
      }
      this.violationChartInstance.setOption(option)
    },
    handleResize() {
      if (this.complianceChartInstance) this.complianceChartInstance.resize()
      if (this.riskChartInstance) this.riskChartInstance.resize()
      if (this.trendChartInstance) this.trendChartInstance.resize()
      if (this.violationChartInstance) this.violationChartInstance.resize()
    },
    getRiskType(level) {
      const typeMap = {
        '无风险': 'success',
        '低风险': 'info',
        '中风险': 'warning',
        '高风险': 'danger'
      }
      return typeMap[level] || 'info'
    },
    viewDetail(row) {
      this.$message.success('查看详情功能开发中...')
    },
    downloadReport(row) {
      this.$message.success('下载报告功能开发中...')
    }
  }
}
</script>

<style lang="scss" scoped>
.privacy-dashboard {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f1722 0%, #1a2332 100%);
  padding: 20px;
  color: #fff;

  // 顶部标题区
  .dashboard-header {
    background: linear-gradient(135deg, #1e3a5f 0%, #2c5282 100%);
    border-radius: 10px;
    padding: 20px 30px;
    margin-bottom: 20px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);

    .header-content {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .title-wrapper {
        .main-title {
          font-size: 32px;
          font-weight: bold;
          background: linear-gradient(90deg, #fff 0%, #64b5f6 100%);
          background-clip: text;
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          margin-bottom: 8px;

          i {
            margin-right: 12px;
            color: #64b5f6;
          }
        }

        .sub-title {
          font-size: 14px;
          color: #b0bec5;
          letter-spacing: 1px;
        }
      }

      .current-time {
        font-size: 18px;
        color: #90caf9;
        font-family: 'Courier New', monospace;
        font-weight: 500;
      }
    }
  }

  // 数据概览卡片
  .overview-section {
    margin-bottom: 20px;

    .stat-card {
      background: linear-gradient(135deg, #1e3a5f 0%, #2c5282 100%);
      border-radius: 10px;
      padding: 20px;
      display: flex;
      align-items: center;
      transition: all 0.3s ease;
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.2);

      &:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
      }

      &.card-0 { border-left: 4px solid #409EFF; }
      &.card-1 { border-left: 4px solid #67C23A; }
      &.card-2 { border-left: 4px solid #E6A23C; }
      &.card-3 { border-left: 4px solid #F56C6C; }

      .card-icon {
        width: 60px;
        height: 60px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 20px;
        font-size: 28px;

        i {
          background: linear-gradient(135deg, #64b5f6 0%, #42a5f5 100%);
          background-clip: text;
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }
      }

      .card-content {
        flex: 1;

        .card-value {
          font-size: 28px;
          font-weight: bold;
          color: #fff;
          margin-bottom: 5px;
        }

        .card-label {
          font-size: 14px;
          color: #b0bec5;
          margin-bottom: 8px;
        }

        .card-trend {
          font-size: 12px;
          display: inline-flex;
          align-items: center;
          padding: 2px 8px;
          border-radius: 4px;

          &.up {
            color: #67C23A;
            background: rgba(103, 194, 58, 0.1);
          }

          &.down {
            color: #F56C6C;
            background: rgba(245, 108, 108, 0.1);
          }

          i {
            margin-right: 4px;
          }
        }
      }
    }
  }

  // 图表区域
  .chart-section {
    margin-bottom: 20px;
  }

  .chart-card {
    background: linear-gradient(135deg, #1a2a3a 0%, #1e3a5f 100%);
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.2);

    &.chart-card-large {
      height: calc(100% - 20px);
    }

    .card-header {
      border-bottom: 2px solid #2c5282;
      padding-bottom: 15px;
      margin-bottom: 20px;

      .header-title {
        font-size: 18px;
        font-weight: bold;
        color: #fff;

        i {
          margin-right: 8px;
          color: #64b5f6;
        }
      }
    }

    .card-body {
      .chart-container {
        height: 280px;
      }

      .chart-container-large {
        height: 420px;
      }

      .recent-list {
        max-height: 280px;
        overflow-y: auto;

        &::-webkit-scrollbar {
          width: 6px;
        }

        &::-webkit-scrollbar-thumb {
          background: #2c5282;
          border-radius: 3px;
        }

        .record-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px;
          margin-bottom: 10px;
          background: rgba(44, 82, 130, 0.2);
          border-radius: 6px;
          transition: all 0.3s ease;

          &:hover {
            background: rgba(44, 82, 130, 0.4);
            transform: translateX(5px);
          }

          .record-left {
            .record-name {
              font-size: 14px;
              color: #fff;
              margin-bottom: 5px;
            }

            .record-time {
              font-size: 12px;
              color: #8c9db5;
            }
          }
        }
      }
    }
  }

  // 表格区域
  .table-section {
    ::v-deep .el-table {
      background: transparent;
      color: #fff;

      &::before {
        background-color: transparent;
      }

      tr {
        background-color: transparent;
      }

      th, td {
        border-bottom: 1px solid #2c5282;
      }

      .el-table__body tr:hover > td {
        background-color: rgba(44, 82, 130, 0.3);
      }

      .el-button--text {
        color: #64b5f6;
      }
    }
  }
}

// 响应式适配
@media screen and (max-width: 768px) {
  .privacy-dashboard {
    padding: 10px;

    .dashboard-header {
      padding: 15px;

      .header-content {
        flex-direction: column;
        align-items: flex-start;

        .title-wrapper .main-title {
          font-size: 24px;
        }

        .current-time {
          margin-top: 10px;
          font-size: 14px;
        }
      }
    }

    .stat-card {
      margin-bottom: 15px;

      .card-icon {
        width: 50px;
        height: 50px;
        font-size: 24px;
      }

      .card-content .card-value {
        font-size: 24px;
      }
    }
  }
}
</style>
