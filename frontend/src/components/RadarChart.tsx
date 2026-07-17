interface RadarData {
  subject: string;
  correctRate: number;
  weight: number;
}

interface RadarChartProps {
  data: RadarData[];
  width?: number;
  height?: number;
}

export default function RadarChart({ data, width = 280, height = 280 }: RadarChartProps) {
  if (!data.length) return null;

  const cx = width / 2;
  const cy = height / 2;
  const radius = Math.min(cx, cy) - 30;
  const levels = 5;

  // 计算多边形顶点
  const getPoint = (index: number, total: number, value: number, maxValue: number) => {
    const angle = (Math.PI * 2 * index) / total - Math.PI / 2;
    const r = (value / maxValue) * radius;
    return {
      x: cx + r * Math.cos(angle),
      y: cy + r * Math.sin(angle),
    };
  };

  const getGridPoints = (level: number) => {
    return data.map((_, i) => getPoint(i, data.length, level, levels));
  };

  const maxRate = 100;
  const dataPoints = data.map((d, i) =>
    getPoint(i, data.length, d.correctRate, maxRate)
  );

  return (
    <svg width={width} height={height} className="mx-auto">
      {/* 网格线 */}
      {Array.from({ length: levels }, (_, level) => {
        const points = getGridPoints(level + 1);
        return (
          <polygon
            key={level}
            points={points.map((p) => `${p.x},${p.y}`).join(' ')}
            fill="none"
            stroke="#e5e7eb"
            strokeWidth={1}
          />
        );
      })}

      {/* 轴线 */}
      {data.map((_, i) => {
        const p = getPoint(i, data.length, levels, levels);
        return (
          <line
            key={i}
            x1={cx}
            y1={cy}
            x2={p.x}
            y2={p.y}
            stroke="#e5e7eb"
            strokeWidth={1}
          />
        );
      })}

      {/* 数据区域 */}
      <polygon
        points={dataPoints.map((p) => `${p.x},${p.y}`).join(' ')}
        fill="rgba(59, 130, 246, 0.2)"
        stroke="#3b82f6"
        strokeWidth={2}
      />

      {/* 数据点 */}
      {dataPoints.map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r={4} fill="#3b82f6" />
      ))}

      {/* 标签 */}
      {data.map((d, i) => {
        const p = getPoint(i, data.length, levels + 1, levels);
        return (
          <text
            key={i}
            x={p.x}
            y={p.y}
            textAnchor="middle"
            dominantBaseline="middle"
            className="text-xs fill-gray-600"
          >
            {d.subject}
          </text>
        );
      })}
    </svg>
  );
}
