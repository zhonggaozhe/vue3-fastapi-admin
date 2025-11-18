import { useI18n } from '@/hooks/web/useI18n'
import router from '@/router'
import { useUserStoreWithOut } from '@/store/modules/user'

const resolvePermissions = () => {
  const routePermission = (router.currentRoute.value.meta.permission || []) as string[]
  const userStore = useUserStoreWithOut()
  const userPermissions = (userStore.getUserInfo?.permissions || []) as string[]
  return new Set<string>([...routePermission, ...userPermissions])
}

export const hasPermi = (value: string) => {
  const { t } = useI18n()
  if (!value) {
    throw new Error(t('permission.hasPermission'))
  }
  return resolvePermissions().has(value)
}
