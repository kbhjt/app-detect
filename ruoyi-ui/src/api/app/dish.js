import request from '@/utils/request'

// 查询菜品管理列表
export function listDish(query) {
  return request({
    url: '/app/dish/list',
    method: 'get',
    params: query
  })
}

// 查询菜品管理详细
export function getDish(id) {
  return request({
    url: '/app/dish/' + id,
    method: 'get'
  })
}

// 新增菜品管理
export function addDish(data) {
  return request({
    url: '/app/dish',
    method: 'post',
    data: data
  })
}

// 修改菜品管理
export function updateDish(data) {
  return request({
    url: '/app/dish',
    method: 'put',
    data: data
  })
}

// 删除菜品管理
export function delDish(id) {
  return request({
    url: '/app/dish/' + id,
    method: 'delete'
  })
}
