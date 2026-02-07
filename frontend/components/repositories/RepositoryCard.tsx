'use client';

import { Repository } from '@/lib/types/repository';
import Link from 'next/link';

interface RepositoryCardProps {
    repo: Repository;
    onSync?: (id: string) => void;
}

export function RepositoryCard({ repo, onSync }: RepositoryCardProps) {
    return (
        <div className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-6 border border-gray-700/50 hover:border-purple-500/50 transition-all">
            <div className="flex items-start justify-between">
                <div className="flex-1">
                    <Link href={`/repositories/${repo.id}`} className="group">
                        <h3 className="text-lg font-semibold text-white group-hover:text-purple-400 transition-colors">
                            {repo.name}
                        </h3>
                        <p className="text-sm text-gray-400">{repo.full_name}</p>
                    </Link>
                    {repo.description && (
                        <p className="mt-2 text-sm text-gray-300 line-clamp-2">{repo.description}</p>
                    )}
                </div>
                <span className={`px-2 py-1 text-xs rounded-full ${repo.visibility === 'public'
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-yellow-500/20 text-yellow-400'
                    }`}>
                    {repo.visibility}
                </span>
            </div>

            <div className="mt-4 flex items-center gap-4 text-sm text-gray-400">
                {repo.language && (
                    <span className="flex items-center gap-1">
                        <span className="w-3 h-3 rounded-full bg-purple-500"></span>
                        {repo.language}
                    </span>
                )}
                <span>⭐ {repo.stars_count}</span>
                <span>🔱 {repo.forks_count}</span>
                <span>📋 {repo.open_issues_count}</span>
            </div>

            <div className="mt-4 flex items-center justify-between">
                <span className="text-xs text-gray-500">
                    {repo.last_synced_at
                        ? `Synced ${new Date(repo.last_synced_at).toLocaleString()}`
                        : 'Never synced'}
                </span>
                {onSync && (
                    <button
                        onClick={() => onSync(repo.id)}
                        className="px-3 py-1 text-sm bg-purple-500/20 text-purple-400 rounded-lg hover:bg-purple-500/30 transition-colors"
                    >
                        Sync
                    </button>
                )}
            </div>
        </div>
    );
}

export default RepositoryCard;
