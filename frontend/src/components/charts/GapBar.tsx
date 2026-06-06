// ECharts 横向柱状图——当前值 vs 要求值对比，差距标签标注
import ReactECharts from 'echarts-for-react'
import { useAppStore } from '../../stores/appStore'

interface GapDataItem {
  skill: string
  current: number
  required: number
}

interface GapBarProps {
  data: GapDataItem[]
}

const containerStyle: React.CSSProperties = {
  width: '100%',
  height: '100%',
  background: 'transparent',
  borderRadius: 12,
  padding: 16,
  boxSizing: 'border-box',
}

export default function GapBar({ data }: GapBarProps) {
  const { theme } = useAppStore()
  const isDark = theme === 'dark'

  const textColor = isDark ? '#a0a5b5' : '#6e6e73'
  const lineColor = isDark ? '#2c2f3a' : '#e8e5df'
  const gridLineColor = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)'
  const tooltipBg = isDark ? 'rgba(22, 24, 29, 0.95)' : 'rgba(248, 247, 244, 0.95)'
  const tooltipBorder = isDark ? '#2c2f3a' : '#e8e5df'
  const tooltipText = isDark ? '#f5f6f9' : '#1d1d1f'

  const greenColor = isDark ? '#83bfa0' : '#6ba87a' // accent-green
  const roseColor = isDark ? '#d695a3' : '#c47a8b'   // accent-rose
  const grayColor = isDark ? '#6c7284' : '#aeaeb2'   // text-tertiary

  const skills = data.map((d) => d.skill).reverse()
  const currentValues = data.map((d) => d.current).reverse()
  const requiredValues = data.map((d) => d.required).reverse()
  const gaps = data.map((d) => d.required - d.current).reverse()

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      backgroundColor: tooltipBg,
      borderColor: tooltipBorder,
      textStyle: { color: tooltipText, fontSize: 13 },
      trigger: 'axis' as const,
      axisPointer: { type: 'shadow' as const },
      formatter: (params: any) => {
        if (!Array.isArray(params)) return ''
        const name = params[0].name
        let html = `<div style="font-weight:600;margin-bottom:6px">${name}</div>`
        params.forEach((p: any) => {
          html += `<div style="display:flex;align-items:center;gap:6px">${p.marker} ${p.seriesName}: <b>${p.value}</b></div>`
        })
        const gap = gaps[skills.indexOf(name)]
        if (gap > 0) {
          html += `<div style="color:${roseColor};margin-top:4px">差距: <b>+${gap.toFixed(0)}</b></div>`
        } else if (gap < 0) {
          html += `<div style="color:${greenColor};margin-top:4px">超出: <b>${Math.abs(gap).toFixed(0)}</b></div>`
        } else {
          html += `<div style="color:${grayColor};margin-top:4px">已达标</div>`
        }
        return html
      },
    },
    legend: {
      show: true,
      bottom: 0,
      textStyle: { color: textColor, fontSize: 12 },
      itemWidth: 12,
      itemHeight: 8,
    },
    grid: {
      left: 80,
      right: 70,
      top: 16,
      bottom: 40,
      containLabel: false,
    },
    xAxis: {
      type: 'value',
      max: 100,
      axisLabel: {
        color: textColor,
        fontSize: 11,
        formatter: '{value}',
      },
      splitLine: {
        lineStyle: {
          color: gridLineColor,
          type: 'dashed' as const,
        },
      },
      axisLine: {
        lineStyle: { color: lineColor },
      },
    },
    yAxis: {
      type: 'category',
      data: skills,
      axisLabel: {
        color: textColor,
        fontSize: 12,
      },
      axisLine: {
        lineStyle: { color: lineColor },
      },
      axisTick: { show: false },
    },
    series: [
      {
        name: '要求',
        type: 'bar',
        data: requiredValues.map((v) => ({
          value: v,
          itemStyle: {
            color: isDark ? 'rgba(165, 154, 214, 0.2)' : 'rgba(139, 126, 200, 0.25)',
            borderRadius: [0, 4, 4, 0],
            borderColor: isDark ? '#a59ad6' : '#8b7ec8',
            borderWidth: 1,
          },
        })),
        barWidth: 14,
        barGap: '20%',
        z: 1,
      },
      {
        name: '当前',
        type: 'bar',
        data: currentValues.map((v) => ({
          value: v,
          itemStyle: {
            color: isDark ? '#6c8ecf' : '#5b7bb5',
            borderRadius: [0, 4, 4, 0],
          },
        })),
        barWidth: 14,
        z: 2,
      },
    ],
    graphic: gaps
      .map((gap, index) => {
        if (gap === 0) return null
        const color = gap > 0 ? roseColor : greenColor
        const text = gap > 0 ? `+${gap.toFixed(0)}` : `-${Math.abs(gap).toFixed(0)}`
        return {
          type: 'text',
          left: '87%',
          top: index * (100 / Math.max(gaps.length, 1)) + 100 / Math.max(gaps.length, 1) / 2 + '%',
          style: {
            text,
            fill: color,
            fontSize: 11,
            fontFamily: "var(--font-mono)",
            fontWeight: 'bold',
          },
          z: 10,
        }
      })
      .filter(Boolean),
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
