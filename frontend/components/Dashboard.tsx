"use client";

import { useEffect, useState } from 'react';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    ArcElement,
    BarElement
} from 'chart.js';
import { Line, Bar, Pie } from 'react-chartjs-2';
import * as api from '@/lib/api';
import { Filter, DollarSign, ShoppingCart, Percent, TrendingUp, Calendar, MapPin, Tag, LucideIcon } from 'lucide-react';



ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, ArcElement, BarElement);

export default function Dashboard() {
    const [loading, setLoading] = useState(true);
    const [filtersData, setFiltersData] = useState<api.FilterOptions | null>(null);

    // Selected Filters
    const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
    const [selectedRegions, setSelectedRegions] = useState<string[]>([]);
    const [startDate, setStartDate] = useState<string>('');
    const [endDate, setEndDate] = useState<string>('');

    // Dashboard Data
    const [kpis, setKpis] = useState<api.KPIData | null>(null);
    const [salesTrend, setSalesTrend] = useState<api.SalesTrendItem[]>([]);
    const [catSales, setCatSales] = useState<api.CategorySaleItem[]>([]);
    const [regionSales, setRegionSales] = useState<api.RegionSaleItem[]>([]);
    const [forecast, setForecast] = useState<api.ForecastItem[]>([]);

    // Load Filters Options
    useEffect(() => {
        api.fetchFilters().then(data => {
            setFiltersData(data);
            setStartDate(data.min_date);
            setEndDate(data.max_date);
        });
    }, []);

    // Fetch Data when filters change
    useEffect(() => {
        if (!startDate || !endDate) return;

        // eslint-disable-next-line react-hooks/exhaustive-deps
        setLoading(true);
        const params = {
            category: selectedCategories,
            region: selectedRegions,
            start_date: startDate,
            end_date: endDate
        };

        Promise.all([
            api.fetchKPIs(params),
            api.fetchSalesTrend(params),
            api.fetchCategorySales(params),
            api.fetchRegionSales(params),
            api.fetchForecast(params)
        ]).then(([kpiData, trendData, catData, regionData, forecastData]) => {
            setKpis(kpiData);
            setSalesTrend(trendData);
            setCatSales(catData);
            setRegionSales(regionData);
            setForecast(Array.isArray(forecastData) ? forecastData : []);
            setLoading(false);
        }).catch(err => {
            console.error(err);
            setLoading(false);
        });
    }, [selectedCategories, selectedRegions, startDate, endDate]);

    if (!filtersData) return <div className="p-10 text-center animate-pulse">Loading Dashboard...</div>;

    return (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* 🟢 Sidebar Filters */}
            <div className="lg:col-span-1 bg-white p-6 rounded-2xl shadow-sm border border-gray-100 h-fit sticky top-6">
                <div className="flex items-center gap-2 mb-6">
                    <Filter className="w-5 h-5 text-indigo-600" />
                    <h2 className="text-xl font-semibold text-gray-800">Filters</h2>
                </div>

                <div className="space-y-6">
                    {/* Date Range */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                            <Calendar className="w-4 h-4" /> Date Range
                        </label>
                        <div className="grid grid-cols-2 gap-2">
                            <input
                                type="date"
                                value={startDate}
                                onChange={e => setStartDate(e.target.value)}
                                className="w-full border rounded-lg p-2 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                            />
                            <input
                                type="date"
                                value={endDate}
                                onChange={e => setEndDate(e.target.value)}
                                className="w-full border rounded-lg p-2 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                            />
                        </div>
                    </div>

                    {/* Categories */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                            <Tag className="w-4 h-4" /> Categories
                        </label>
                        <div className="max-h-40 overflow-y-auto space-y-2 border p-3 rounded-lg bg-gray-50">
                            {filtersData.categories.map((cat: string) => (
                                <label key={cat} className="flex items-center gap-2 text-sm cursor-pointer hover:bg-gray-100 p-1 rounded">
                                    <input
                                        type="checkbox"
                                        checked={selectedCategories.includes(cat)}
                                        onChange={(e) => {
                                            if (e.target.checked) setSelectedCategories([...selectedCategories, cat]);
                                            else setSelectedCategories(selectedCategories.filter(c => c !== cat));
                                        }}
                                        className="rounded text-indigo-600 focus:ring-indigo-500"
                                    />
                                    {cat}
                                </label>
                            ))}
                        </div>
                    </div>

                    {/* Regions */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                            <MapPin className="w-4 h-4" /> Regions
                        </label>
                        <div className="space-y-2 border p-3 rounded-lg bg-gray-50">
                            {filtersData.regions.map((reg: string) => (
                                <label key={reg} className="flex items-center gap-2 text-sm cursor-pointer hover:bg-gray-100 p-1 rounded">
                                    <input
                                        type="checkbox"
                                        checked={selectedRegions.includes(reg)}
                                        onChange={(e) => {
                                            if (e.target.checked) setSelectedRegions([...selectedRegions, reg]);
                                            else setSelectedRegions(selectedRegions.filter(r => r !== reg));
                                        }}
                                        className="rounded text-indigo-600 focus:ring-indigo-500"
                                    />
                                    {reg}
                                </label>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* 🔵 Main Content */}
            <div className="lg:col-span-3 space-y-6">

                {/* KPIs */}
                {kpis && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        <KpiCard title="Total Sales" value={`$${kpis.total_sales.toLocaleString()}`} icon={DollarSign} color="bg-blue-50 text-blue-600" />
                        <KpiCard title="Total Profit" value={`$${kpis.total_profit.toLocaleString()}`} icon={TrendingUp} color="bg-green-50 text-green-600" />
                        <KpiCard title="Total Orders" value={kpis.total_orders} icon={ShoppingCart} color="bg-purple-50 text-purple-600" />
                        <KpiCard title="Avg Discount" value={`${(kpis.avg_discount * 100).toFixed(2)}%`} icon={Percent} color="bg-orange-50 text-orange-600" />
                    </div>
                )}

                {/* Sales Trend Chart */}
                <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                    <h3 className="text-lg font-semibold mb-4 text-gray-800">Daily Sales Trend</h3>
                    <div className="h-72">
                        <Line
                            data={{
                                labels: salesTrend.map(d => d['Order Date']),
                                datasets: [{
                                    label: 'Sales',
                                    data: salesTrend.map(d => d.Sales),
                                    borderColor: '#4f46e5',
                                    backgroundColor: 'rgba(79, 70, 229, 0.1)',
                                    tension: 0.3,
                                    fill: true
                                }]
                            }}
                            options={{ responsive: true, maintainAspectRatio: false }}
                        />
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Category Chart */}
                    <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                        <h3 className="text-lg font-semibold mb-4 text-gray-800">Sales by Category</h3>
                        <div className="h-64">
                            <Bar
                                data={{
                                    labels: catSales.map(d => d.Category),
                                    datasets: [{
                                        label: 'Sales',
                                        data: catSales.map(d => d.Sales),
                                        backgroundColor: ['#6366f1', '#8b5cf6', '#ec4899'],
                                        borderRadius: 6
                                    }]
                                }}
                                options={{ responsive: true, maintainAspectRatio: false }}
                            />
                        </div>
                    </div>

                    {/* Region Chart */}
                    <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                        <h3 className="text-lg font-semibold mb-4 text-gray-800">Regional Distribution</h3>
                        <div className="h-64 flex justify-center">
                            <Pie
                                data={{
                                    labels: regionSales.map(d => d.Region),
                                    datasets: [{
                                        data: regionSales.map(d => d.Sales),
                                        backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'],
                                        borderWidth: 0
                                    }]
                                }}
                                options={{ responsive: true, maintainAspectRatio: false }}
                            />
                        </div>
                    </div>
                </div>

                {/* Forecast Chart */}
                <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                    <div className="flex justify-between items-center mb-4">
                        <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
                            <TrendingUp className="w-5 h-5 text-purple-600" />
                            AI Sales Forecast (30 Days)
                        </h3>
                        <span className="text-xs font-medium px-2 py-1 bg-purple-100 text-purple-700 rounded-full">Prophet Model</span>
                    </div>

                    <div className="h-80">
                        {forecast.length > 0 ? (
                            <Line
                                data={{
                                    labels: forecast.map(d => d.ds),
                                    datasets: [
                                        {
                                            label: 'Forecast',
                                            data: forecast.map(d => d.yhat),
                                            borderColor: '#9333ea',
                                            borderDash: [5, 5],
                                            backgroundColor: 'rgba(147, 51, 234, 0.05)',
                                            fill: false,
                                            pointRadius: 0
                                        },
                                        {
                                            label: 'Upper Bound',
                                            data: forecast.map(d => d.yhat_upper),
                                            borderColor: 'rgba(146, 51, 234, 0.26)',
                                            backgroundColor: 'rgba(146, 51, 234, 0.26)',
                                            borderWidth: 1,
                                            pointRadius: 0,
                                            fill: '+1'
                                        },
                                        {
                                            label: 'Lower Bound',
                                            data: forecast.map(d => d.yhat_lower),
                                            borderColor: 'rgba(146, 51, 234, 0.45)',
                                            backgroundColor: 'rgba(146, 51, 234, 0.45)',
                                            borderWidth: 1,
                                            pointRadius: 0,
                                            fill: true
                                        }
                                    ]
                                }}
                                options={{
                                    responsive: true,
                                    maintainAspectRatio: false,
                                    plugins: {
                                        legend: { display: true },
                                        tooltip: { mode: 'index', intersect: false }
                                    }
                                }}
                            />
                        ) : (
                            <div className="h-full flex items-center justify-center text-gray-400">Not enough data for forecast</div>
                        )}
                    </div>
                </div>

            </div>
        </div>
    );
}

interface KpiCardProps {
    title: string;
    value: string | number;
    icon: LucideIcon;
    color: string;
}

function KpiCard({ title, value, icon: Icon, color }: KpiCardProps) {
    return (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center gap-4">
            <div className={`p-3 rounded-full ${color}`}>
                <Icon className="w-6 h-6" />
            </div>
            <div>
                <p className="text-sm text-gray-500 font-medium">{title}</p>
                <h4 className="text-2xl font-bold text-gray-900">{value}</h4>
            </div>
        </div>
    )
}
