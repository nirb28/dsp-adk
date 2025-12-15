import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Star, Download, ExternalLink, Bot, Wrench, Sparkles, GitBranch, Plug } from 'lucide-react'
import { getAsset, getSkill } from '../api/repository'

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

export default function AssetDetail() {
  const { type, id } = useParams<{ type: string; id: string }>()

  const { data: asset, isLoading } = useQuery({
    queryKey: ['asset', type, id],
    queryFn: () => getAsset(type!, id!),
    enabled: !!type && !!id && type !== 'skill',
  })

  const { data: skill, isLoading: skillLoading } = useQuery({
    queryKey: ['skill', id],
    queryFn: () => getSkill(id!),
    enabled: type === 'skill' && !!id,
  })

  if (isLoading || skillLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    )
  }

  const displayAsset = type === 'skill' ? {
    ...skill,
    type: 'skill',
  } : asset

  if (!displayAsset) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Asset not found</p>
        <Link to="/" className="text-indigo-600 hover:underline mt-2 inline-block">
          Go back to dashboard
        </Link>
      </div>
    )
  }

  const Icon = typeIcons[type || ''] || Bot
  const colorClass = typeColors[type || ''] || 'bg-gray-100 text-gray-800'

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <Link
        to={-1 as any}
        className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900"
      >
        <ArrowLeft className="h-4 w-4" />
        Back
      </Link>

      {/* Header */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className={`p-3 rounded-lg ${colorClass}`}>
              <Icon className="h-8 w-8" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{displayAsset.name}</h1>
              <div className="flex items-center gap-3 mt-1">
                <span className={`px-2 py-0.5 rounded-full text-sm ${colorClass}`}>
                  {type}
                </span>
                <span className="text-gray-500 text-sm">v{displayAsset.version}</span>
                {displayAsset.author && (
                  <span className="text-gray-500 text-sm">by {displayAsset.author}</span>
                )}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-4">
            {displayAsset.rating > 0 && (
              <div className="flex items-center gap-1 text-amber-500">
                <Star className="h-5 w-5 fill-current" />
                <span className="font-medium">{displayAsset.rating.toFixed(1)}</span>
              </div>
            )}
          </div>
        </div>

        <p className="mt-4 text-gray-600">{displayAsset.description}</p>

        {/* Tags */}
        {displayAsset.tags && displayAsset.tags.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-2">
            {displayAsset.tags.map((tag: string) => (
              <span
                key={tag}
                className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Skill-specific: System Prompt */}
      {type === 'skill' && skill?.system_prompt && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">System Prompt</h2>
          <pre className="bg-gray-50 p-4 rounded-lg text-sm text-gray-700 whitespace-pre-wrap overflow-x-auto">
            {skill.system_prompt}
          </pre>
        </div>
      )}

      {/* Parameters */}
      {((type === 'skill' && skill?.parameters) || displayAsset.config_schema) && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Configuration Parameters</h2>
          {type === 'skill' && skill?.parameters ? (
            <div className="space-y-3">
              {skill.parameters.map((param: any) => (
                <div key={param.name} className="border-b border-gray-100 pb-3 last:border-0">
                  <div className="flex items-center gap-2">
                    <code className="text-indigo-600 font-medium">{param.name}</code>
                    <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
                      {param.type}
                    </span>
                    {param.required && (
                      <span className="text-xs text-red-600 bg-red-50 px-2 py-0.5 rounded">
                        required
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{param.description}</p>
                  {param.default !== undefined && (
                    <p className="text-xs text-gray-500 mt-1">
                      Default: <code>{JSON.stringify(param.default)}</code>
                    </p>
                  )}
                </div>
              ))}
            </div>
          ) : displayAsset.config_schema ? (
            <pre className="bg-gray-50 p-4 rounded-lg text-sm text-gray-700 overflow-x-auto">
              {JSON.stringify(displayAsset.config_schema, null, 2)}
            </pre>
          ) : null}
        </div>
      )}

      {/* Dependencies */}
      {displayAsset.dependencies && displayAsset.dependencies.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Dependencies</h2>
          <div className="flex flex-wrap gap-2">
            {displayAsset.dependencies.map((dep: string) => (
              <span
                key={dep}
                className="px-3 py-1.5 bg-indigo-50 text-indigo-700 rounded-lg text-sm font-medium"
              >
                {dep}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Required Tools (for skills) */}
      {type === 'skill' && skill?.required_tools && skill.required_tools.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Required Tools</h2>
          <div className="flex flex-wrap gap-2">
            {skill.required_tools.map((tool: string) => (
              <Link
                key={tool}
                to={`/asset/tool/${tool}`}
                className="px-3 py-1.5 bg-green-50 text-green-700 rounded-lg text-sm font-medium hover:bg-green-100"
              >
                {tool}
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Examples */}
      {displayAsset.examples && displayAsset.examples.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Examples</h2>
          <div className="space-y-4">
            {displayAsset.examples.map((example: any, idx: number) => (
              <div key={idx} className="bg-gray-50 rounded-lg p-4">
                {example.input && (
                  <div className="mb-2">
                    <span className="text-xs font-medium text-gray-500 uppercase">Input</span>
                    <pre className="mt-1 text-sm text-gray-700 whitespace-pre-wrap">
                      {example.input}
                    </pre>
                  </div>
                )}
                {example.output && (
                  <div>
                    <span className="text-xs font-medium text-gray-500 uppercase">Output</span>
                    <pre className="mt-1 text-sm text-gray-700 whitespace-pre-wrap">
                      {example.output}
                    </pre>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
