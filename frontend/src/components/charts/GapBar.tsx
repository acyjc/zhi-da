// ECharts 横向柱状图——当前值 vs 要求值对比，差距标签标注
import ReactECharts from 'echarts-for-react'

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
  background: '#fafaf8',
  borderRadius: 12,
  padding: 16,
  boxSizing: 'border-box',
}

export default function GapBar({ data }: GapBarProps) {
  const skills = data.map((d) => d.skill).reverse()
  const currentValues = data.map((d) => d.current).reverse()
  const requiredValues = data.map((d) => d.required).reverse()
  const gaps = data.map((d) => d.required - d.current).reverse()

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      backgroundColor: 'rgba(248, 247, 244, 0.95)',
      borderColor: '#e8e5df',
      textStyle: { color: '#1d1d1f', fontSize: 13 },
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
          html += `<div style="color:#f472b6;margin-top:4px">差距: <b>+${gap.toFixed(1)}</b></div>`
        } else if (gap < 0) {
          html += `<div style="color:#4ade80;margin-top:4px">超出: <b>${gap.toFixed(1)}</b></div>`
        } else {
          html += `<div style="color:#8892b0;margin-top:4px">已达标</div>`
        }
        return html
      },
    },
    legend: {
      show: true,
      bottom: 0,
      textStyle: { color: '#6e6e73', fontSize: 12 },
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
        color: '#6e6e73',
        fontSize: 11,
        formatter: '{value}',
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(0,0,0,0.06)',
          type: 'dashed' as const,
        },
      },
      axisLine: {
        lineStyle: { color: '#e8e5df' },
      },
    },
    yAxis: {
      type: 'category',
      data: skills,
      axisLabel: {
        color: '#6e6e73',
        fontSize: 12,
      },
      axisLine: {
        lineStyle: { color: '#e8e5df' },
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
            color: 'rgba(139, 126, 200, 0.35)',
            borderRadius: [0, 4, 4, 0],
            borderColor: '#8b7ec8',
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
            color: '#5b7bb5',
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
        const color = gap > 0 ? '#f472b6' : '#4ade80'
        const text = gap > 0 ? `+${gap.toFixed(1)}` : gap.toFixed(1)
        return {
          type: 'text',
          left: '87%',
          top: index * (100 / Math.max(gaps.length, 1)) + 100 / Math.max(gaps.length, 1) / 2 + '%',
          style: {
            text,
            fill: color,
            fontSize: 11,
            fontFamily: "'Rajdhani', sans-serif",
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
