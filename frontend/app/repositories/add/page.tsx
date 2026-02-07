'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { repositoriesApi } from '@/lib/api/repositories';
import { ProtectedRoute } from '@/components/auth';

function AddRepositoryContent() {
    const router = useRouter();
    const [fullName, setFullName] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        if (!fullName.includes('/')) {
            setError('Please enter repository in owner/repo format');
            return;
        }

        setLoading(true);
        try {
            const repo = await repositoriesApi.add(fullName);
            router.push(`/repositories/${repo.id}`);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to add repository');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center p-8">
            <div className="w-full max-w-lg">
                <div className="mb-8">
                    <Link href="/repositories" className="text-gray-400 hover:text-white flex items-center gap-2 mb-4">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                        </svg>
                        Back to Repositories
                    </Link>
                    <h1 className="text-3xl font-bold text-white">Add Repository</h1>
                    <p className="text-gray-400 mt-1">Connect a GitHub repository to Echo</p>
                </div>

                <div className="bg-gray-800/50 backdrop-blur-lg rounded-2xl p-8 border border-gray-700/50">
                    {error && (
                        <div className="mb-6 p-4 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div>
                            <label htmlFor="fullName" className="block text-sm font-medium text-gray-300 mb-2">
                                Repository
                            </label>
                            <div className="relative">
                                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500">
                                    github.com/
                                </span>
                                <input
                                    id="fullName"
                                    type="text"
                                    value={fullName}
                                    onChange={(e) => setFullName(e.target.value)}
                                    placeholder="owner/repository"
                                    className="w-full pl-28 pr-4 py-3 bg-gray-700/50 border border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-white placeholder-gray-400"
                                    required
                                />
                            </div>
                            <p className="mt-2 text-xs text-gray-500">
                                Enter the repository in owner/repo format (e.g., facebook/react)
                            </p>
                        </div>

                        <div className="bg-gray-700/30 rounded-lg p-4">
                            <h3 className="text-sm font-medium text-gray-300 mb-2">What happens next?</h3>
                            <ul className="space-y-2 text-sm text-gray-400">
                                <li className="flex items-center gap-2">
                                    <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                    </svg>
                                    Sync repository metadata from GitHub
                                </li>
                                <li className="flex items-center gap-2">
                                    <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                    </svg>
                                    Set up webhooks for real-time updates
                                </li>
                                <li className="flex items-center gap-2">
                                    <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                    </svg>
                                    Enable Echo AI agent for this repository
                                </li>
                            </ul>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-3 px-4 bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold rounded-lg hover:from-purple-600 hover:to-pink-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                        >
                            {loading ? 'Adding Repository...' : 'Add Repository'}
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
}

export default function AddRepositoryPage() {
    return (
        <ProtectedRoute>
            <AddRepositoryContent />
        </ProtectedRoute>
    );
}
