<script setup lang="ts">
import { FormSchema, Form } from '@/components/Form'
import { ElDrawer } from 'element-plus'
import { reactive } from 'vue'
import { useForm } from '@/hooks/web/useForm'
import { useValidator } from '@/hooks/web/useValidator'

const modelValue = defineModel<boolean>()

const { required } = useValidator()

const formSchema = reactive<FormSchema[]>([
  {
    field: 'label',
    label: 'Label',
    component: 'Input',
    colProps: {
      span: 24
    }
  },
  {
    field: 'namespace',
    label: 'Namespace',
    component: 'Input',
    value: 'system',
    colProps: {
      span: 24
    }
  },
  {
    field: 'resource',
    label: 'Resource',
    component: 'Input',
    colProps: {
      span: 24
    }
  },
  {
    field: 'action',
    label: 'Action',
    component: 'Input',
    colProps: {
      span: 24
    }
  }
])

const { formRegister, formMethods } = useForm()
const { getFormData, getElFormExpose } = formMethods

const emit = defineEmits(['confirm'])

const rules = reactive({
  label: [required()],
  resource: [required()],
  action: [required()]
})

const confirm = async () => {
  const elFormExpose = await getElFormExpose()
  if (!elFormExpose) return
  const valid = await elFormExpose?.validate().catch((err) => {
    console.log(err)
  })
  if (valid) {
    const formData = await getFormData()
    const namespace = (formData.namespace || 'system').trim()
    const resource = (formData.resource || '').trim()
    const action = (formData.action || '').trim()
    const label = (formData.label || '').trim()
    const value = [namespace, resource, action].join(':')
    emit('confirm', {
      id: Date.now(),
      label,
      value
    })
    modelValue.value = false
  }
}
</script>

<template>
  <ElDrawer v-model="modelValue" title="新增按钮权限">
    <template #default>
      <Form :rules="rules" @register="formRegister" :schema="formSchema" />
    </template>
    <template #footer>
      <div>
        <BaseButton @click="() => (modelValue = false)">取消</BaseButton>
        <BaseButton type="primary" @click="confirm">确认</BaseButton>
      </div>
    </template>
  </ElDrawer>
</template>
