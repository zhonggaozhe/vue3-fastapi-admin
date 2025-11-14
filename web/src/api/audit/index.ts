import request from '@/axios'
import type { AxiosConfig } from '@/axios/types'

export interface AuditLogItem {
  id: number
  trace_id: string
  operator_id: number | null
  operator_name: string | null
  action: string
  resource_type: string | null
  resource_id: string | null
  request_ip: string | null
  user_agent: string | null
  before_state: Record<string, any> | null
  after_state: Record<string, any> | null
  params: Record<string, any> | null
  result_status: number
  result_message: string | null
  created_at: string
}

export interface AuditLogListParams {
  operator_id?: number
  operator_name?: string
  action?: string
  resource_type?: string
  resource_id?: string
  result_status?: number
  start_time?: string
  end_time?: string
  page?: number
  page_size?: number
}

export interface AuditLogListResponse {
  list: AuditLogItem[]
  total: number
  page: number
  page_size: number
}

// 获取审计日志列表
export const getAuditLogListApi = ({ params }: AxiosConfig<AuditLogListParams>): Promise<IResponse<AuditLogListResponse>> => {
  return request.get({ url: '/audit/list', params })
}

// 获取审计日志详情
export const getAuditLogDetailApi = (id: number): Promise<IResponse<AuditLogItem>> => {
  return request.get({ url: `/audit/${id}` })
}

