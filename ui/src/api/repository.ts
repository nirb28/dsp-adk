const API_BASE = '/api/repository'

export interface AssetMetadata {
  id: string
  type: string
  name: string
  description: string
  version: string
  category: string
  tags: string[]
  author?: string
  rating: number
  usage_count: number
  dependencies: string[]
  config_schema: Record<string, unknown>
}

export interface SearchResult {
  asset: AssetMetadata
  score: number
  highlights: Record<string, string[]>
}

export interface SearchResponse {
  success: boolean
  results: SearchResult[]
  total: number
  query?: string
  took_ms: number
}

export interface RepositoryStats {
  total_assets: number
  assets_by_type: Record<string, number>
  assets_by_category: Record<string, number>
  top_tags: Array<{ tag: string; count: number }>
  recent_assets: AssetMetadata[]
  popular_assets: AssetMetadata[]
}

export interface Skill {
  id: string
  name: string
  description: string
  category: string
  version: string
  system_prompt: string
  parameters: Array<{
    name: string
    type: string
    description: string
    required: boolean
    default?: unknown
  }>
  required_tools: string[]
  tags: string[]
  rating: number
}

export async function searchRepository(params: {
  query?: string
  types?: string[]
  categories?: string[]
  tags?: string[]
  sort_by?: string
  limit?: number
  offset?: number
}): Promise<SearchResponse> {
  const searchParams = new URLSearchParams()
  if (params.query) searchParams.set('query', params.query)
  if (params.types) params.types.forEach(t => searchParams.append('types', t))
  if (params.categories) params.categories.forEach(c => searchParams.append('categories', c))
  if (params.tags) params.tags.forEach(t => searchParams.append('tags', t))
  if (params.sort_by) searchParams.set('sort_by', params.sort_by)
  if (params.limit) searchParams.set('limit', params.limit.toString())
  if (params.offset) searchParams.set('offset', params.offset.toString())

  const response = await fetch(`${API_BASE}/search?${searchParams}`)
  return response.json()
}

export async function getStats(): Promise<RepositoryStats> {
  const response = await fetch(`${API_BASE}/stats`)
  return response.json()
}

export async function getCategories(type?: string): Promise<string[]> {
  const url = type ? `${API_BASE}/categories?type=${type}` : `${API_BASE}/categories`
  const response = await fetch(url)
  return response.json()
}

export async function getTags(type?: string): Promise<string[]> {
  const url = type ? `${API_BASE}/tags?type=${type}` : `${API_BASE}/tags`
  const response = await fetch(url)
  return response.json()
}

export async function getAsset(type: string, id: string): Promise<AssetMetadata> {
  const response = await fetch(`${API_BASE}/assets/${type}/${id}`)
  return response.json()
}

export async function getSkills(category?: string): Promise<{ skills: Skill[]; total: number }> {
  const url = category ? `${API_BASE}/skills?category=${category}` : `${API_BASE}/skills`
  const response = await fetch(url)
  return response.json()
}

export async function getSkill(id: string): Promise<Skill> {
  const response = await fetch(`${API_BASE}/skills/${id}`)
  return response.json()
}
