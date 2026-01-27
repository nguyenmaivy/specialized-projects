import Dashboard from '@/components/Dashboard';
import Link from 'next/link';
import { Users } from 'lucide-react';

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-[1760px] mx-auto">
        <header className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-extrabold text-gray-900 tracking-tight">Business Intelligence Dashboard</h1>
            <p className="text-gray-500 mt-2">AI-Powered Sales Forecasting & Analytics</p>
          </div>
          <Link
            href="/customers"
            className="flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition-colors shadow-sm font-medium"
          >
            <Users className="w-5 h-5" />
            Customer Insights
          </Link>
        </header>
        <Dashboard />
      </div>
    </main>
  );
}
