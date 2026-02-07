'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { repositoriesApi } from '@/lib/api/repositories';
import { Repository } from '@/lib/types/repository';
import { ProtectedRoute } from '@/components/auth';

function RepositoryCard({ repo, onSync }: { repo: Repository; onSync: (id: string) => void }) {
    const [syncing, setSyncing] = useState(false);

    const handleSync = async () => {
        setSyncing(true);
        try {
            await onSync(repo.id);
        } finally {
            setSyncing(false);
        }
    };

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
                <span className="flex items-center gap-1">
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                    {repo.stars_count}
                </span>
                <span className="flex items-center gap-1">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                    </svg>
                    {repo.forks_count}
                </span>
                <span className="flex items-center gap-1">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {repo.open_issues_count}
                </span>
            </div>

            <div className="mt-4 flex items-center justify-between">
                <span className="text-xs text-gray-500">
                    {repo.last_synced_at
                        ? `Synced ${new Date(repo.last_synced_at).toLocaleString()}`
                        : 'Never synced'
                    }
                </span>
                <button
                    onClick={handleSync}
                    disabled={syncing}
                    className="px-3 py-1 text-sm bg-purple-500/20 text-purple-400 rounded-lg hover:bg-purple-500/30 disabled:opacity-50 transition-colors"
                >
                    {syncing ? 'Syncing...' : 'Sync'}
                </button>
            </div>
        </div>
    );
}

function RepositoriesContent() {
    const [repos, setRepos] = useState<Repository[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        loadRepositories();
    }, []);

    const loadRepositories = async () => {
        try {
            const data = await repositoriesApi.list();
            setRepos(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load repositories');
        } finally {
            setLoading(false);
        }
    };

    const handleSync = async (id: string) => {
        try {
            await repositoriesApi.sync(id);
            await loadRepositories();
        } catch (err) {
            console.error('Sync failed:', err);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center py-12">
                <div className="animate-spin w-8 h-8 border-4 border-purple-500 border-t-transparent rounded-full"></div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-8">
            <div className="max-w-6xl mx-auto">
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-3xl font-bold text-white">Repositories</h1>
                        <p className="text-gray-400 mt-1">Manage your GitHub repositories</p>
                    </div>
                    <Link
                        href="/repositories/add"
                        className="px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all flex items-center gap-2"
                    >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                        </svg>
                        Add Repository
                    </Link>
                </div>

                {error && (
                    <div className="mb-6 p-4 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400">
                        {error}
                    </div>
                )}

                {repos.length === 0 ? (
                    <div className="text-center py-12 bg-gray-800/30 rounded-xl border border-gray-700/50">
                        <svg className="w-16 h-16 mx-auto text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                        </svg>
                        <h3 className="text-xl font-semibold text-gray-300 mb-2">No repositories yet</h3>
                        <p className="text-gray-500 mb-4">Add your first GitHub repository to get started</p>
                        <Link
                            href="/repositories/add"
                            className="inline-flex items-center gap-2 px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors"
                        >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                            </svg>
                            Add Repository
                        </Link>
                    </div>
                ) : (
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                        {repos.map((repo) => (
                            <RepositoryCard key={repo.id} repo={repo} onSync={handleSync} />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

export default function RepositoriesPage() {
    return (
        <ProtectedRoute>
            <RepositoriesContent />
        </ProtectedRoute>
    );
}
