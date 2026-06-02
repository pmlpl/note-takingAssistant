/** 欢迎页 ECharts 手绘风主题（与 assets/style.css 设计令牌一致） */
export const WELCOME_CHART = {
  pencil: '#2d2d2d',
  blue: '#2d5da1',
  yellow: '#fff9c4',
  accent: '#ff4d4d',
  muted: '#e5e0d8',
  paper: '#faf9f6',
  font: "'Patrick Hand', 'ZCOOL KuaiLe', 'Segoe UI', sans-serif",
}

export function baseGrid() {
  return { left: 52, right: 28, top: 44, bottom: 48 }
}

export function axisCategory(dates) {
  return {
    type: 'category',
    data: dates,
    axisLine: { lineStyle: { color: WELCOME_CHART.pencil, width: 2 } },
    axisTick: { show: false },
    axisLabel: { color: '#555', fontFamily: WELCOME_CHART.font, fontSize: 12 },
  }
}

export function axisValue(name) {
  return {
    type: 'value',
    name,
    nameTextStyle: { color: '#666', fontFamily: WELCOME_CHART.font },
    minInterval: 1,
    axisLine: { show: true, lineStyle: { color: WELCOME_CHART.pencil } },
    splitLine: { lineStyle: { type: 'dashed', color: WELCOME_CHART.muted } },
    axisLabel: { color: '#555', fontFamily: WELCOME_CHART.font },
  }
}

export function tooltipAxis() {
  return {
    trigger: 'axis',
    backgroundColor: 'rgba(255,255,255,0.96)',
    borderColor: WELCOME_CHART.pencil,
    borderWidth: 2,
    textStyle: { color: WELCOME_CHART.pencil, fontFamily: WELCOME_CHART.font },
  }
}

export function legendBottom(items) {
  return {
    bottom: 0,
    itemGap: 20,
    textStyle: { fontFamily: WELCOME_CHART.font, color: WELCOME_CHART.pencil },
    data: items,
  }
}
