import type { App, Directive, DirectiveBinding } from 'vue'
import { useI18n } from '@/hooks/web/useI18n'
import router from '@/router'
import { useUserStoreWithOut } from '@/store/modules/user'

const { t } = useI18n()

const userStore = useUserStoreWithOut()

const resolvePermissionPool = (): Set<string> => {
  const routePermission = (router.currentRoute.value.meta.permission || []) as string[]
  const userPermissions = (userStore.getUserInfo?.permissions || []) as string[]
  return new Set<string>([...routePermission, ...userPermissions])
}

const hasPermission = (value: string): boolean => {
  const permission = resolvePermissionPool()
  if (!value) {
    throw new Error(t('permission.hasPermission'))
  }
  if (permission.has(value)) {
    return true
  }
  return false
}
function hasPermi(el: Element, binding: DirectiveBinding) {
  const value = binding.value

  const flag = hasPermission(value)
  if (!flag) {
    el.parentNode?.removeChild(el)
  }
}
const mounted = (el: Element, binding: DirectiveBinding<any>) => {
  hasPermi(el, binding)
}

const permiDirective: Directive = {
  mounted
}

export const setupPermissionDirective = (app: App<Element>) => {
  app.directive('hasPermi', permiDirective)
}

export default permiDirective
