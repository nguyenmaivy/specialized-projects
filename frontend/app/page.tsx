import Dashboard from '@/components/Dashboard';

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <header className="mb-8">
          <h1 className="text-4xl font-extrabold text-gray-900 tracking-tight">Business Intelligence Dashboard</h1>
          <p className="text-gray-500 mt-2">AI-Powered Sales Forecasting & Analytics</p>
        </header>
        <Dashboard />
      </div>
    </main>
  );
}
