<script setup lang="tsx">
import { Form, FormSchema } from '@/components/Form'
import { useForm } from '@/hooks/web/useForm'
import { PropType, reactive, watch, ref, unref, nextTick } from 'vue'
import { useValidator } from '@/hooks/web/useValidator'
import { useI18n } from '@/hooks/web/useI18n'
import { ElTree, ElCheckboxGroup, ElCheckbox } from 'element-plus'
import { getMenuListApi } from '@/api/menu'
import { eachTree } from '@/utils/tree'
import { findIndex } from '@/utils'

const { t } = useI18n()

const { required } = useValidator()

const props = defineProps({
  currentRow: {
    type: Object as PropType<any>,
    default: () => null
  }
})

const treeRef = ref<typeof ElTree>()

const formSchema = ref<FormSchema[]>([
  {
    field: 'roleName',
    label: t('role.roleName'),
    component: 'Input'
  },
  {
    field: 'role',
    label: t('role.role'),
    component: 'Input'
  },
  {
    field: 'status',
    label: t('menu.status'),
    component: 'Select',
    componentProps: {
      options: [
        {
          label: t('userDemo.disable'),
          value: 0
        },
        {
          label: t('userDemo.enable'),
          value: 1
        }
      ]
    }
  },
  {
    field: 'remark',
    label: t('userDemo.remark'),
    component: 'Input',
    componentProps: {
      type: 'textarea',
      rows: 3
    }
  },
  {
    field: 'menu',
    label: t('role.menu'),
    colProps: {
      span: 24
    },
    formItemProps: {
      slots: {
        default: () => {
          return (
            <>
              <div class="flex w-full">
                <div class="flex-1">
                  <ElTree
                    ref={treeRef}
                    show-checkbox
                    node-key="id"
                    highlight-current
                    expand-on-click-node={false}
                    data={treeData.value}
                    onNode-click={nodeClick}
                  >
                    {{
                      default: (data) => {
                        return <span>{data.data.meta.title}</span>
                      }
                    }}
                  </ElTree>
                </div>
                <div class="flex-1">
                  {unref(currentTreeData) && unref(currentTreeData)?.permissionList ? (
                    <ElCheckboxGroup v-model={unref(currentTreeData).meta.permissionIds}>
                      {unref(currentTreeData)?.permissionList.map((v: any) => {
                        if (v.id === undefined || v.id === null) {
                          return null
                        }
                        return (
                          <ElCheckbox label={Number(v.id)}>
                            <span>{v.label}</span>
                            <span class="ml-8px text-12px text-[#909399]">({v.value})</span>
                          </ElCheckbox>
                        )
                      })}
                    </ElCheckboxGroup>
                  ) : null}
                </div>
              </div>
            </>
          )
        }
      }
    }
  }
])

const currentTreeData = ref()
const nodeClick = (treeData: any) => {
  currentTreeData.value = treeData
}

const rules = reactive({
  roleName: [required()],
  role: [required()],
  status: [required()]
})

const { formRegister, formMethods } = useForm()
const { setValues, getFormData, getElFormExpose } = formMethods

const treeData = ref([])
const nodeMap = ref(new Map<number, any>())

const buildNodeMap = (list: any[]) => {
  const map = new Map<number, any>()
  eachTree(list, (node: any) => {
    map.set(node.id, node)
  })
  nodeMap.value = map
}

const applyCurrentMenus = async (currentRow?: any) => {
  if (!currentRow || !currentRow.menu || !treeData.value.length) {
    unref(treeRef)?.setCheckedKeys([], false)
    return
  }
  ensurePermissionIds(currentRow.menu)
  const checked: any[] = []
  eachTree(currentRow.menu, (v) => {
    checked.push({
      id: v.id,
      permissionIds: v.meta?.permissionIds || [],
      permissionCodes: v.meta?.permission || []
    })
  })

  eachTree(treeData.value, (node) => {
    const index = findIndex(checked, (item) => item.id === node.id)
    if (index > -1) {
      const meta = { ...(node.meta || {}) }
      const selectedIds = checked[index].permissionIds || []
      if (selectedIds.length) {
        meta.permissionIds = selectedIds
      } else if (checked[index].permissionCodes?.length && node.permissionList?.length) {
        const lookup = new Map<number | string, number>()
        node.permissionList.forEach((perm: any) => {
          if (perm?.value && perm?.id !== undefined) {
            lookup.set(perm.value, Number(perm.id))
          }
        })
        meta.permissionIds = checked[index].permissionCodes
          .map((code: string) => lookup.get(code))
          .filter((id: any) => typeof id === 'number') as number[]
      } else {
        meta.permissionIds = []
      }
      node.meta = meta
    }
  })

  await nextTick()
  const tree = unref(treeRef)
  tree?.setCheckedKeys([], false)
  checked.forEach((item) => {
    tree?.setChecked(item.id, true, false)
  })
}

const ensurePermissionIds = (menus: any[]) => {
  eachTree(menus, (node: any) => {
    const meta = node.meta || {}
    if (!Array.isArray(meta.permissionIds)) {
      meta.permissionIds = []
    }
    node.meta = meta
  })
}

const getMenuList = async () => {
  const res = await getMenuListApi()
  if (res) {
    treeData.value = res.data.list
    ensurePermissionIds(treeData.value)
    buildNodeMap(treeData.value)
    await applyCurrentMenus(props.currentRow || undefined)
  }
}

getMenuList()

const submit = async () => {
  const elForm = await getElFormExpose()
  const valid = await elForm?.validate().catch((err) => {
    console.log(err)
  })
  if (valid) {
    const formData = await getFormData()
    const tree = unref(treeRef)
    const checkedKeys = tree
      ? [...(tree.getCheckedKeys?.() || []), ...(tree.getHalfCheckedKeys?.() || [])]
      : []
    const normalizedKeys = checkedKeys.map((id: string | number) => Number(id))
    const selectedMenus = normalizedKeys.map((id) => nodeMap.value.get(id)).filter(Boolean)
    formData.menu = selectedMenus || []
    return formData
  }
}

watch(
  () => props.currentRow,
  (currentRow) => {
    if (!currentRow) return
    setValues(currentRow)
    applyCurrentMenus(currentRow)
  },
  {
    deep: true,
    immediate: true
  }
)

defineExpose({
  submit
})
</script>

<template>
  <Form :rules="rules" @register="formRegister" :schema="formSchema" />
</template>
