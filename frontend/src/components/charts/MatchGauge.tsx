// ECharts 半圆仪表盘——三段色(玫瑰→琥珀→绿)，支持 previousScore 变化箭头
import ReactECharts from 'echarts-for-react'

interface MatchGaugeProps {
  score: number
  previousScore?: number
  label?: string
}

const containerStyle: React.CSSProperties = {
  width: '100%',
  height: '100%',
  background: '#fafaf8',
  borderRadius: 12,
  boxSizing: 'border-box',
  position: 'relative',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
}

const labelStyle: React.CSSProperties = {
  color: '#8892b0',
  fontSize: 14,
  textAlign: 'center',
  position: 'absolute',
  top: 22,
  left: '50%',
  transform: 'translateX(-50%)',
}

const deltaStyle: React.CSSProperties = {
  position: 'absolute',
  bottom: 18,
  left: '50%',
  transform: 'translateX(-50%)',
  fontFamily: "'Rajdhani', sans-serif",
  fontSize: 16,
  display: 'flex',
  alignItems: 'center',
  gap: 6,
}

export default function MatchGauge({ score, previousScore, label }: MatchGaugeProps) {
  const percent = Math.round(score * 100)
  const delta = previousScore !== undefined ? Math.round((score - previousScore) * 100) : null
  const isUp = delta !== null && delta > 0
  const isDown = delta !== null && delta < 0

  const option = {
    backgroundColor: 'transparent',
    series: [
      {
        type: 'gauge',
        startAngle: 210,
        endAngle: -30,
        center: ['50%', '60%'],
        radius: '90%',
        min: 0,
        max: 100,
        splitNumber: 10,
        axisLine: {
          show: true,
          lineStyle: {
            width: 18,
            color: [
              [0.4, '#c47a8b'],
              [0.7, '#c4944a'],
              [1, '#6ba87a'],
            ],
            shadowBlur: 8,
            shadowColor: 'rgba(91, 123, 181, 0.3)',
            shadowOffsetX: 0,
            shadowOffsetY: 0,
          },
        },
        pointer: {
          icon: 'path://M12.8,0.7l12,40.1H0.7L12.8,0.7z',
          length: '60%',
          width: 6,
          offsetCenter: [0, '-14%'],
          itemStyle: {
            color: 'auto',
          },
        },
        axisTick: {
          length: 10,
          lineStyle: {
            color: 'auto',
            width: 1,
          },
          distance: -20,
        },
        splitLine: {
          length: 22,
          lineStyle: {
            color: 'auto',
            width: 3,
          },
          distance: -22,
        },
        axisLabel: {
          color: '#6e6e73',
          distance: 30,
          fontSize: 11,
          fontFamily: "'Rajdhani', sans-serif",
        },
        anchor: {
          show: true,
          showAbove: true,
          size: 16,
          itemStyle: {
            borderColor: '#fafaf8',
            borderWidth: 3,
            color: '#5b7bb5',
          },
        },
        title: {
          show: false,
        },
        detail: {
          valueAnimation: true,
          formatter: '{value}%',
          color: '#1d1d1f',
          fontSize: 36,
          fontFamily: "'Rajdhani', sans-serif",
          fontWeight: 'bold',
          offsetCenter: [0, '50%'],
        },
        data: [
          {
            value: percent,
          },
        ],
      },
    ],
  }

  return (
    <div style={containerStyle}>
      {label && <div style={labelStyle}>{label}</div>}
      <ReactECharts
        option={option}
        style={{ width: '100%', height: '100%' }}
        opts={{ renderer: 'canvas' }}
      />
      {delta !== null && delta !== 0 && (
        <div style={deltaStyle}>
          <span style={{ color: isUp ? '#4ade80' : '#f472b6', fontSize: 20 }}>
            {isUp ? '▲' : '▼'}
          </span>
          <span style={{ color: isUp ? '#4ade80' : '#f472b6' }}>
            {isUp ? '+' : ''}{delta}%
          </span>
          <span style={{ color: '#8892b0', fontSize: 12 }}>vs 上次</span>
        </div>
      )}
    </div>
  )
}
