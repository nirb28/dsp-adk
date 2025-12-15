import { useQuery } from '@tanstack/react-query'
import { Bot, Wrench, Sparkles, GitBranch, TrendingUp } from 'lucide-react'
import { Link } from 'react-router-dom'
import { getStats } from '../api/repository'
import AssetCard from '../components/AssetCard'

export default function Dashboard() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['stats'],
    queryFn: getStats,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    )
  }

  const typeStats = [
    { type: 'agent', label: 'Agents', icon: Bot, color: 'bg-blue-500' },
    { type: 'tool', label: 'Tools', icon: Wrench, color: 'bg-green-500' },
    { type: 'skill', label: 'Skills', icon: Sparkles, color: 'bg-purple-500' },
    { type: 'graph', label: 'Graphs', icon: GitBranch, color: 'bg-orange-500' },
  ]

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Repository Dashboard</h1>
        <p className="mt-1 text-gray-600">
          Browse and discover agents, tools, skills, and graphs
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {typeStats.map(({ type, label, icon: Icon, color }) => (
          <Link
            key={type}
            to={`/${type}s`}
            className="bg-white rounded-lg border border-gray-200 p-5 hover:shadow-md transition-shadow"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">{label}</p>
                <p className="text-3xl font-bold text-gray-900">
                  {stats?.assets_by_type[type] || 0}
                </p>
              </div>
              <div className={`p-3 rounded-lg ${color}`}>
                <Icon className="h-6 w-6 text-white" />
              </div>
            </div>
          </Link>
        ))}
      </div>

      {/* Total Stats */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-lg p-6 text-white">
        <div className="flex items-center gap-3">
          <TrendingUp className="h-8 w-8" />
          <div>
            <p className="text-indigo-200">Total Assets</p>
            <p className="text-4xl font-bold">{stats?.total_assets || 0}</p>
          </div>
        </div>
      </div>

      {/* Top Tags */}
      {stats?.top_tags && stats.top_tags.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-5">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Popular Tags</h2>
          <div className="flex flex-wrap gap-2">
            {stats.top_tags.slice(0, 15).map(({ tag, count }) => (
              <Link
                key={tag}
                to={`/search?tags=${tag}`}
                className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-full text-sm hover:bg-indigo-100 hover:text-indigo-700 transition-colors"
              >
                {tag} <span className="text-gray-400">({count})</span>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Recent & Popular */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Assets */}
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Assets</h2>
          <div className="space-y-3">
            {stats?.recent_assets?.slice(0, 5).map((asset) => (
              <AssetCard key={`${asset.type}:${asset.id}`} asset={asset} />
            ))}
            {(!stats?.recent_assets || stats.recent_assets.length === 0) && (
              <p className="text-gray-500 text-sm">No recent assets</p>
            )}
          </div>
        </div>

        {/* Popular Assets */}
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Popular Assets</h2>
          <div className="space-y-3">
            {stats?.popular_assets?.slice(0, 5).map((asset) => (
              <AssetCard key={`${asset.type}:${asset.id}`} asset={asset} />
            ))}
            {(!stats?.popular_assets || stats.popular_assets.length === 0) && (
              <p className="text-gray-500 text-sm">No popular assets</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
