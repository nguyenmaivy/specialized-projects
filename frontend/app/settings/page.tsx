"use client";

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/auth-context';
import * as authApi from '@/lib/auth-api';
import Link from 'next/link';
import { Settings, Shield, Key, Users, Trash2, UserPlus, ArrowLeft, Loader2 } from 'lucide-react';

export default function SettingsPage() {
    const { user } = useAuth();
    
    // Change Password State
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [passwordError, setPasswordError] = useState('');
    const [passwordSuccess, setPasswordSuccess] = useState('');
    const [isChangingPassword, setIsChangingPassword] = useState(false);

    // User Management State (Admins only)
    const [users, setUsers] = useState<any[]>([]);
    const [loadingUsers, setLoadingUsers] = useState(false);
    const [userError, setUserError] = useState('');

    useEffect(() => {
        if (user?.role === 'admin') {
            loadUsers();
        }
    }, [user]);

    const loadUsers = async () => {
        setLoadingUsers(true);
        try {
            const data = await authApi.getUsers();
            setUsers(data);
        } catch (err: any) {
            console.error(err);
            setUserError('Failed to load users');
        } finally {
            setLoadingUsers(false);
        }
    };

    const handleChangePassword = async (e: React.FormEvent) => {
        e.preventDefault();
        setPasswordError('');
        setPasswordSuccess('');
        
        if (newPassword !== confirmPassword) {
            setPasswordError('New passwords do not match');
            return;
        }
        
        setIsChangingPassword(true);
        try {
            await authApi.changePassword({
                current_password: currentPassword,
                new_password: newPassword
            });
            setPasswordSuccess('Password changed successfully');
            setCurrentPassword('');
            setNewPassword('');
            setConfirmPassword('');
        } catch (err: any) {
            setPasswordError(err.response?.data?.detail || 'Failed to change password');
        } finally {
            setIsChangingPassword(false);
        }
    };

    const handleDeleteUser = async (username: string) => {
        if (username === 'admin') {
            alert('Cannot delete the default admin user');
            return;
        }
        if (!confirm(`Are you sure you want to delete user ${username}?`)) {
            return;
        }

        try {
            await authApi.deleteUser(username);
            setUsers(users.filter(u => u.username !== username));
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Failed to delete user');
        }
    };

    if (!user) {
        return <div className="p-10 text-center">Loading...</div>;
    }

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col p-6">
            <div className="max-w-[1760px] mx-auto w-full space-y-6">
                
                {/* Header */}
                <div className="flex items-center gap-4 mb-8">
                    <Link href="/" className="p-2 bg-white border border-gray-200 hover:bg-gray-50 rounded-xl transition-colors shadow-sm">
                        <ArrowLeft className="w-5 h-5 text-gray-600" />
                    </Link>
                    <div>
                        <h1 className="text-3xl font-extrabold text-gray-900 flex items-center gap-3">
                            <Settings className="w-8 h-8 text-indigo-600" />
                            Account Settings
                        </h1>
                        <p className="text-gray-500 mt-1">Manage your security preferences and administrative controls</p>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    
                    {/* Security Column */}
                    <div className="lg:col-span-1 space-y-6">
                        
                        {/* Profile Card */}
                        <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
                            <div className="flex items-center gap-3 mb-4">
                                <div className="p-3 bg-indigo-50 rounded-xl">
                                    <Shield className="w-6 h-6 text-indigo-600" />
                                </div>
                                <div>
                                    <h2 className="text-lg font-bold text-gray-900">Your Profile</h2>
                                    <p className="text-sm text-gray-500">Current active session</p>
                                </div>
                            </div>
                            <div className="space-y-3">
                                <div className="flex justify-between items-center py-2 border-b border-gray-100">
                                    <span className="text-sm text-gray-500">Username</span>
                                    <span className="font-medium text-gray-900">{user.username}</span>
                                </div>
                                <div className="flex justify-between items-center py-2">
                                    <span className="text-sm text-gray-500">Role</span>
                                    <span className="px-2 py-1 bg-indigo-50 text-indigo-700 text-xs font-semibold rounded-md uppercase tracking-wider">
                                        {user.role}
                                    </span>
                                </div>
                            </div>
                        </div>

                        {/* Change Password Card */}
                        <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
                            <div className="flex items-center gap-3 mb-6">
                                <div className="p-3 bg-amber-50 rounded-xl">
                                    <Key className="w-6 h-6 text-amber-600" />
                                </div>
                                <div>
                                    <h2 className="text-lg font-bold text-gray-900">Change Password</h2>
                                    <p className="text-sm text-gray-500">Update your security credentials</p>
                                </div>
                            </div>

                            <form onSubmit={handleChangePassword} className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Current Password</label>
                                    <input
                                        type="password"
                                        required
                                        value={currentPassword}
                                        onChange={(e) => setCurrentPassword(e.target.value)}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">New Password (min 6 chars)</label>
                                    <input
                                        type="password"
                                        required
                                        minLength={6}
                                        value={newPassword}
                                        onChange={(e) => setNewPassword(e.target.value)}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Confirm New Password</label>
                                    <input
                                        type="password"
                                        required
                                        minLength={6}
                                        value={confirmPassword}
                                        onChange={(e) => setConfirmPassword(e.target.value)}
                                        className="w-full px-4 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
                                    />
                                </div>

                                {passwordError && (
                                    <div className="text-sm text-red-600 bg-red-50 p-3 rounded-lg border border-red-100">{passwordError}</div>
                                )}
                                {passwordSuccess && (
                                    <div className="text-sm text-green-600 bg-green-50 p-3 rounded-lg border border-green-100">{passwordSuccess}</div>
                                )}

                                <button
                                    type="submit"
                                    disabled={isChangingPassword}
                                    className="w-full py-2.5 px-4 bg-gray-900 hover:bg-gray-800 text-white rounded-xl font-medium transition-colors flex items-center justify-center gap-2"
                                >
                                    {isChangingPassword ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Update Password'}
                                </button>
                            </form>
                        </div>
                    </div>

                    {/* Admin Column */}
                    {user.role === 'admin' && (
                        <div className="lg:col-span-2">
                            <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm min-h-full">
                                <div className="flex items-center justify-between mb-6">
                                    <div className="flex items-center gap-3">
                                        <div className="p-3 bg-purple-50 rounded-xl">
                                            <Users className="w-6 h-6 text-purple-600" />
                                        </div>
                                        <div>
                                            <h2 className="text-lg font-bold text-gray-900">User Management</h2>
                                            <p className="text-sm text-gray-500">Administrator controls for system users</p>
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => alert("Registration endpoint is available via API: POST /auth/register")}
                                        className="flex items-center gap-2 px-4 py-2 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200 rounded-lg text-sm font-medium transition-colors"
                                    >
                                        <UserPlus className="w-4 h-4" />
                                        New User
                                    </button>
                                </div>

                                {loadingUsers ? (
                                    <div className="flex items-center justify-center p-12 text-gray-400">
                                        <Loader2 className="w-8 h-8 animate-spin" />
                                    </div>
                                ) : userError ? (
                                    <div className="p-6 text-center text-red-500 bg-red-50 rounded-xl border border-red-100">
                                        {userError}
                                    </div>
                                ) : (
                                    <div className="overflow-x-auto rounded-xl border border-gray-200">
                                        <table className="w-full text-left text-sm text-gray-600">
                                            <thead className="bg-gray-50 border-b border-gray-200 text-gray-700 text-xs uppercase font-semibold">
                                                <tr>
                                                    <th className="px-6 py-4">Username</th>
                                                    <th className="px-6 py-4">Role</th>
                                                    <th className="px-6 py-4 text-right">Actions</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-gray-100">
                                                {users.map((u, i) => (
                                                    <tr key={i} className="hover:bg-gray-50 transition-colors">
                                                        <td className="px-6 py-4 font-medium text-gray-900">
                                                            {u.username}
                                                            {u.username === user.username && (
                                                                <span className="ml-2 text-[10px] uppercase font-bold text-indigo-500 bg-indigo-50 px-2 py-0.5 rounded-full">You</span>
                                                            )}
                                                        </td>
                                                        <td className="px-6 py-4">
                                                            <span className={`px-2.5 py-1 text-xs font-semibold rounded-full border ${
                                                                u.role === 'admin' ? 'bg-purple-50 text-purple-700 border-purple-200' :
                                                                u.role === 'editor' ? 'bg-blue-50 text-blue-700 border-blue-200' :
                                                                'bg-gray-100 text-gray-600 border-gray-300'
                                                            }`}>
                                                                {u.role}
                                                            </span>
                                                        </td>
                                                        <td className="px-6 py-4 text-right">
                                                            <button 
                                                                onClick={() => handleDeleteUser(u.username)}
                                                                disabled={u.username === 'admin'}
                                                                className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                                                title={u.username === 'admin' ? 'Cannot delete default admin' : 'Delete user'}
                                                            >
                                                                <Trash2 className="w-4 h-4" />
                                                            </button>
                                                        </td>
                                                    </tr>
                                                ))}
                                                {users.length === 0 && (
                                                    <tr>
                                                        <td colSpan={3} className="px-6 py-8 text-center text-gray-500">No users found.</td>
                                                    </tr>
                                                )}
                                            </tbody>
                                        </table>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                    
                </div>
            </div>
        </div>
    );
}
