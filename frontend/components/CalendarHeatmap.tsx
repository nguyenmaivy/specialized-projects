"use client";

import { useMemo, useState } from 'react';
import { HeatmapData } from '@/lib/api';
import { Calendar, ChevronLeft, ChevronRight } from 'lucide-react';

interface CalendarHeatmapProps {
    data: HeatmapData[];
    onInsight?: (type: 'point' | 'range', selectionData: any) => void;
}

export default function CalendarHeatmap({ data, onInsight }: CalendarHeatmapProps) {
    // Get all available months from data
    const availableMonths = useMemo(() => {
        const monthSet = new Map<string, { year: number; month: number; label: string }>();
        data.forEach(item => {
            const d = new Date(item.day);
            const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
            if (!monthSet.has(key)) {
                const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                monthSet.set(key, {
                    year: d.getFullYear(),
                    month: d.getMonth(),
                    label: `${months[d.getMonth()]} ${d.getFullYear()}`
                });
            }
        });
        return Array.from(monthSet.entries())
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([key, val]) => ({ key, ...val }));
    }, [data]);

    // Selected month index (default to latest month)
    const [selectedMonthIdx, setSelectedMonthIdx] = useState<number>(
        Math.max(availableMonths.length - 1, 0)
    );

    // Range selection state
    const [isDragging, setIsDragging] = useState(false);
    const [dragStart, setDragStart] = useState<string | null>(null);
    const [dragEnd, setDragEnd] = useState<string | null>(null);

    // Current selected month info
    const currentMonth = availableMonths[selectedMonthIdx] || null;

    // Filter data for selected month & build calendar grid
    const { filteredData, dataMap, maxValue, weeks, monthSales, monthDays, bestDay, avgDaily } = useMemo(() => {
        if (!currentMonth) {
            return { filteredData: [], dataMap: new Map(), maxValue: 1, weeks: [], monthSales: 0, monthDays: 0, bestDay: null as { day: string; value: number } | null, avgDaily: 0 };
        }

        // Filter data for selected month
        const filtered = data.filter(item => {
            const d = new Date(item.day);
            return d.getFullYear() === currentMonth.year && d.getMonth() === currentMonth.month;
        });

        const dMap = new Map(filtered.map(item => [item.day, item.value]));
        const mValue = Math.max(...filtered.map(d => d.value), 1);
        const mSales = filtered.reduce((sum, d) => sum + d.value, 0);

        // Find best day
        const best = filtered.length > 0
            ? filtered.reduce((max, d) => d.value > max.value ? d : max, filtered[0])
            : null;

        // Build calendar grid for the selected month
        const year = currentMonth.year;
        const month = currentMonth.month;
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0); // Last day of month

        const calWeeks: (Date | null)[][] = [];
        let week: (Date | null)[] = [];

        // Pad start with nulls (days before 1st of month)
        for (let i = 0; i < firstDay.getDay(); i++) {
            week.push(null);
        }

        // Fill in days of month
        for (let day = 1; day <= lastDay.getDate(); day++) {
            week.push(new Date(year, month, day));
            if (week.length === 7) {
                calWeeks.push(week);
                week = [];
            }
        }

        // Pad end with nulls
        if (week.length > 0) {
            while (week.length < 7) {
                week.push(null);
            }
            calWeeks.push(week);
        }

        return {
            filteredData: filtered,
            dataMap: dMap,
            maxValue: mValue,
            weeks: calWeeks,
            monthSales: mSales,
            monthDays: filtered.length,
            bestDay: best,
            avgDaily: filtered.length > 0 ? mSales / filtered.length : 0
        };
    }, [data, currentMonth]);

    const getColor = (value: number | undefined) => {
        if (value === undefined || value === 0) {
            return 'bg-gray-100';
        }
        const ratio = value / maxValue;
        if (ratio < 0.2) return 'bg-blue-100';
        if (ratio < 0.4) return 'bg-blue-300';
        if (ratio < 0.6) return 'bg-blue-500';
        if (ratio < 0.8) return 'bg-blue-700';
        return 'bg-blue-900';
    };

    const getDayShortName = (dayIndex: number) => {
        return ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][dayIndex];
    };

    const handleMouseDown = (dateStr: string) => {
        setIsDragging(true);
        setDragStart(dateStr);
        setDragEnd(dateStr);
    };

    const handleMouseEnter = (dateStr: string) => {
        if (isDragging) {
            setDragEnd(dateStr);
        }
    };

    const handleMouseUp = () => {
        if (isDragging && dragStart && dragEnd) {
            setIsDragging(false);
            if (dragStart === dragEnd) {
                // Point selection
                const val = dataMap.get(dragStart) || 0;
                onInsight?.('point', { x: dragStart, y: val });
            } else {
                // Range selection
                const dates = [new Date(dragStart), new Date(dragEnd)].sort((a, b) => a.getTime() - b.getTime());
                const startStr = `${dates[0].getFullYear()}-${String(dates[0].getMonth() + 1).padStart(2, '0')}-${String(dates[0].getDate()).padStart(2, '0')}`;
                const endStr = `${dates[1].getFullYear()}-${String(dates[1].getMonth() + 1).padStart(2, '0')}-${String(dates[1].getDate()).padStart(2, '0')}`;
                
                // compute aggregates for range
                let sum = 0;
                let count = 0;
                let min = Infinity;
                let max = -Infinity;
                
                data.forEach(d => {
                    if (d.day >= startStr && d.day <= endStr) {
                        sum += d.value;
                        count++;
                        if (d.value < min) min = d.value;
                        if (d.value > max) max = d.value;
                    }
                });
                
                if (count === 0) { min = 0; max = 0; }
                const mean = count > 0 ? sum / count : 0;

                onInsight?.('range', { start: startStr, end: endStr, sum, mean, min, max, count });
            }
        }
    };

    const canPrev = selectedMonthIdx > 0;
    const canNext = selectedMonthIdx < availableMonths.length - 1;

    return (
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
            {/* Header with month navigation */}
            <div className="flex items-center justify-between mb-5">
                <div className="flex items-center gap-2">
                    <Calendar className="w-5 h-5 text-indigo-600" />
                    <h3 className="text-lg font-semibold text-gray-800">Sales Heatmap Calendar</h3>
                </div>

                {availableMonths.length > 0 && (
                    <div className="flex items-center gap-2">
                        {/* Prev button */}
                        <button
                            onClick={() => canPrev && setSelectedMonthIdx(i => i - 1)}
                            disabled={!canPrev}
                            className={`p-1.5 rounded-lg transition-colors ${
                                canPrev
                                    ? 'hover:bg-indigo-50 text-indigo-600 cursor-pointer'
                                    : 'text-gray-300 cursor-not-allowed'
                            }`}
                        >
                            <ChevronLeft className="w-5 h-5" />
                        </button>

                        {/* Month selector dropdown */}
                        <select
                            value={selectedMonthIdx}
                            onChange={(e) => setSelectedMonthIdx(Number(e.target.value))}
                            className="px-3 py-1.5 rounded-lg border border-gray-200 bg-white text-sm font-medium text-gray-700 
                                       hover:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500
                                       cursor-pointer min-w-[140px] text-center appearance-none"
                        >
                            {availableMonths.map((m, idx) => (
                                <option key={m.key} value={idx}>
                                    {m.label}
                                </option>
                            ))}
                        </select>

                        {/* Next button */}
                        <button
                            onClick={() => canNext && setSelectedMonthIdx(i => i + 1)}
                            disabled={!canNext}
                            className={`p-1.5 rounded-lg transition-colors ${
                                canNext
                                    ? 'hover:bg-indigo-50 text-indigo-600 cursor-pointer'
                                    : 'text-gray-300 cursor-not-allowed'
                            }`}
                        >
                            <ChevronRight className="w-5 h-5" />
                        </button>
                    </div>
                )}
            </div>

            {data.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                    No data available for the selected period
                </div>
            ) : (
                <div className="flex gap-6">
                    {/* Calendar section */}
                    <div className="flex-1 min-w-0">
                        {/* Day of week headers */}
                        <div className="grid grid-cols-7 gap-1 mb-2">
                            {[0, 1, 2, 3, 4, 5, 6].map(day => (
                                <div key={day} className="h-8 flex items-center justify-center text-xs font-semibold text-gray-500 uppercase">
                                    {getDayShortName(day)}
                                </div>
                            ))}
                        </div>

                        {/* Calendar cells */}
                        {weeks.map((week, weekIndex) => (
                            <div key={weekIndex} className="grid grid-cols-7 gap-1 mb-1">
                                {week.map((date, dayIndex) => {
                                    const dateStr = date ?
                                        `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
                                        : null;
                                    const value = dateStr ? dataMap.get(dateStr) : undefined;

                                    let isSelected = false;
                                    if (dateStr && dragStart && dragEnd && isDragging) {
                                        const d = new Date(dateStr).getTime();
                                        const s = new Date(dragStart).getTime();
                                        const e = new Date(dragEnd).getTime();
                                        if (d >= Math.min(s, e) && d <= Math.max(s, e)) {
                                            isSelected = true;
                                        }
                                    }

                                    return (
                                        <div
                                            key={dayIndex}
                                            title={dateStr && value !== undefined ? `${dateStr}: $${value.toLocaleString()}` : dateStr || ''}
                                            onMouseDown={() => dateStr && handleMouseDown(dateStr)}
                                            onMouseEnter={() => dateStr && handleMouseEnter(dateStr)}
                                            onMouseUp={handleMouseUp}
                                            className={`
                                                aspect-square rounded-lg border flex items-center justify-center select-none
                                                text-xs cursor-pointer transition-all duration-200
                                                ${date ? getColor(value) : 'bg-transparent border-transparent'}
                                                ${date ? 'border-gray-200 hover:ring-2 hover:ring-indigo-400 hover:scale-105' : ''}
                                                ${date && value !== undefined && value > 0 ? 'text-white font-bold' : 'text-gray-400 font-normal'}
                                                ${isSelected ? 'ring-2 ring-indigo-500 scale-105 opacity-80' : ''}
                                            `}
                                        >
                                            {date && <span>{date.getDate()}</span>}
                                        </div>
                                    );
                                })}
                            </div>
                        ))}

                        {/* Legend */}
                        <div className="mt-5 flex items-center justify-between text-xs">
                            <span className="text-gray-600 font-medium">Less</span>
                            <div className="flex gap-1 mx-2">
                                <div className="w-4 h-4 rounded-sm bg-gray-100 border border-gray-200"></div>
                                <div className="w-4 h-4 rounded-sm bg-blue-100 border border-gray-200"></div>
                                <div className="w-4 h-4 rounded-sm bg-blue-300 border border-gray-200"></div>
                                <div className="w-4 h-4 rounded-sm bg-blue-500 border border-gray-200"></div>
                                <div className="w-4 h-4 rounded-sm bg-blue-700 border border-gray-200"></div>
                                <div className="w-4 h-4 rounded-sm bg-blue-900 border border-gray-200"></div>
                            </div>
                            <span className="text-gray-600 font-medium">More</span>
                        </div>
                    </div>

                    {/* Month stats - vertical sidebar */}
                    {currentMonth && filteredData.length > 0 && (
                        <div className="w-44 flex-shrink-0 flex flex-col gap-3 text-xs">
                            <div className="bg-indigo-50 rounded-xl p-3 text-center">
                                <div className="text-indigo-400 mb-1 font-medium">📅 {currentMonth.label}</div>
                                <div className="text-lg font-bold text-indigo-700">${Math.round(monthSales).toLocaleString()}</div>
                                <div className="text-indigo-400">Total Sales</div>
                            </div>
                            <div className="bg-green-50 rounded-xl p-3 text-center">
                                <div className="text-green-500 mb-1 font-medium">📊 Active Days</div>
                                <div className="text-lg font-bold text-green-700">{monthDays}</div>
                                <div className="text-green-400">out of {new Date(currentMonth.year, currentMonth.month + 1, 0).getDate()} days</div>
                            </div>
                            <div className="bg-amber-50 rounded-xl p-3 text-center">
                                <div className="text-amber-500 mb-1 font-medium">⭐ Best Day</div>
                                <div className="text-lg font-bold text-amber-700">${bestDay ? Math.round(bestDay.value).toLocaleString() : '0'}</div>
                                <div className="text-amber-400">{bestDay?.day || '-'}</div>
                            </div>
                            <div className="bg-purple-50 rounded-xl p-3 text-center">
                                <div className="text-purple-500 mb-1 font-medium">📈 Avg/Day</div>
                                <div className="text-lg font-bold text-purple-700">${Math.round(avgDaily).toLocaleString()}</div>
                                <div className="text-purple-400">per active day</div>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
