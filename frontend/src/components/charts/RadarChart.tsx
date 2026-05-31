// ECharts 雷达图——四维能力可视化，支持 previousData 半透明对比叠加层
import ReactECharts from 'echarts-for-react'
import { useRef } from 'react'

const CHART_COLORS = ['#5b7bb5', '#5a9e8f', '#8b7ec8', '#c4944a', '#c47a8b', '#6ba87a']

interface RadarDataItem {
  name: string
  value: number
  fullMark?: number
}

interface RadarChartProps {
  data: RadarDataItem[]
  previousData?: RadarDataItem[]
}

const containerStyle: React.CSSProperties = {
  width: '100%',
  height: '100%',
  background: '#fafaf8',
  borderRadius: 12,
  padding: 16,
  boxSizing: 'border-box',
  position: 'relative',
}

export default function RadarChart({ data, previousData }: RadarChartProps) {
  const indicator = data.map((item) => ({
    name: item.name,
    max: item.fullMark ?? 100,
  }))

  const series: any[] = []

  if (previousData) {
    series.push({
      type: 'radar',
      data: [
        {
          value: previousData.map((d) => d.value),
          name: '上次诊断',
        },
      ],
      symbol: 'none',
      lineStyle: {
        color: '#8b7ec8',
        width: 1,
        type: 'dashed' as const,
      },
      areaStyle: {
        color: 'rgba(139, 126, 200, 0.15)',
      },
      itemStyle: {
        color: '#8b7ec8',
      },
      z: 1,
    })
  }

  series.push({
    type: 'radar',
    data: [
      {
        value: data.map((d) => d.value),
        name: '当前能力',
      },
    ],
    symbol: 'circle',
    symbolSize: 6,
    lineStyle: {
      color: CHART_COLORS[0],
      width: 2,
    },
    areaStyle: {
      color: 'rgba(91, 123, 181, 0.3)',
    },
    itemStyle: {
      color: CHART_COLORS[0],
      borderColor: '#fafaf8',
      borderWidth: 2,
    },
    z: 2,
  })

  const option = {
    color: CHART_COLORS,
    backgroundColor: 'transparent',
    tooltip: {
      backgroundColor: 'rgba(248, 247, 244, 0.95)',
      borderColor: '#e8e5df',
      textStyle: { color: '#1d1d1f', fontSize: 13 },
      formatter: (params: any) => {
        if (!Array.isArray(params)) return ''
        let result = `<div style="font-weight:600;margin-bottom:4px">${params[0].name}</div>`
        params.forEach((p: any) => {
          result += `<div style="display:flex;align-items:center;gap:6px">${p.marker} ${p.seriesName}: <b>${p.value}</b></div>`
        })
        return result
      },
    },
    legend: {
      show: false,
    },
    radar: {
      center: ['50%', '52%'],
      radius: '62%',
      indicator,
      shape: 'circle',
      splitNumber: 5,
      axisName: {
        color: '#6e6e73',
        fontSize: 13,
        borderRadius: 4,
        padding: [4, 8],
      },
      splitArea: {
        areaStyle: {
          color: ['rgba(0,0,0,0.03)', 'rgba(0,0,0,0.01)'],
        },
      },
      splitLine: {
        lineStyle: {
          color: '#e8e5df',
        },
      },
      axisLine: {
        lineStyle: {
          color: '#e8e5df',
        },
      },
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
