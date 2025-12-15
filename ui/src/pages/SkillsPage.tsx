import { useQuery } from '@tanstack/react-query'
import { Sparkles, Star } from 'lucide-react'
import { Link } from 'react-router-dom'
import { getSkills } from '../api/repository'

export default function SkillsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['skills'],
    queryFn: () => getSkills(),
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-purple-100 rounded-lg">
          <Sparkles className="h-6 w-6 text-purple-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Skills</h1>
          <p className="text-gray-600">Reusable agent capabilities and behaviors</p>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
        </div>
      ) : (
        <>
          <p className="text-sm text-gray-500">{data?.total || 0} skills</p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {data?.skills.map((skill) => (
              <Link
                key={skill.id}
                to={`/asset/skill/${skill.id}`}
                className="block bg-white rounded-lg border border-gray-200 p-5 hover:shadow-md hover:border-purple-300 transition-all"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-purple-100 text-purple-800">
                      <Sparkles className="h-5 w-5" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">{skill.name}</h3>
                      <span className="inline-block px-2 py-0.5 text-xs rounded-full bg-purple-100 text-purple-800">
                        {skill.category}
                      </span>
                    </div>
                  </div>
                  {skill.rating > 0 && (
                    <div className="flex items-center gap-1 text-amber-500">
                      <Star className="h-4 w-4 fill-current" />
                      <span className="text-sm font-medium">{skill.rating.toFixed(1)}</span>
                    </div>
                  )}
                </div>

                <p className="mt-3 text-sm text-gray-600 line-clamp-2">
                  {skill.description}
                </p>

                {skill.parameters && skill.parameters.length > 0 && (
                  <div className="mt-3">
                    <p className="text-xs text-gray-500 mb-1">
                      {skill.parameters.length} configurable parameter{skill.parameters.length !== 1 ? 's' : ''}
                    </p>
                  </div>
                )}

                <div className="mt-3 flex flex-wrap gap-1.5">
                  {skill.tags.slice(0, 3).map((tag) => (
                    <span
                      key={tag}
                      className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </Link>
            ))}
          </div>
          {data?.skills.length === 0 && (
            <div className="text-center py-12 text-gray-500">No skills found</div>
          )}
        </>
      )}
    </div>
  )
}
