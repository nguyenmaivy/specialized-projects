"use client";

import Dashboard from '@/components/Dashboard';
import LoginPage from '@/components/LoginPage';
import Link from 'next/link';
import { Users, LogOut, Shield, Settings } from 'lucide-react';
import { useAuth } from '@/lib/auth-context';

export default function Home() {
  const { isAuthenticated, isLoading, user, logout } = useAuth();

  // Show loading while checking auth state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex items-center gap-3">
          <svg className="animate-spin w-8 h-8 text-indigo-600" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <span className="text-gray-500 text-lg">Loading...</span>
        </div>
      </div>
    );
  }

  // Show login page if not authenticated
  if (!isAuthenticated) {
    return <LoginPage />;
  }

  // Show dashboard
  return (
    <main className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-[1760px] mx-auto">
        <header className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-extrabold text-gray-900 tracking-tight">Business Intelligence Dashboard</h1>
            <p className="text-gray-500 mt-2">AI-Powered Sales Forecasting & Analytics</p>
          </div>
          <div className="flex items-center gap-3">
            {/* User info badge */}
            <div className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-xl text-sm text-gray-600">
              <Shield className="w-4 h-4 text-indigo-500" />
              <span className="font-medium">{user?.username}</span>
              <span className="text-xs px-2 py-0.5 bg-indigo-50 text-indigo-600 rounded-full font-medium">
                {user?.role}
              </span>
            </div>

            <Link
              href="/customers"
              className="flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition-colors shadow-sm font-medium"
            >
              <Users className="w-5 h-5" />
              Customer Insights
            </Link>

            <Link
              href="/settings"
              className="flex items-center gap-2 px-4 py-3 bg-white border border-gray-200 text-gray-700 rounded-xl hover:bg-gray-50 hover:border-gray-300 transition-all shadow-sm font-medium"
            >
              <Settings className="w-5 h-5" />
              Settings
            </Link>

            {/* Logout button */}
            <button
              onClick={logout}
              className="flex items-center gap-2 px-4 py-3 bg-white border border-gray-200 text-gray-600 rounded-xl hover:bg-red-50 hover:text-red-600 hover:border-red-200 transition-all font-medium"
            >
              <LogOut className="w-5 h-5" />
              Logout
            </button>
          </div>
        </header>
        <Dashboard />
      </div>
    </main>
  );
}
