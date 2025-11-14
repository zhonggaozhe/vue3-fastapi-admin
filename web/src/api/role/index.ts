import request from '@/axios'

export const getRoleListApi = () => {
  return request.get({ url: '/roles/list' })
}

export const createRoleApi = (data: any) => {
  return request.post({ url: '/roles/save', data })
}

export const updateRoleApi = (id: number, data: any) => {
  return request.post({ url: '/roles/edit', data: { ...data, id } })
}

export const deleteRoleApi = (id: number) => {
  return request.post({ url: '/roles/del', data: { ids: [id] } })
}
