/**
 * Element Plus 按需导入配置
 * 只导入实际使用的组件，减少包体积
 */

// 核心组件（添加所有布局和常用组件）
import { 
  ElButton, 
  ElCard, 
  ElTable, 
  ElTableColumn,
  ElPagination,
  ElInput,
  ElSelect,
  ElOption,
  ElForm,
  ElFormItem,
  ElDialog,
  ElMessage,
  ElMessageBox,
  ElNotification,
  ElLoading,
  ElIcon,
  ElUpload,
  ElDatePicker,
  ElTag,
  ElSwitch,
  ElCheckbox,
  ElCheckboxGroup,
  ElRadio,
  ElRadioGroup,
  ElDropdown,
  ElDropdownMenu,
  ElDropdownItem,
  ElMenu,
  ElMenuItem,
  ElSubMenu,
  ElInputNumber,
  ElTransfer,
  ElCol,
  ElRow,
  ElContainer,
  ElAside,
  ElHeader,
  ElMain,
  ElTooltip,
  ElLink
} from 'element-plus'

// 暂时注释按需导入，使用简化版本
// 按需导入组件（延迟加载）
const asyncComponents = {
  // ElUpload: () => import('element-plus/lib/components/upload'),
  // ElDatePicker: () => import('element-plus/lib/components/date-picker'),
  // ElTransfer: () => import('element-plus/lib/components/transfer'),
  // ElTag: () => import('element-plus/lib/components/tag'),
  // ElSwitch: () => import('element-plus/lib/components/switch'),
  // ElCheckbox: () => import('element-plus/lib/components/checkbox'),
  // ElCheckboxGroup: () => import('element-plus/lib/components/checkbox-group'),
  // ElRadio: () => import('element-plus/lib/components/radio'),
  // ElRadioGroup: () => import('element-plus/lib/components/radio-group'),
  // ElDropdown: () => import('element-plus/lib/components/dropdown'),
  // ElDropdownMenu: () => import('element-plus/lib/components/dropdown-menu'),
  // ElDropdownItem: () => import('element-plus/lib/components/dropdown-item'),
  // ElMenu: () => import('element-plus/lib/components/menu'),
  // ElMenuItem: () => import('element-plus/lib/components/menu-item'),
  // ElInputNumber: () => import('element-plus/lib/components/input-number')
}

// 核心组件列表
const coreComponents = [
  ElButton,
  ElCard, 
  ElTable,
  ElTableColumn,
  ElPagination,
  ElInput,
  ElSelect,
  ElOption,
  ElForm,
  ElFormItem,
  ElDialog,
  ElIcon,
  ElUpload,
  ElDatePicker,
  ElTag,
  ElSwitch,
  ElCheckbox,
  ElCheckboxGroup,
  ElRadio,
  ElRadioGroup,
  ElDropdown,
  ElDropdownMenu,
  ElDropdownItem,
  ElMenu,
  ElMenuItem,
  ElSubMenu,
  ElInputNumber,
  ElTransfer,
  ElCol,
  ElRow,
  ElContainer,
  ElAside,
  ElHeader,
  ElMain,
  ElTooltip,
  ElLink
]

// 安装核心组件
export const installCoreComponents = (app) => {
  coreComponents.forEach(component => {
    app.component(component.name, component)
  })
  
  // 全局属性
  app.config.globalProperties.$message = ElMessage
  app.config.globalProperties.$messageBox = ElMessageBox
  app.config.globalProperties.$notify = ElNotification
  app.config.globalProperties.$loading = ElLoading.service
}

// 动态加载组件
export const loadComponent = async (componentName) => {
  if (asyncComponents[componentName]) {
    const module = await asyncComponents[componentName]()
    return module.default || module
  }
  return null
}

export default {
  install: installCoreComponents
} 