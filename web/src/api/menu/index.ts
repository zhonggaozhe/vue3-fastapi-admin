import request from '@/axios'

export const getMenuListApi = () => {
  return request.get({ url: '/menus/list' })
}

export const createMenuApi = (data: any) => {
  return request.post({ url: '/menus/save', data })
}

export const updateMenuApi = (id: number, data: any) => {
  return request.post({ url: '/menus/edit', data: { ...data, id } })
}

export const deleteMenuApi = (id: number, options?: { force?: boolean }) => {
  const data: Record<string, any> = { ids: [id] }
  if (options?.force) {
    data.force = true
  }
  return request.post({
    url: '/menus/del',
    data
  })
}

export const getMenuDetailApi = (id: number) => {
  return request.get({ url: `/menus/${id}` })
}

export const createMenuPermissionApi = (menuId: number, data: { label: string; value: string }) => {
  return request.post({ url: `/menus/${menuId}/actions`, data })
}

export const updateMenuPermissionApi = (
  menuId: number,
  actionId: number,
  data: { label: string; value: string }
) => {
  return request.put({ url: `/menus/${menuId}/actions/${actionId}`, data })
}

export const deleteMenuPermissionApi = (menuId: number, actionId: number) => {
  return request.delete({ url: `/menus/${menuId}/actions/${actionId}` })
}
