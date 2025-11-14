<template>
  <ContentWrap>
    <!-- 搜索工作栏 -->
    <el-form
      class="-mb-15px"
      :model="queryParams"
      ref="queryFormRef"
      :inline="true"
      label-width="100px"
    >
      <el-form-item label="操作者ID" prop="operator_id">
        <el-input
          v-model="queryParams.operator_id"
          placeholder="请输入操作者ID"
          clearable
          @keyup.enter="handleQuery"
          class="!w-240px"
        />
      </el-form-item>
      <el-form-item label="操作者名称" prop="operator_name">
        <el-input
          v-model="queryParams.operator_name"
          placeholder="请输入操作者名称"
          clearable
          @keyup.enter="handleQuery"
          class="!w-240px"
        />
      </el-form-item>
      <el-form-item label="操作类型" prop="action">
        <el-input
          v-model="queryParams.action"
          placeholder="请输入操作类型"
          clearable
          @keyup.enter="handleQuery"
          class="!w-240px"
        />
      </el-form-item>
      <el-form-item label="资源类型" prop="resource_type">
        <el-input
          v-model="queryParams.resource_type"
          placeholder="请输入资源类型"
          clearable
          @keyup.enter="handleQuery"
          class="!w-240px"
        />
      </el-form-item>
      <el-form-item label="操作结果" prop="result_status">
        <el-select
          v-model="queryParams.result_status"
          placeholder="请选择操作结果"
          clearable
          class="!w-240px"
        >
          <el-option label="成功" :value="1" />
          <el-option label="失败" :value="0" />
        </el-select>
      </el-form-item>
      <el-form-item label="操作时间" prop="dateRange">
        <el-date-picker
          v-model="dateRange"
          type="datetimerange"
          value-format="YYYY-MM-DD HH:mm:ss"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          :default-time="[new Date('2000-01-01 00:00:00'), new Date('2000-01-01 23:59:59')]"
          class="!w-240px"
        />
      </el-form-item>
      <el-form-item>
        <el-button @click="handleQuery">
          <Icon icon="ep:search" class="mr-5px" />
          搜索
        </el-button>
        <el-button @click="resetQuery">
          <Icon icon="ep:refresh" class="mr-5px" />
          重置
        </el-button>
      </el-form-item>
    </el-form>
  </ContentWrap>

  <!-- 列表 -->
  <ContentWrap>
    <el-table v-loading="loading" :data="list" stripe show-overflow-tooltip>
      <el-table-column label="ID" prop="id" width="80" />
      <el-table-column label="操作者" width="120">
        <template #default="{ row }">
          <div>
            <div v-if="row.operator_name">{{ row.operator_name }}</div>
            <div v-else class="text-gray-400">-</div>
            <div v-if="row.operator_id" class="text-xs text-gray-400">ID: {{ row.operator_id }}</div>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="操作类型" prop="action" width="180" />
      <el-table-column label="资源类型" prop="resource_type" width="120" />
      <el-table-column label="资源ID" prop="resource_id" width="120" />
      <el-table-column label="操作结果" prop="result_status" width="100">
        <template #default="{ row }">
          <el-tag :type="row.result_status === 1 ? 'success' : 'danger'">
            {{ row.result_status === 1 ? '成功' : '失败' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作IP" prop="request_ip" width="140" />
      <el-table-column label="操作时间" prop="created_at" width="180" :formatter="dateFormatter" />
      <el-table-column label="操作" fixed="right" width="120">
        <template #default="{ row }">
          <el-button
            link
            type="primary"
            @click="openDetail(row)"
            v-hasPermi="['audit:read']"
          >
            详情
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    <!-- 分页 -->
    <Pagination
      :total="total"
      v-model:page="queryParams.page"
      v-model:limit="queryParams.page_size"
      @pagination="getList"
    />
  </ContentWrap>

  <!-- 详情弹窗 -->
  <Detail ref="detailRef" />
</template>

<script setup lang="ts">
import { dateFormatter } from '@/utils/formatTime'
import { getAuditLogListApi, type AuditLogItem, type AuditLogListParams } from '@/api/audit'
import Detail from './components/Detail.vue'

defineOptions({ name: 'AuthorizationAudit' })

const { t } = useI18n() // 国际化

const loading = ref(true) // 列表的加载中
const list = ref<AuditLogItem[]>([]) // 列表的数据
const total = ref(0) // 列表的总页数
const queryParams = reactive<AuditLogListParams>({
  page: 1,
  page_size: 20
})
const dateRange = ref<[string, string]>()

const queryFormRef = ref() // 搜索的表单
const detailRef = ref() // 详情 Ref

/** 查询列表 */
const getList = async () => {
  loading.value = true
  try {
    // 处理日期范围
    if (dateRange.value && dateRange.value.length === 2) {
      queryParams.start_time = dateRange.value[0]
      queryParams.end_time = dateRange.value[1]
    } else {
      queryParams.start_time = undefined
      queryParams.end_time = undefined
    }

    const data = await getAuditLogListApi({ params: queryParams })
    list.value = data.list
    total.value = data.total
  } finally {
    loading.value = false
  }
}

/** 搜索按钮操作 */
const handleQuery = () => {
  queryParams.page = 1
  getList()
}

/** 重置按钮操作 */
const resetQuery = () => {
  dateRange.value = undefined
  queryFormRef.value.resetFields()
  handleQuery()
}

/** 打开详情弹窗 */
const openDetail = (row: AuditLogItem) => {
  detailRef.value.open(row)
}

/** 初始化 **/
onMounted(() => {
  getList()
})
</script>

