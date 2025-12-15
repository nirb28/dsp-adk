import { Link } from 'react-router-dom'
import { Bot, Wrench, Sparkles, GitBranch, Plug, Star } from 'lucide-react'
import type { AssetMetadata } from '../api/repository'

const typeIcons: Record<string, typeof Bot> = {
  agent: Bot,
  tool: Wrench,
  skill: Sparkles,
  graph: GitBranch,
  adapter: Plug,
}

const typeColors: Record<string, string> = {
  agent: 'bg-blue-100 text-blue-800',
  tool: 'bg-green-100 text-green-800',
  skill: 'bg-purple-100 text-purple-800',
  graph: 'bg-orange-100 text-orange-800',
  adapter: 'bg-pink-100 text-pink-800',
}

interface AssetCardProps {
  asset: AssetMetadata
  highlights?: Record<string, string[]>
}

export default function AssetCard({ asset, highlights }: AssetCardProps) {
  const Icon = typeIcons[asset.type] || Bot
  const colorClass = typeColors[asset.type] || 'bg-gray-100 text-gray-800'

  return (
    <Link
      to={`/asset/${asset.type}/${asset.id}`}
      className="block bg-white rounded-lg border border-gray-200 p-5 hover:shadow-md hover:border-indigo-300 transition-all"
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${colorClass}`}>
            <Icon className="h-5 w-5" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">{asset.name}</h3>
            <span className={`inline-block px-2 py-0.5 text-xs rounded-full ${colorClass}`}>
              {asset.type}
            </span>
          </div>
        </div>
        {asset.rating > 0 && (
          <div className="flex items-center gap-1 text-amber-500">
            <Star className="h-4 w-4 fill-current" />
            <span className="text-sm font-medium">{asset.rating.toFixed(1)}</span>
          </div>
        )}
      </div>

      <p className="mt-3 text-sm text-gray-600 line-clamp-2">
        {highlights?.description?.[0] || asset.description || 'No description available'}
      </p>

      <div className="mt-4 flex flex-wrap gap-1.5">
        {asset.tags.slice(0, 4).map(tag => (
          <span
            key={tag}
            className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full"
          >
            {tag}
          </span>
        ))}
        {asset.tags.length > 4 && (
          <span className="px-2 py-0.5 bg-gray-100 text-gray-500 text-xs rounded-full">
            +{asset.tags.length - 4}
          </span>
        )}
      </div>

      <div className="mt-4 flex items-center justify-between text-xs text-gray-500">
        <span>v{asset.version}</span>
        <span>{asset.category}</span>
      </div>
    </Link>
  )
}
