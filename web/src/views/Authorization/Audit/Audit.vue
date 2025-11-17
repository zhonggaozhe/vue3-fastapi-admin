<script setup lang="tsx">
import { reactive, ref, unref } from 'vue'
import { Table, type TableColumn } from '@/components/Table'
import { ContentWrap } from '@/components/ContentWrap'
import { Search } from '@/components/Search'
import type { FormSchema } from '@/components/Form'
import { useTable } from '@/hooks/web/useTable'
import { getAuditLogListApi, type AuditLogItem, type AuditLogListParams } from '@/api/audit'
import { ElButton, ElTag } from 'element-plus'
import Detail from './components/Detail.vue'
import { formatTime } from '@/utils'

defineOptions({ name: 'AuthorizationAudit' })

const detailRef = ref<ComponentRef<typeof Detail>>()
const searchParams = ref<Partial<AuditLogListParams>>({})

const { tableRegister, tableState, tableMethods } = useTable({
  fetchDataApi: async () => {
    const { currentPage, pageSize } = tableState
    const params: AuditLogListParams = {
      page: unref(currentPage),
      page_size: unref(pageSize),
      ...unref(searchParams)
    }
    const response = await getAuditLogListApi({ params }).catch(() => undefined)
    const data = response?.data ?? { list: [], total: 0 }
    return {
      list: Array.isArray(data.list) ? data.list : [],
      total: Number.isFinite(data.total) ? data.total : 0
    }
  }
})

const { dataList, loading, total, currentPage } = tableState
const { getList } = tableMethods

const normalizeSearchParams = (params: Record<string, any>) => {
  const next = { ...(params || {}) }
  const range: [string, string] | undefined = next.dateRange
  if (range && range.length === 2) {
    next.start_time = range[0]
    next.end_time = range[1]
  } else {
    next.start_time = undefined
    next.end_time = undefined
  }
  delete next.dateRange
  return next
}

const setSearchParams = (params: Record<string, any>) => {
  searchParams.value = normalizeSearchParams(params)
  currentPage.value = 1
  getList()
}

const tableColumns = reactive<TableColumn[]>([
  {
    field: 'id',
    label: 'ID',
    width: 80
  },
  {
    field: 'operator_name',
    label: '操作者',
    minWidth: 160,
    slots: {
      default: ({ row }) => {
        if (!row) return null
        return (
          <div>
            <div>{row.operator_name || '-'}</div>
            {row.operator_id ? (
              <div class="text-xs text-gray-400">ID: {row.operator_id}</div>
            ) : null}
          </div>
        )
      }
    }
  },
  {
    field: 'action',
    label: '操作类型',
    minWidth: 180
  },
  {
    field: 'resource_type',
    label: '资源类型',
    minWidth: 140
  },
  {
    field: 'resource_id',
    label: '资源ID',
    minWidth: 160
  },
  {
    field: 'result_status',
    label: '操作结果',
    width: 140,
    slots: {
      default: ({ row }) => {
        if (!row) return null
        return (
          <ElTag type={row.result_status === 1 ? 'success' : 'danger'}>
            {row.result_status === 1 ? '成功' : '失败'}
          </ElTag>
        )
      }
    }
  },
  {
    field: 'request_ip',
    label: '操作IP',
    minWidth: 160
  },
  {
    field: 'created_at',
    label: '操作时间',
    minWidth: 200,
    formatter: (_row, _column, cellValue) =>
      cellValue ? formatTime(cellValue, 'yyyy-MM-dd HH:mm:ss') : '-'
  },
  {
    field: 'actionSlot',
    label: '操作',
    width: 140,
    fixed: 'right',
    slots: {
      default: ({ row }) => {
        if (!row) return null
        return (
          <ElButton link type="primary" onClick={() => openDetail(row)}>
            详情
          </ElButton>
        )
      }
    }
  }
])

const searchSchema = reactive<FormSchema[]>([
  {
    field: 'operator_id',
    label: '操作者ID',
    component: 'Input'
  },
  {
    field: 'operator_name',
    label: '操作者名称',
    component: 'Input'
  },
  {
    field: 'action',
    label: '操作类型',
    component: 'Input'
  },
  {
    field: 'resource_type',
    label: '资源类型',
    component: 'Input'
  },
  {
    field: 'result_status',
    label: '操作结果',
    component: 'Select',
    componentProps: {
      options: [
        { label: '成功', value: 1 },
        { label: '失败', value: 0 }
      ],
      clearable: true,
      style: { width: '100%' }
    }
  },
  {
    field: 'dateRange',
    label: '操作时间',
    component: 'DatePicker',
    componentProps: {
      type: 'datetimerange',
      valueFormat: 'YYYY-MM-DD HH:mm:ss',
      startPlaceholder: '开始时间',
      endPlaceholder: '结束时间',
      defaultTime: [new Date('2000-01-01 00:00:00'), new Date('2000-01-01 23:59:59')]
    }
  }
])

const openDetail = (row: AuditLogItem) => {
  detailRef.value?.open(row)
}
</script>

<template>
  <ContentWrap>
    <Search :schema="searchSchema" @search="setSearchParams" @reset="setSearchParams" />
    <Table
      :columns="tableColumns"
      :data="dataList"
      :loading="loading"
      :pagination="{ total }"
      @register="tableRegister"
    />
  </ContentWrap>

  <Detail ref="detailRef" />
</template>
