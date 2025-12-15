import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, Filter, X } from 'lucide-react'
import { searchRepository, getCategories, getTags } from '../api/repository'
import AssetCard from '../components/AssetCard'

const assetTypes = ['agent', 'tool', 'skill', 'graph', 'adapter']

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [selectedTypes, setSelectedTypes] = useState<string[]>([])
  const [selectedCategories, setSelectedCategories] = useState<string[]>([])
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [sortBy, setSortBy] = useState('relevance')
  const [showFilters, setShowFilters] = useState(false)

  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: () => getCategories(),
  })

  const { data: tags } = useQuery({
    queryKey: ['tags'],
    queryFn: () => getTags(),
  })

  const { data: results, isLoading } = useQuery({
    queryKey: ['search', query, selectedTypes, selectedCategories, selectedTags, sortBy],
    queryFn: () =>
      searchRepository({
        query: query || undefined,
        types: selectedTypes.length > 0 ? selectedTypes : undefined,
        categories: selectedCategories.length > 0 ? selectedCategories : undefined,
        tags: selectedTags.length > 0 ? selectedTags : undefined,
        sort_by: sortBy,
        limit: 50,
      }),
  })

  const toggleType = (type: string) => {
    setSelectedTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    )
  }

  const toggleCategory = (category: string) => {
    setSelectedCategories((prev) =>
      prev.includes(category) ? prev.filter((c) => c !== category) : [...prev, category]
    )
  }

  const toggleTag = (tag: string) => {
    setSelectedTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    )
  }

  const clearFilters = () => {
    setSelectedTypes([])
    setSelectedCategories([])
    setSelectedTags([])
  }

  const hasFilters = selectedTypes.length > 0 || selectedCategories.length > 0 || selectedTags.length > 0

  return (
    <div className="space-y-6">
      {/* Search Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Search Repository</h1>
        <p className="mt-1 text-gray-600">Find agents, tools, skills, and graphs</p>
      </div>

      {/* Search Bar */}
      <div className="flex gap-3">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by name, description, or tags..."
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`px-4 py-2 rounded-lg border flex items-center gap-2 ${
            showFilters || hasFilters
              ? 'bg-indigo-50 border-indigo-300 text-indigo-700'
              : 'border-gray-300 text-gray-700 hover:bg-gray-50'
          }`}
        >
          <Filter className="h-5 w-5" />
          Filters
          {hasFilters && (
            <span className="bg-indigo-600 text-white text-xs px-1.5 py-0.5 rounded-full">
              {selectedTypes.length + selectedCategories.length + selectedTags.length}
            </span>
          )}
        </button>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="bg-white rounded-lg border border-gray-200 p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-medium text-gray-900">Filters</h3>
            {hasFilters && (
              <button
                onClick={clearFilters}
                className="text-sm text-indigo-600 hover:text-indigo-800"
              >
                Clear all
              </button>
            )}
          </div>

          {/* Type Filter */}
          <div>
            <p className="text-sm font-medium text-gray-700 mb-2">Asset Type</p>
            <div className="flex flex-wrap gap-2">
              {assetTypes.map((type) => (
                <button
                  key={type}
                  onClick={() => toggleType(type)}
                  className={`px-3 py-1.5 rounded-full text-sm capitalize ${
                    selectedTypes.includes(type)
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>

          {/* Category Filter */}
          {categories && categories.length > 0 && (
            <div>
              <p className="text-sm font-medium text-gray-700 mb-2">Category</p>
              <div className="flex flex-wrap gap-2">
                {categories.slice(0, 10).map((category) => (
                  <button
                    key={category}
                    onClick={() => toggleCategory(category)}
                    className={`px-3 py-1.5 rounded-full text-sm ${
                      selectedCategories.includes(category)
                        ? 'bg-indigo-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {category}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Tag Filter */}
          {tags && tags.length > 0 && (
            <div>
              <p className="text-sm font-medium text-gray-700 mb-2">Tags</p>
              <div className="flex flex-wrap gap-2">
                {tags.slice(0, 15).map((tag) => (
                  <button
                    key={tag}
                    onClick={() => toggleTag(tag)}
                    className={`px-3 py-1.5 rounded-full text-sm ${
                      selectedTags.includes(tag)
                        ? 'bg-indigo-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {tag}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Sort By */}
          <div>
            <p className="text-sm font-medium text-gray-700 mb-2">Sort By</p>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
            >
              <option value="relevance">Relevance</option>
              <option value="rating">Rating</option>
              <option value="usage">Usage</option>
              <option value="name">Name</option>
              <option value="created">Created Date</option>
            </select>
          </div>
        </div>
      )}

      {/* Active Filters */}
      {hasFilters && (
        <div className="flex flex-wrap gap-2">
          {selectedTypes.map((type) => (
            <span
              key={type}
              className="inline-flex items-center gap-1 px-3 py-1 bg-indigo-100 text-indigo-800 rounded-full text-sm"
            >
              {type}
              <button onClick={() => toggleType(type)}>
                <X className="h-3 w-3" />
              </button>
            </span>
          ))}
          {selectedCategories.map((category) => (
            <span
              key={category}
              className="inline-flex items-center gap-1 px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm"
            >
              {category}
              <button onClick={() => toggleCategory(category)}>
                <X className="h-3 w-3" />
              </button>
            </span>
          ))}
          {selectedTags.map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center gap-1 px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm"
            >
              {tag}
              <button onClick={() => toggleTag(tag)}>
                <X className="h-3 w-3" />
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Results */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <p className="text-sm text-gray-600">
            {results?.total || 0} results {query && `for "${query}"`}
            {results?.took_ms && (
              <span className="text-gray-400"> ({results.took_ms.toFixed(0)}ms)</span>
            )}
          </p>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {results?.results.map(({ asset, highlights }) => (
              <AssetCard key={`${asset.type}:${asset.id}`} asset={asset} highlights={highlights} />
            ))}
          </div>
        )}

        {!isLoading && results?.results.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500">No results found</p>
            <p className="text-sm text-gray-400 mt-1">Try adjusting your search or filters</p>
          </div>
        )}
      </div>
    </div>
  )
}
