'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { repositoriesApi } from '@/lib/api/repositories';
import { Repository, Branch } from '@/lib/types/repository';
import { ProtectedRoute } from '@/components/auth';

function RepositoryDetailContent() {
    const params = useParams();
    const router = useRouter();
    const repoId = params.id as string;

    const [repo, setRepo] = useState<Repository | null>(null);
    const [branches, setBranches] = useState<Branch[]>([]);
    const [loading, setLoading] = useState(true);
    const [syncing, setSyncing] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        loadRepository();
    }, [repoId]);

    const loadRepository = async () => {
        try {
            const [repoData, branchData] = await Promise.all([
                repositoriesApi.get(repoId),
                repositoriesApi.getBranches(repoId).catch(() => []),
            ]);
            setRepo(repoData);
            setBranches(branchData);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load repository');
        } finally {
            setLoading(false);
        }
    };

    const handleSync = async () => {
        setSyncing(true);
        try {
            await repositoriesApi.sync(repoId);
            await loadRepository();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Sync failed');
        } finally {
            setSyncing(false);
        }
    };

    const handleDelete = async () => {
        if (!confirm('Are you sure you want to remove this repository?')) return;

        try {
            await repositoriesApi.delete(repoId);
            router.push('/repositories');
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Delete failed');
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center">
                <div className="animate-spin w-10 h-10 border-4 border-purple-500 border-t-transparent rounded-full"></div>
            </div>
        );
    }

    if (!repo) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center">
                <div className="text-center">
                    <h2 className="text-2xl font-bold text-white mb-4">Repository not found</h2>
                    <Link href="/repositories" className="text-purple-400 hover:text-purple-300">
                        Back to repositories
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-8">
            <div className="max-w-6xl mx-auto">
                <Link href="/repositories" className="text-gray-400 hover:text-white flex items-center gap-2 mb-6">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                    Back to Repositories
                </Link>

                {error && (
                    <div className="mb-6 p-4 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400">
                        {error}
                    </div>
                )}

                {/* Header */}
                <div className="bg-gray-800/50 backdrop-blur-lg rounded-2xl p-6 border border-gray-700/50 mb-6">
                    <div className="flex items-start justify-between">
                        <div>
                            <h1 className="text-3xl font-bold text-white">{repo.name}</h1>
                            <a href={repo.html_url} target="_blank" rel="noopener noreferrer" className="text-purple-400 hover:text-purple-300">
                                {repo.full_name}
                            </a>
                            {repo.description && (
                                <p className="mt-2 text-gray-300">{repo.description}</p>
                            )}
                        </div>
                        <div className="flex gap-2">
                            <button
                                onClick={handleSync}
                                disabled={syncing}
                                className="px-4 py-2 bg-purple-500/20 text-purple-400 rounded-lg hover:bg-purple-500/30 disabled:opacity-50"
                            >
                                {syncing ? 'Syncing...' : 'Sync Now'}
                            </button>
                            <Link
                                href={`/repositories/${repoId}/settings`}
                                className="px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600"
                            >
                                Settings
                            </Link>
                            <button
                                onClick={handleDelete}
                                className="px-4 py-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30"
                            >
                                Remove
                            </button>
                        </div>
                    </div>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    {[
                        { label: 'Stars', value: repo.stars_count, icon: '⭐' },
                        { label: 'Forks', value: repo.forks_count, icon: '🔱' },
                        { label: 'Issues', value: repo.open_issues_count, icon: '📋' },
                        { label: 'Branches', value: branches.length, icon: '🌿' },
                    ].map((stat) => (
                        <div key={stat.label} className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50">
                            <div className="text-2xl mb-1">{stat.icon}</div>
                            <div className="text-2xl font-bold text-white">{stat.value}</div>
                            <div className="text-sm text-gray-400">{stat.label}</div>
                        </div>
                    ))}
                </div>

                {/* Branches */}
                <div className="bg-gray-800/50 backdrop-blur-lg rounded-2xl p-6 border border-gray-700/50">
                    <h2 className="text-xl font-semibold text-white mb-4">Branches</h2>
                    <div className="space-y-2">
                        {branches.map((branch) => (
                            <div key={branch.name} className="flex items-center justify-between p-3 bg-gray-700/30 rounded-lg">
                                <div className="flex items-center gap-2">
                                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                    </svg>
                                    <span className="text-white">{branch.name}</span>
                                    {branch.name === repo.default_branch && (
                                        <span className="px-2 py-0.5 text-xs bg-purple-500/20 text-purple-400 rounded-full">default</span>
                                    )}
                                </div>
                                {branch.protected && (
                                    <span className="px-2 py-0.5 text-xs bg-yellow-500/20 text-yellow-400 rounded-full">protected</span>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default function RepositoryDetailPage() {
    return (
        <ProtectedRoute>
            <RepositoryDetailContent />
        </ProtectedRoute>
    );
}
