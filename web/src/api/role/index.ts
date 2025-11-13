import request from '@/axios'

export const getRoleListApi = () => {
  return request.get({ url: '/roles/list' })
}

export const createRoleApi = (data: any) => {
  return request.post({ url: '/roles', data })
}

export const updateRoleApi = (id: number, data: any) => {
  return request.put({ url: `/roles/${id}`, data })
}

export const deleteRoleApi = (id: number) => {
  return request.delete({ url: `/roles/${id}` })
}
