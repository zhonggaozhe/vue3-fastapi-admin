<template>
  <Dialog :title="dialogTitle" v-model="dialogVisible" width="800px">
    <el-descriptions :column="2" border v-if="formData">
      <el-descriptions-item label="ID">{{ formData.id }}</el-descriptions-item>
      <el-descriptions-item label="链路ID">{{ formData.trace_id }}</el-descriptions-item>
      <el-descriptions-item label="操作者ID">
        {{ formData.operator_id || '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="操作者名称">
        {{ formData.operator_name || '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="操作类型" :span="2">
        <el-tag>{{ formData.action }}</el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="资源类型">
        {{ formData.resource_type || '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="资源ID">{{ formData.resource_id || '-' }}</el-descriptions-item>
      <el-descriptions-item label="操作结果" :span="2">
        <el-tag :type="formData.result_status === 1 ? 'success' : 'danger'">
          {{ formData.result_status === 1 ? '成功' : '失败' }}
        </el-tag>
        <span v-if="formData.result_message" class="ml-2 text-red-500">
          {{ formData.result_message }}
        </span>
      </el-descriptions-item>
      <el-descriptions-item label="操作IP">{{ formData.request_ip || '-' }}</el-descriptions-item>
      <el-descriptions-item label="操作时间">{{ formData.created_at }}</el-descriptions-item>
      <el-descriptions-item label="User Agent" :span="2">
        <div class="text-xs text-gray-500 break-all">{{ formData.user_agent || '-' }}</div>
      </el-descriptions-item>
      <el-descriptions-item label="请求参数" :span="2" v-if="formData.params">
        <pre class="json-preview">{{ JSON.stringify(formData.params, null, 2) }}</pre>
      </el-descriptions-item>
      <el-descriptions-item label="变更前状态" :span="2" v-if="formData.before_state">
        <pre class="json-preview">{{ JSON.stringify(formData.before_state, null, 2) }}</pre>
      </el-descriptions-item>
      <el-descriptions-item label="变更后状态" :span="2" v-if="formData.after_state">
        <pre class="json-preview">{{ JSON.stringify(formData.after_state, null, 2) }}</pre>
      </el-descriptions-item>
    </el-descriptions>
    <template #footer>
      <el-button @click="dialogVisible = false">关闭</el-button>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElButton, ElDescriptions, ElDescriptionsItem, ElTag } from 'element-plus'
import { Dialog } from '@/components/Dialog'
import type { AuditLogItem } from '@/api/audit'

defineOptions({ name: 'AuditDetail' })

const dialogVisible = ref(false) // 弹窗的是否展示
const dialogTitle = ref('审计日志详情') // 弹窗的标题
const formData = ref<AuditLogItem | null>(null)

/** 打开弹窗 */
const open = (row: AuditLogItem) => {
  formData.value = row
  dialogVisible.value = true
}

defineExpose({ open })
</script>

<style scoped>
.json-preview {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  max-height: 300px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
