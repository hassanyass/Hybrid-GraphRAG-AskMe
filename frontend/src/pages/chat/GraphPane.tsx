import { useEffect, useRef, useState, useMemo } from 'react'
import type { Entity, Relationship } from '@/hooks/useChat'
import { Network } from 'lucide-react'
import ForceGraph2D, { ForceGraphMethods } from 'react-force-graph-2d'

interface GraphPaneProps {
  entities?: Entity[]
  relationships?: Relationship[]
}

export function GraphPane({ entities = [], relationships = [] }: GraphPaneProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const graphRef = useRef<ForceGraphMethods>()
  
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 })

  useEffect(() => {
    if (!containerRef.current) return
    const observer = new ResizeObserver((entries) => {
      const { width, height } = entries[0].contentRect
      setDimensions({ width, height })
    })
    observer.observe(containerRef.current)
    return () => observer.disconnect()
  }, [])

  // Format data for react-force-graph
  const graphData = useMemo(() => {
    const nodes = entities.map(e => ({
      id: e.id,
      name: e.name || e.label || e.id,
      val: 2,
      type: e.type || e.label || 'Entity',
      color: '#4B6BFb'
    }))

    const links = relationships.map(r => ({
      source: r.source,
      target: r.target,
      name: r.type,
      color: '#cbd5e1'
    }))

    return { nodes, links }
  }, [entities, relationships])

  useEffect(() => {
    if (graphRef.current && graphData.nodes.length > 0) {
      setTimeout(() => {
        graphRef.current?.zoomToFit(400, 50)
      }, 100)
    }
  }, [graphData])

  if (!entities || entities.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center p-8 text-center text-neutral-dark">
        <Network className="mb-4 h-12 w-12 opacity-20" />
        <p className="text-sm font-medium text-foreground">No entities extracted</p>
        <p className="mt-1 text-xs">Knowledge graph relationships will appear here.</p>
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col overflow-hidden animate-in fade-in slide-in-from-right-4 duration-300">
      <div className="p-6 pb-2 shrink-0">
        <h3 className="font-semibold text-lg flex items-center gap-2 text-foreground">
          <Network className="h-5 w-5 text-accent" />
          Interactive Knowledge Graph
        </h3>
        <p className="text-xs text-neutral-dark mt-1">
          {entities.length} Nodes &bull; {relationships.length} Relationships
        </p>
      </div>
      
      <div ref={containerRef} className="flex-1 w-full relative bg-neutral-50 rounded-lg overflow-hidden m-4 mt-2 border border-border">
        {dimensions.width > 0 && dimensions.height > 0 && (
          <ForceGraph2D
            ref={graphRef as any}
            width={dimensions.width}
            height={dimensions.height}
            graphData={graphData}
            nodeLabel="name"
            nodeColor="color"
            nodeRelSize={6}
            linkColor="color"
            linkWidth={1.5}
            linkDirectionalArrowLength={3.5}
            linkDirectionalArrowRelPos={1}
            linkLabel="name"
            onNodeClick={(node: any) => {
              graphRef.current?.centerAt(node.x, node.y, 1000)
              graphRef.current?.zoom(4, 1000)
            }}
            nodeCanvasObject={(node: any, ctx, globalScale) => {
              const label = node.name
              const fontSize = 12 / globalScale
              ctx.font = `${fontSize}px Sans-Serif`
              const textWidth = ctx.measureText(label).width
              const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.2)

              ctx.fillStyle = 'rgba(255, 255, 255, 0.8)'
              ctx.fillRect(node.x - bckgDimensions[0] / 2, node.y - bckgDimensions[1] / 2, bckgDimensions[0], bckgDimensions[1])

              ctx.textAlign = 'center'
              ctx.textBaseline = 'middle'
              ctx.fillStyle = node.color
              ctx.fillText(label, node.x, node.y)

              node.__bckgDimensions = bckgDimensions
            }}
            nodePointerAreaPaint={(node: any, color, ctx) => {
              ctx.fillStyle = color
              const bckgDimensions = node.__bckgDimensions
              bckgDimensions && ctx.fillRect(node.x - bckgDimensions[0] / 2, node.y - bckgDimensions[1] / 2, bckgDimensions[0], bckgDimensions[1])
            }}
          />
        )}
      </div>
    </div>
  )
}
