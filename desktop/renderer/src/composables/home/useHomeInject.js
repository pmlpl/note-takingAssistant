import { inject } from 'vue'
import { HOME_PAGE_KEY } from './useHomePage'

export function useHomeInject() {
  const ctx = inject(HOME_PAGE_KEY)
  if (!ctx) {
    throw new Error('useHomeInject() must be used under Home view')
  }
  return ctx
}
