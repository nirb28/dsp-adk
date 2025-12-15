import { useQuery } from '@tanstack/react-query'
import { Wrench } from 'lucide-react'
import { searchRepository } from '../api/repository'
import AssetCard from '../components/AssetCard'

export default function ToolsPage() {
  const { data: results, isLoading } = useQuery({
    queryKey: ['tools'],
    queryFn: () =>
      searchRepository({
        types: ['tool'],
        sort_by: 'name',
        limit: 100,
      }),
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-green-100 rounded-lg">
          <Wrench className="h-6 w-6 text-green-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Tools</h1>
          <p className="text-gray-600">Reusable tool configurations with parameters</p>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
        </div>
      ) : (
        <>
          <p className="text-sm text-gray-500">{results?.total || 0} tools</p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {results?.results.map(({ asset }) => (
              <AssetCard key={asset.id} asset={asset} />
            ))}
          </div>
          {results?.results.length === 0 && (
            <div className="text-center py-12 text-gray-500">No tools found</div>
          )}
        </>
      )}
    </div>
  )
}
