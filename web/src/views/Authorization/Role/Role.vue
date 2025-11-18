<script setup lang="tsx">
import { reactive, ref, unref } from 'vue'
import { getRoleListApi, createRoleApi, updateRoleApi, deleteRoleApi } from '@/api/role'
import { useTable } from '@/hooks/web/useTable'
import { useI18n } from '@/hooks/web/useI18n'
import { Table, TableColumn } from '@/components/Table'
import { ElMessage, ElMessageBox, ElTag } from 'element-plus'
import { Search } from '@/components/Search'
import { FormSchema } from '@/components/Form'
import { ContentWrap } from '@/components/ContentWrap'
import Write from './components/Write.vue'
import Detail from './components/Detail.vue'
import { Dialog } from '@/components/Dialog'
import { BaseButton } from '@/components/Button'

const { t } = useI18n()

const { tableRegister, tableState, tableMethods } = useTable({
  fetchDataApi: async () => {
    const res = await getRoleListApi()
    return {
      list: res.data.list || [],
      total: res.data.total
    }
  }
})

const { dataList, loading, total } = tableState
const { getList } = tableMethods

const tableColumns = reactive<TableColumn[]>([
  {
    field: 'index',
    label: t('userDemo.index'),
    type: 'index'
  },
  {
    field: 'roleName',
    label: t('role.roleName')
  },
  {
    field: 'status',
    label: t('menu.status'),
    slots: {
      default: (data: any) => {
        return (
          <>
            <ElTag type={data.row.status === 0 ? 'danger' : 'success'}>
              {data.row.status === 1 ? t('userDemo.enable') : t('userDemo.disable')}
            </ElTag>
          </>
        )
      }
    }
  },
  {
    field: 'createTime',
    label: t('tableDemo.displayTime')
  },
  {
    field: 'remark',
    label: t('userDemo.remark')
  },
  {
    field: 'action',
    label: t('userDemo.action'),
    width: 240,
    slots: {
      default: (data: any) => {
        const row = data.row
        return (
          <>
            <BaseButton type="primary" onClick={() => action(row, 'edit')}>
              {t('exampleDemo.edit')}
            </BaseButton>
            <BaseButton type="success" onClick={() => action(row, 'detail')}>
              {t('exampleDemo.detail')}
            </BaseButton>
            <BaseButton type="danger" onClick={() => handleDelete(row)}>
              {t('exampleDemo.del')}
            </BaseButton>
          </>
        )
      }
    }
  }
])

const searchSchema = reactive<FormSchema[]>([
  {
    field: 'roleName',
    label: t('role.roleName'),
    component: 'Input'
  }
])

const searchParams = ref({})
const setSearchParams = (data: any) => {
  searchParams.value = data
  getList()
}

const dialogVisible = ref(false)
const dialogTitle = ref('')

const currentRow = ref()
const actionType = ref<'add' | 'edit' | 'detail'>('add')

const writeRef = ref<ComponentRef<typeof Write>>()

const saveLoading = ref(false)

const action = (row: any, type: 'edit' | 'detail') => {
  dialogTitle.value = t(type === 'edit' ? 'exampleDemo.edit' : 'exampleDemo.detail')
  actionType.value = type
  currentRow.value = row
  dialogVisible.value = true
}

const AddAction = () => {
  dialogTitle.value = t('exampleDemo.add')
  currentRow.value = {
    roleName: '',
    role: '',
    status: 1,
    remark: '',
    menu: []
  }
  dialogVisible.value = true
  actionType.value = 'add'
}

const save = async () => {
  const write = unref(writeRef)
  const formData = await write?.submit()
  if (formData) {
    saveLoading.value = true
    const payload = transformPayload(formData)
    try {
      if (actionType.value === 'edit' && currentRow.value?.id) {
        await updateRoleApi(currentRow.value.id, payload)
        ElMessage.success(t('common.editSuccess'))
      } else {
        await createRoleApi(payload)
        ElMessage.success(t('common.addSuccess'))
      }
      dialogVisible.value = false
      await getList()
    } catch (error: any) {
      const detail = error?.response?.data?.detail
      if (detail === 'ROLE_CODE_OR_NAME_EXISTS') {
        ElMessage.error(t('role.roleExists'))
      }
    } finally {
      saveLoading.value = false
    }
  }
}

const collectPermissionIds = (menus: any[] = []) => {
  const ids = new Set<number>()
  menus.forEach((item: any) => {
    if (!item || item.id === undefined || item.id === null) return
    const selectedIds = Array.isArray(item.meta?.permissionIds) ? item.meta.permissionIds : []
    selectedIds.forEach((id: number | string) => {
      const numericId = Number(id)
      if (!Number.isNaN(numericId)) {
        ids.add(numericId)
      }
    })
  })
  return Array.from(ids)
}

const transformPayload = (formData: any) => {
  const selectedMenus = formData.menu || []
  return {
    roleName: formData.roleName,
    role: formData.role,
    status: formData.status,
    remark: formData.remark,
    menuIds: selectedMenus.map((item: any) => Number(item.id)),
    permissionIds: collectPermissionIds(selectedMenus)
  }
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(t('common.deleteConfirm'), t('common.reminder'), {
      type: 'warning'
    })
  } catch {
    return
  }
  try {
    await deleteRoleApi(row.id)
    ElMessage.success(t('common.delSuccess'))
    await getList()
  } catch (error: any) {
    const detail = error?.response?.data?.detail
    if (detail === 'ROLE_IN_USE') {
      ElMessage.error(t('role.roleInUse'))
    }
  }
}
</script>

<template>
  <ContentWrap>
    <Search :schema="searchSchema" @reset="setSearchParams" @search="setSearchParams" />
    <div class="mb-10px">
      <BaseButton type="primary" @click="AddAction">{{ t('exampleDemo.add') }}</BaseButton>
    </div>
    <Table
      :columns="tableColumns"
      default-expand-all
      node-key="id"
      :data="dataList"
      :loading="loading"
      :pagination="{
        total
      }"
      @register="tableRegister"
    />
  </ContentWrap>

  <Dialog v-model="dialogVisible" :title="dialogTitle">
    <Write v-if="actionType !== 'detail'" ref="writeRef" :current-row="currentRow" />
    <Detail v-else :current-row="currentRow" />

    <template #footer>
      <BaseButton
        v-if="actionType !== 'detail'"
        type="primary"
        :loading="saveLoading"
        @click="save"
      >
        {{ t('exampleDemo.save') }}
      </BaseButton>
      <BaseButton @click="dialogVisible = false">{{ t('dialogDemo.close') }}</BaseButton>
    </template>
  </Dialog>
</template>
