import { formatTime } from '@/utils'

type TableFormatter = (row: Recordable, column: Recordable, cellValue: any, index: number) => string

export const dateFormatter: TableFormatter = (_, __, cellValue) => {
  if (!cellValue) {
    return ''
  }
  return formatTime(cellValue, 'yyyy-MM-dd HH:mm:ss')
}
