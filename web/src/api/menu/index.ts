import request from '@/axios'

export const getMenuListApi = () => {
  return request.get({ url: '/menus' })
}

export const createMenuApi = (data: any) => {
  return request.post({ url: '/menus', data })
}

export const updateMenuApi = (id: number, data: any) => {
  return request.put({ url: `/menus/${id}`, data })
}

export const deleteMenuApi = (id: number) => {
  return request.delete({ url: `/menus/${id}` })
}

export const getMenuDetailApi = (id: number) => {
  return request.get({ url: `/menus/${id}` })
}
