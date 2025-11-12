<script setup lang="tsx">
import { reactive, ref, unref, watch } from 'vue'
import { getMenuListApi, createMenuApi, updateMenuApi, deleteMenuApi } from '@/api/menu'
import { useTable } from '@/hooks/web/useTable'
import { useI18n } from '@/hooks/web/useI18n'
import { Table, TableColumn } from '@/components/Table'
import { ElMessage, ElMessageBox, ElTag } from 'element-plus'
import { Icon } from '@/components/Icon'
import { Search } from '@/components/Search'
import { FormSchema } from '@/components/Form'
import { ContentWrap } from '@/components/ContentWrap'
import Write from './components/Write.vue'
import Detail from './components/Detail.vue'
import { Dialog } from '@/components/Dialog'
import { BaseButton } from '@/components/Button'
import { cloneDeep } from 'lodash-es'

const { t } = useI18n()

const { tableRegister, tableState, tableMethods } = useTable({
  fetchDataApi: async () => {
    const res = await getMenuListApi()
    return {
      list: res.data.list || []
    }
  }
})

const { dataList, loading } = tableState
const { getList } = tableMethods

const tableColumns = reactive<TableColumn[]>([
  {
    field: 'index',
    label: t('userDemo.index'),
    type: 'index'
  },
  {
    field: 'meta.title',
    label: t('menu.menuName'),
    slots: {
      default: (data: any) => {
        const title = data.row.meta.title
        return <>{title}</>
      }
    }
  },
  {
    field: 'meta.icon',
    label: t('menu.icon'),
    slots: {
      default: (data: any) => {
        const icon = data.row.meta.icon
        if (icon) {
          return (
            <>
              <Icon icon={icon} />
            </>
          )
        } else {
          return null
        }
      }
    }
  },
  // {
  //   field: 'meta.permission',
  //   label: t('menu.permission'),
  //   slots: {
  //     default: (data: any) => {
  //       const permission = data.row.meta.permission
  //       return permission ? <>{permission.join(', ')}</> : null
  //     }
  //   }
  // },
  {
    field: 'component',
    label: t('menu.component'),
    slots: {
      default: (data: any) => {
        const component = data.row.component
        return <>{component === '#' ? '顶级目录' : component === '##' ? '子目录' : component}</>
      }
    }
  },
  {
    field: 'path',
    label: t('menu.path')
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
    field: 'meta.title',
    label: t('menu.menuName'),
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
const actionType = ref('')
const dialogKey = ref(0)

const writeRef = ref<ComponentRef<typeof Write>>()

const saveLoading = ref(false)

const menuMap = ref(new Map<number, any>())
const buildMenuMap = (list: any[] = []) => {
  const map = new Map<number, any>()
  const walk = (nodes: any[]) => {
    nodes?.forEach((node: any) => {
      map.set(node.id, node)
      if (node.children?.length) {
        walk(node.children)
      }
    })
  }
  walk(list)
  return map
}

watch(
  () => dataList.value,
  (val) => {
    menuMap.value = buildMenuMap(val || [])
  },
  { deep: true, immediate: true }
)

const formatRow = (row: any) => {
  const parent = row.parentId ? menuMap.value.get(row.parentId) : null
  return {
    ...row,
    parentName: parent?.meta?.title ?? '-'
  }
}

const AddAction = () => {
  dialogTitle.value = t('exampleDemo.add')
  dialogVisible.value = true
  actionType.value = 'add'
  dialogKey.value++
  currentRow.value = {
    type: 0,
    parentId: null,
    component: '#',
    name: '',
    path: '',
    status: 1,
    meta: {
      title: '',
      icon: '',
      alwaysShow: false,
      noCache: false,
      breadcrumb: true,
      affix: false,
      noTagsView: false,
      canTo: false,
      hidden: false,
      activeMenu: ''
    },
    permissionList: []
  }
}

const action = (row: any, type: string) => {
  dialogTitle.value = t(type === 'edit' ? 'exampleDemo.edit' : 'exampleDemo.detail')
  actionType.value = type
  currentRow.value = formatRow(cloneDeep(row))
  dialogVisible.value = true
  dialogKey.value++
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(t('common.deleteConfirm'), t('common.reminder'), {
      type: 'warning'
    })
  } catch {
    return
  }

  let forceDelete = false
  try {
    await ElMessageBox.confirm(
      t('menu.deleteChildrenConfirm'),
      t('menu.deleteChildrenTitle'),
      {
        type: 'warning',
        confirmButtonText: t('menu.deleteChildrenOk'),
        cancelButtonText: t('menu.deleteChildrenCancel'),
        distinguishCancelAndClose: true
      }
    )
    forceDelete = true
  } catch (action) {
    if (action !== 'cancel') {
      return
    }
  }

  try {
    await deleteMenuApi(row.id, { force: forceDelete })
    ElMessage.success(t('common.delSuccess'))
    await getList()
  } catch (error: any) {
    console.log(error)
    const detail = error?.response?.data?.detail
    if (!forceDelete && detail === 'Please remove child menus first') {
      ElMessage.warning(t('menu.deleteNeedCascade'))
    }
  }
}

const transformMenuPayload = (formData: any) => {
  const meta = formData.meta || {}
  return {
    type: formData.type ?? 0,
    parentId: formData.parentId ?? null,
    name: formData.name,
    component: formData.component,
    path: formData.path,
    redirect: formData.redirect || null,
    status: formData.status ?? 1,
    meta: {
      title: meta.title,
      icon: meta.icon || null,
      alwaysShow: !!meta.alwaysShow,
      noCache: !!meta.noCache,
      breadcrumb: meta.breadcrumb ?? true,
      affix: !!meta.affix,
      noTagsView: !!meta.noTagsView,
      canTo: !!meta.canTo,
      hidden: !!meta.hidden,
      activeMenu: meta.activeMenu || null
    },
    permissionList: (formData.permissionList || []).map((item: any) => ({
      id: item.id,
      label: item.label,
      value: item.value
    }))
  }
}

const save = async () => {
  const write = unref(writeRef)
  const formData = await write?.submit()
  if (formData) {
    saveLoading.value = true
    try {
      const payload = transformMenuPayload(formData)
      if (actionType.value === 'edit' && currentRow.value?.id) {
        await updateMenuApi(currentRow.value.id, payload)
      } else {
        await createMenuApi(payload)
      }
      ElMessage.success(t('common.saveSuccess'))
      dialogVisible.value = false
      await getList()
    } finally {
      saveLoading.value = false
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
      @register="tableRegister"
    />
  </ContentWrap>

  <Dialog v-model="dialogVisible" :title="dialogTitle">
    <Write v-if="actionType !== 'detail'" ref="writeRef" :current-row="currentRow" :key="dialogKey" />

    <Detail v-if="actionType === 'detail'" :current-row="currentRow" />

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
