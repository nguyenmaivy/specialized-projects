"use client";

import { useEffect, useState } from 'react';
import { Pie, Bubble } from 'react-chartjs-2';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    Title,
    Tooltip,
    Legend,
    ArcElement
} from 'chart.js';
import * as api from '@/lib/api';
import { Users, TrendingUp, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

ChartJS.register(CategoryScale, LinearScale, PointElement, Title, Tooltip, Legend, ArcElement);

export default function CustomersPage() {
    const [loading, setLoading] = useState(true);
    const [segmentationData, setSegmentationData] = useState<api.SegmentationResponse | null>(null);

    useEffect(() => {
        setLoading(true);
        api.fetchCustomerSegmentation({})
            .then(data => {
                setSegmentationData(data);
                setLoading(false);
            })
            .catch(err => {
                console.error(err);
                setLoading(false);
            });
    }, []);

    if (loading) {
        return <div className="p-10 text-center animate-pulse">Loading Customer Insights...</div>;
    }

    if (!segmentationData) {
        return <div className="p-10 text-center text-red-500">Failed to load customer data</div>;
    }

    // Prepare data for segment distribution pie chart
    const segmentColors: Record<string, string> = {
        'Champions': '#10b981',
        'Loyal': '#3b82f6',
        'At Risk': '#f59e0b',
        'New Customers': '#8b5cf6'
    };

    const pieData = {
        labels: segmentationData.segments.map(s => s.segment),
        datasets: [{
            data: segmentationData.segments.map(s => s.customer_count),
            backgroundColor: segmentationData.segments.map(s => segmentColors[s.segment] || '#6b7280'),
            borderWidth: 0
        }]
    };

    // Prepare data for RFM bubble chart (Chart.js format)
    const bubbleData = {
        datasets: Object.entries(
            segmentationData.customers.reduce((acc, customer) => {
                if (!acc[customer.Segment]) {
                    acc[customer.Segment] = [];
                }
                acc[customer.Segment].push({
                    x: customer.Recency,
                    y: customer.Monetary,
                    r: Math.min(Math.max(customer.Frequency * 2, 3), 30) // Bubble radius based on frequency, capped
                });
                return acc;
            }, {} as Record<string, Array<{ x: number; y: number; r: number }>>)
        ).map(([segment, data]) => ({
            label: segment,
            data: data,
            backgroundColor: segmentColors[segment] ? `${segmentColors[segment]}80` : '#6b728080',
            borderColor: segmentColors[segment] || '#6b7280',
            borderWidth: 1
        }))
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 p-6">
            <div className="max-w-[1760px] mx-auto space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Link href="/" className="p-2 hover:bg-white rounded-lg transition-colors">
                            <ArrowLeft className="w-6 h-6 text-gray-600" />
                        </Link>
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                                <Users className="w-8 h-8 text-indigo-600" />
                                Customer Intelligence
                            </h1>
                            <p className="text-gray-600 mt-1">RFM Analysis & Customer Segmentation</p>
                        </div>
                    </div>
                </div>

                {/* Segment Distribution */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                        <h3 className="text-lg font-semibold mb-4 text-gray-800">Customer Segment Distribution</h3>
                        <div className="h-80 flex justify-center items-center">
                            <Pie
                                data={pieData}
                                options={{
                                    responsive: true,
                                    maintainAspectRatio: false,
                                    plugins: {
                                        legend: {
                                            position: 'bottom'
                                        }
                                    }
                                }}
                            />
                        </div>
                    </div>

                    {/* Segment Statistics Table */}
                    <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                        <h3 className="text-lg font-semibold mb-4 text-gray-800">Segment Statistics</h3>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="border-b border-gray-200">
                                        <th className="text-left py-3 px-2 font-semibold text-gray-700">Segment</th>
                                        <th className="text-right py-3 px-2 font-semibold text-gray-700">Customers</th>
                                        <th className="text-right py-3 px-2 font-semibold text-gray-700">Avg Recency</th>
                                        <th className="text-right py-3 px-2 font-semibold text-gray-700">Avg Frequency</th>
                                        <th className="text-right py-3 px-2 font-semibold text-gray-700">Avg Revenue</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {segmentationData.segments.map((segment) => (
                                        <tr key={segment.segment} className="border-b border-gray-100 hover:bg-gray-50">
                                            <td className="py-3 px-2">
                                                <span
                                                    className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium"
                                                    style={{
                                                        backgroundColor: `${segmentColors[segment.segment]}20`,
                                                        color: segmentColors[segment.segment]
                                                    }}
                                                >
                                                    {segment.segment}
                                                </span>
                                            </td>
                                            <td className="text-right py-3 px-2 font-medium">{segment.customer_count}</td>
                                            <td className="text-right py-3 px-2 text-gray-600">{segment.avg_recency.toFixed(0)} days</td>
                                            <td className="text-right py-3 px-2 text-gray-600">{segment.avg_frequency.toFixed(1)} orders</td>
                                            <td className="text-right py-3 px-2 text-gray-600">${segment.avg_monetary.toFixed(0)}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                {/* RFM Bubble Chart */}
                <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                    <div className="flex items-center gap-2 mb-4">
                        <TrendingUp className="w-5 h-5 text-purple-600" />
                        <h3 className="text-lg font-semibold text-gray-800">RFM Analysis: Recency vs Monetary Value</h3>
                        <span className="text-xs text-gray-500 ml-auto">(Bubble size = Purchase Frequency)</span>
                    </div>
                    <div className="h-[500px]">  {/* thay cho h-96 */}

                        <Bubble
                            data={bubbleData}
                            options={{
                                responsive: true,
                                maintainAspectRatio: false,
                                layout: {
                                    padding: {
                                        top: 40,
                                        right: 40,
                                        bottom: 60,
                                        left: 40
                                    }
                                },
                                scales: {
                                    x: {
                                        offset: true,
                                        min: -50,
                                        title: {
                                            display: true,
                                            text: 'Recency (days since last purchase)'
                                        }
                                    },
                                    y: {
                                        offset: true,
                                        title: {
                                            display: true,
                                            text: 'Monetary Value ($)'
                                        }
                                    }
                                },
                                plugins: {
                                    legend: {
                                        position: 'bottom'
                                    },
                                    tooltip: {
                                        callbacks: {
                                            label: function (context) {
                                                const label = context.dataset.label || '';
                                                const x = context.parsed.x;
                                                const y = context.parsed.y;
                                                const r = (context.raw as { r: number }).r;

                                                // Handle null/undefined values
                                                if (x == null || y == null) {
                                                    return `${label}: No data`;
                                                }

                                                return `${label}: Recency ${x} days, Revenue ${y.toFixed(0)}, Frequency ${(r / 2).toFixed(0)} orders`;
                                            }
                                        }
                                    }
                                }
                            }}
                        />
                    </div>
                    <div className="mt-4 p-4 bg-indigo-50 rounded-lg">
                        <p className="text-sm text-gray-700">
                            <strong>How to read this chart:</strong> Lower recency (left side) means recent purchases.
                            Higher monetary value (top) means bigger spenders. Larger bubbles indicate more frequent buyers.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
