// ECharts 折线图——四维能力随版本变化趋势，平滑曲线 + 渐变面积填充
import ReactECharts from 'echarts-for-react'
import { useAppStore } from '../../stores/appStore'

const CHART_COLORS = ['#5b7bb5', '#5a9e8f', '#8b7ec8', '#c4944a', '#c47a8b', '#6ba87a']

const DIMENSION_LABELS: Record<string, string> = {
  tech_skills: '技术能力',
  project_exp: '项目经验',
  soft_skills: '软技能',
  domain_knowledge: '领域知识',
}

interface GrowthTrendProps {
  history: { date: string; scores: Record<string, number> }[]
}

const containerStyle: React.CSSProperties = {
  width: '100%',
  height: '100%',
  background: 'transparent',
  borderRadius: 12,
  padding: 16,
  boxSizing: 'border-box',
}

export default function GrowthTrend({ history }: GrowthTrendProps) {
  const { theme } = useAppStore()
  const isDark = theme === 'dark'

  const textColor = isDark ? '#a0a5b5' : '#6e6e73'
  const lineColor = isDark ? '#2c2f3a' : '#e8e5df'
  const gridLineColor = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)'
  const tooltipBg = isDark ? 'rgba(22, 24, 29, 0.95)' : 'rgba(248, 247, 244, 0.95)'
  const tooltipBorder = isDark ? '#2c2f3a' : '#e8e5df'
  const tooltipText = isDark ? '#f5f6f9' : '#1d1d1f'

  const dates = history.map((h) => h.date)
  const scoreKeys = history.length > 0 ? Object.keys(history[0].scores) : []

  const series = scoreKeys.map((key, idx) => ({
    name: DIMENSION_LABELS[key] || key,
    type: 'line' as const,
    // 将 0-1 小数乘以 100，绘制在 0-100 坐标系中
    data: history.map((h) => Math.round((h.scores[key] ?? 0) * 100)),
    smooth: true,
    symbol: 'circle',
    symbolSize: 6,
    lineStyle: {
      color: CHART_COLORS[idx % CHART_COLORS.length],
      width: 2,
    },
    itemStyle: {
      color: CHART_COLORS[idx % CHART_COLORS.length],
    },
    areaStyle: {
      color: {
        type: 'linear' as const,
        x: 0,
        y: 0,
        x2: 0,
        y2: 1,
        colorStops: [
          {
            offset: 0,
            color: CHART_COLORS[idx % CHART_COLORS.length] + '40',
          },
          {
            offset: 1,
            color: CHART_COLORS[idx % CHART_COLORS.length] + '08',
          },
        ],
      },
    },
  }))

  const option = {
    color: CHART_COLORS,
    backgroundColor: 'transparent',
    tooltip: {
      backgroundColor: tooltipBg,
      borderColor: tooltipBorder,
      textStyle: { color: tooltipText, fontSize: 13 },
      trigger: 'axis' as const,
      formatter: (params: any) => {
        if (!Array.isArray(params)) return ''
        const dateIdx = params[0].dataIndex
        const label = dates[dateIdx] || ''
        let html = `<div style="font-weight:600;margin-bottom:6px">${label}</div>`
        params.forEach((p: any) => {
          html += `<div style="display:flex;align-items:center;gap:6px">${p.marker} ${p.seriesName}: <b>${p.value}%</b></div>`
        })
        return html
      },
    },
    legend: {
      bottom: 0,
      textStyle: { color: textColor, fontSize: 12 },
      itemWidth: 16,
      itemHeight: 10,
      itemGap: 20,
      icon: 'roundRect',
    },
    grid: {
      left: 40,
      right: 24,
      top: 16,
      bottom: 44,
      containLabel: false,
    },
    xAxis: {
      type: 'category',
      data: dates,
      boundaryGap: false,
      axisLabel: {
        color: textColor,
        fontSize: 11,
      },
      axisLine: {
        lineStyle: { color: lineColor },
      },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      axisLabel: {
        color: textColor,
        fontSize: 11,
      },
      splitLine: {
        lineStyle: {
          color: gridLineColor,
          type: 'dashed' as const,
        },
      },
      axisLine: { show: false },
    },
    series,
  }

  return (
    <div style={containerStyle}>
      <ReactECharts
        option={option}
        style={{ width: '100%', height: '100%' }}
        opts={{ renderer: 'canvas' }}
      />
    </div>
  )
}
