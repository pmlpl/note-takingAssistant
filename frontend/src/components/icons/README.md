# 自定义图标库

这是 AI笔记助手 项目的专属自定义 SVG 图标库，完全独立于 Element Plus 图标组件。

## 📁 目录结构

```
src/components/icons/
├── BaseIcon.vue          # 基础图标组件（包装器）
├── AppLogo.vue           # 应用 Logo（笔记本 + AI 元素）
├── IconHome.vue          # 首页图标
├── IconDocument.vue      # 文档/笔记图标
├── IconMagic.vue         # AI 魔法图标
├── IconTrend.vue         # 趋势图表图标
├── IconUser.vue          # 用户图标
├── IconEdit.vue          # 编辑图标
├── IconUpload.vue        # 上传/保存图标
├── IconSearch.vue        # 搜索图标
├── IconPlus.vue          # 加号图标
├── IconClock.vue         # 时钟图标
├── IconLogout.vue        # 退出登录图标
└── index.js              # 导出文件
```

## 🎨 设计理念

### 1. **AppLogo - 品牌标识**
- 笔记本造型代表"笔记"功能
- 左侧装订线增加真实感
- 横线模拟纸张纹理
- 右上角星星和光晕体现"AI"智能特性
- 蓝色主题色 (#409eff) 传达科技感

### 2. **功能图标设计原则**
- **简洁明了**：每个图标都能一眼识别其功能
- **视觉一致**：统一的线条粗细、圆角风格
- **细节丰富**：添加高光、阴影等细节提升质感
- **色彩灵活**：支持通过 `color` 属性自定义颜色

## 💡 使用方法

### 基本用法

```vue
<template>
  <IconHome :size="24" color="#409eff" />
</template>

<script setup>
import { IconHome } from '@/components/icons'
</script>
```

### 可用属性

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| size | String/Number | 24 | 图标大小（像素） |
| color | String | 'currentColor' | 图标颜色 |

### 示例

```vue
<!-- 小尺寸图标 -->
<IconHome :size="16" />

<!-- 大尺寸彩色图标 -->
<AppLogo :size="64" color="#67c23a" />

<!-- 继承父元素颜色 -->
<IconUser />
```

## 🎯 图标列表

| 图标名称 | 用途 | 推荐尺寸 |
|---------|------|---------|
| AppLogo | 应用 Logo、品牌展示 | 32-64px |
| IconHome | 首页导航 | 18-24px |
| IconDocument | 笔记、文档相关 | 18-48px |
| IconMagic | AI 生成、智能功能 | 18-48px |
| IconTrend | 统计、趋势分析 | 18-24px |
| IconUser | 用户信息、个人中心 | 18-24px |
| IconEdit | 编辑、修改操作 | 18-24px |
| IconUpload | 保存、上传操作 | 18-24px |
| IconSearch | 搜索功能 | 18-24px |
| IconPlus | 新建、添加操作 | 18-24px |
| IconClock | 时间、历史记录 | 18-32px |
| IconLogout | 退出登录 | 18-24px |

## 🔧 添加新图标

1. 在 `src/components/icons/` 目录下创建新的 `.vue` 文件
2. 使用 `BaseIcon` 作为基础组件
3. 在 `<template>` 中绘制 SVG 图形
4. 在 `index.js` 中导出新图标

### 示例：创建新图标

```vue
<template>
  <BaseIcon :size="size" :color="color">
    <!-- 在这里绘制你的 SVG 图形 -->
    <circle cx="12" cy="12" r="10" fill="currentColor" />
  </BaseIcon>
</template>

<script setup>
import BaseIcon from './BaseIcon.vue'

defineProps({
  size: {
    type: [String, Number],
    default: 24
  },
  color: {
    type: String,
    default: 'currentColor'
  }
})
</script>
```

## ✨ 优势

1. **完全自主可控**：不依赖第三方图标库
2. **体积更小**：只加载实际使用的图标
3. **风格统一**：符合产品整体设计风格
4. **易于定制**：可以轻松修改颜色、大小等属性
5. **SVG 格式**：矢量图形，任意缩放不失真
6. **可访问性好**：语义化标签，支持屏幕阅读器

## 📝 注意事项

- 所有图标都使用 `currentColor`，可以通过 CSS `color` 属性或 `color` prop 改变颜色
- 推荐使用偶数尺寸以获得最佳的渲染效果
- SVG 路径尽量保持简洁，避免过于复杂的图形
- 保持图标的视觉平衡和对齐

---

**最后更新**: 2026-05-08
**维护者**: AI笔记助手开发团队
