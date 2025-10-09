import request from '@/utils/request'

// 查询检测任务列表
export function listTask(query) {
  return request({
    url: '/app/task/list',
    method: 'get',
    params: query
  })
}

// 查询检测任务详细
export function getTask(id) {
  return request({
    url: '/app/task/' + id,
    method: 'get'
  })
}

// 新增检测任务
export function addTask(data) {
  return request({
    url: '/app/task',
    method: 'post',
    data: data
  })
}

// 提交检测任务
export function submitTask(data) {
  return request({
    url: '/app/task/submit',
    method: 'post',
    data: data
  })
}

// 上传应用文件
export function uploadApp(data) {
  return request({
    url: '/app/task/upload',
    method: 'post',
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    data: data
  })
}

// URL下载应用
export function downloadAppFromUrl(url) {
  return request({
    url: '/app/task/download',
    method: 'post',
    data: { url }
  })
}

// 获取样本列表
export function getSampleList() {
  return request({
    url: '/app/task/samples',
    method: 'get'
  })
}

// 修改检测任务
export function updateTask(data) {
  return request({
    url: '/app/task',
    method: 'put',
    data: data
  })
}

// 删除检测任务
export function delTask(id) {
  return request({
    url: '/app/task/' + id,
    method: 'delete'
  })
}

// 批量删除检测任务
export function delTasks(ids) {
  return request({
    url: '/app/task/' + ids,
    method: 'delete'
  })
}

// 取消检测任务
export function cancelTask(id) {
  return request({
    url: '/app/task/cancel/' + id,
    method: 'put'
  })
}

// 重启检测任务
export function restartTask(id) {
  return request({
    url: '/app/task/restart/' + id,
    method: 'put'
  })
}

// 下载检测报告
export function downloadReport(id) {
  return request({
    url: '/app/task/report/' + id,
    method: 'get',
    responseType: 'blob'
  })
}

// 导出检测任务列表
export function exportTask(query) {
  return request({
    url: '/app/task/export',
    method: 'get',
    params: query,
    responseType: 'blob'
  })
}

