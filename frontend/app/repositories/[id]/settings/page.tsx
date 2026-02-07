'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { repositoriesApi } from '@/lib/api/repositories';
import { Repository, RepositorySettings } from '@/lib/types/repository';
import { ProtectedRoute } from '@/components/auth';

function RepositorySettingsContent() {
    const params = useParams();
    const router = useRouter();
    const repoId = params.id as string;

    const [repo, setRepo] = useState<Repository | null>(null);
    const [settings, setSettings] = useState<RepositorySettings>({});
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    useEffect(() => {
        loadData();
    }, [repoId]);

    const loadData = async () => {
        try {
            const repoData = await repositoriesApi.get(repoId);
            setRepo(repoData);
            // Settings would be loaded from a separate endpoint in production
            setSettings({
                auto_sync: true,
                sync_interval_minutes: 60,
                notifications_enabled: true,
                notify_on_pr: true,
                notify_on_issues: true,
                agent_enabled: true,
            });
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load settings');
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        setSaving(true);
        setError('');
        setSuccess('');

        try {
            await repositoriesApi.update(repoId, settings);
            setSuccess('Settings saved successfully');
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to save settings');
        } finally {
            setSaving(false);
        }
    };

    const handleChange = (key: keyof RepositorySettings, value: boolean | number) => {
        setSettings((prev) => ({ ...prev, [key]: value }));
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center">
                <div className="animate-spin w-10 h-10 border-4 border-purple-500 border-t-transparent rounded-full"></div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-8">
            <div className="max-w-3xl mx-auto">
                <Link href={`/repositories/${repoId}`} className="text-gray-400 hover:text-white flex items-center gap-2 mb-6">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                    Back to {repo?.name}
                </Link>

                <h1 className="text-3xl font-bold text-white mb-8">Repository Settings</h1>

                {error && (
                    <div className="mb-6 p-4 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400">
                        {error}
                    </div>
                )}

                {success && (
                    <div className="mb-6 p-4 bg-green-500/10 border border-green-500/50 rounded-lg text-green-400">
                        {success}
                    </div>
                )}

                <div className="space-y-6">
                    {/* Sync Settings */}
                    <div className="bg-gray-800/50 backdrop-blur-lg rounded-2xl p-6 border border-gray-700/50">
                        <h2 className="text-xl font-semibold text-white mb-4">Sync Settings</h2>
                        <div className="space-y-4">
                            <label className="flex items-center justify-between">
                                <div>
                                    <div className="text-white">Auto Sync</div>
                                    <div className="text-sm text-gray-400">Automatically sync repository data</div>
                                </div>
                                <input
                                    type="checkbox"
                                    checked={settings.auto_sync}
                                    onChange={(e) => handleChange('auto_sync', e.target.checked)}
                                    className="w-5 h-5 rounded bg-gray-700 border-gray-600 text-purple-500 focus:ring-purple-500"
                                />
                            </label>
                            <div>
                                <label className="text-white">Sync Interval (minutes)</label>
                                <input
                                    type="number"
                                    value={settings.sync_interval_minutes}
                                    onChange={(e) => handleChange('sync_interval_minutes', parseInt(e.target.value))}
                                    min={15}
                                    max={1440}
                                    className="mt-1 w-full px-4 py-2 bg-gray-700/50 border border-gray-600 rounded-lg text-white"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Notification Settings */}
                    <div className="bg-gray-800/50 backdrop-blur-lg rounded-2xl p-6 border border-gray-700/50">
                        <h2 className="text-xl font-semibold text-white mb-4">Notifications</h2>
                        <div className="space-y-4">
                            <label className="flex items-center justify-between">
                                <div>
                                    <div className="text-white">Enable Notifications</div>
                                    <div className="text-sm text-gray-400">Receive notifications for this repository</div>
                                </div>
                                <input
                                    type="checkbox"
                                    checked={settings.notifications_enabled}
                                    onChange={(e) => handleChange('notifications_enabled', e.target.checked)}
                                    className="w-5 h-5 rounded bg-gray-700 border-gray-600 text-purple-500 focus:ring-purple-500"
                                />
                            </label>
                            <label className="flex items-center justify-between">
                                <span className="text-gray-300">Pull Requests</span>
                                <input
                                    type="checkbox"
                                    checked={settings.notify_on_pr}
                                    onChange={(e) => handleChange('notify_on_pr', e.target.checked)}
                                    className="w-5 h-5 rounded bg-gray-700 border-gray-600 text-purple-500 focus:ring-purple-500"
                                />
                            </label>
                            <label className="flex items-center justify-between">
                                <span className="text-gray-300">Issues</span>
                                <input
                                    type="checkbox"
                                    checked={settings.notify_on_issues}
                                    onChange={(e) => handleChange('notify_on_issues', e.target.checked)}
                                    className="w-5 h-5 rounded bg-gray-700 border-gray-600 text-purple-500 focus:ring-purple-500"
                                />
                            </label>
                        </div>
                    </div>

                    {/* Agent Settings */}
                    <div className="bg-gray-800/50 backdrop-blur-lg rounded-2xl p-6 border border-gray-700/50">
                        <h2 className="text-xl font-semibold text-white mb-4">Echo Agent</h2>
                        <div className="space-y-4">
                            <label className="flex items-center justify-between">
                                <div>
                                    <div className="text-white">Enable Agent</div>
                                    <div className="text-sm text-gray-400">Allow Echo AI to analyze and assist</div>
                                </div>
                                <input
                                    type="checkbox"
                                    checked={settings.agent_enabled}
                                    onChange={(e) => handleChange('agent_enabled', e.target.checked)}
                                    className="w-5 h-5 rounded bg-gray-700 border-gray-600 text-purple-500 focus:ring-purple-500"
                                />
                            </label>
                            <label className="flex items-center justify-between">
                                <div>
                                    <div className="text-gray-300">Auto-create Issues</div>
                                    <div className="text-sm text-gray-500">Create issues from social feedback</div>
                                </div>
                                <input
                                    type="checkbox"
                                    checked={settings.auto_create_issues}
                                    onChange={(e) => handleChange('auto_create_issues', e.target.checked)}
                                    className="w-5 h-5 rounded bg-gray-700 border-gray-600 text-purple-500 focus:ring-purple-500"
                                />
                            </label>
                        </div>
                    </div>

                    <button
                        onClick={handleSave}
                        disabled={saving}
                        className="w-full py-3 px-4 bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold rounded-lg hover:from-purple-600 hover:to-pink-600 disabled:opacity-50"
                    >
                        {saving ? 'Saving...' : 'Save Settings'}
                    </button>
                </div>
            </div>
        </div>
    );
}

export default function RepositorySettingsPage() {
    return (
        <ProtectedRoute>
            <RepositorySettingsContent />
        </ProtectedRoute>
    );
}
