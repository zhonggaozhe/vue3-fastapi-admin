<script setup lang="ts">
import { propTypes } from '@/utils/propTypes'
import { computed, unref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStoreWithOut } from '@/store/modules/user'

const { currentRoute } = useRouter()
const userStore = useUserStoreWithOut()

const props = defineProps({
  permission: propTypes.string.def()
})

const currentPermission = computed(() => {
  const routePermission = (unref(currentRoute)?.meta?.permission || []) as string[]
  const userPermissions = (userStore.getUserInfo?.permissions || []) as string[]
  return Array.from(new Set([...routePermission, ...userPermissions]))
})

const hasPermission = computed(() => {
  const permission = unref(props.permission)
  if (!permission) {
    return true
  }
  return unref(currentPermission).includes(permission)
})
</script>

<template>
  <template v-if="hasPermission">
    <slot></slot>
  </template>
</template>
