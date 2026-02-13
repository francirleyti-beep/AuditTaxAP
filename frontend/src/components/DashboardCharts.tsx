import React, { useMemo } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import { AuditItem, AuditResultsResponse } from '../api';

interface DashboardChartsProps {
    results: AuditResultsResponse;
}

const COLORS = ['#10B981', '#EF4444']; // Emerald-500 (Compliant), Red-500 (Divergent)

export const DashboardCharts: React.FC<DashboardChartsProps> = ({ results }) => {
    const complianceData = useMemo(() => {
        if (!results.summary) return [];
        return [
            { name: 'Em Conformidade', value: results.summary.compliant },
            { name: 'Divergentes', value: results.summary.divergent },
        ];
    }, [results.summary]);

    const issuesData = useMemo(() => {
        const issueCounts: { [key: string]: number } = {};
        results.items.forEach(item => {
            item.issues.forEach(issue => {
                // Simplify issue text for chart (take first 30 chars or segment)
                const shortIssue = issue.length > 50 ? issue.substring(0, 50) + '...' : issue;
                issueCounts[shortIssue] = (issueCounts[shortIssue] || 0) + 1;
            });
        });

        return Object.entries(issueCounts)
            .map(([name, value]) => ({ name, value }))
            .sort((a, b) => b.value - a.value)
            .slice(0, 5); // Top 5 issues
    }, [results.items]);

    if (!results.summary) return null;

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            {/* Compliance Pie Chart */}
            <div className="bg-white dark:bg-slate-800 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700">
                <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-4">Visão Geral de Conformidade</h3>
                <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                            <Pie
                                data={complianceData}
                                cx="50%"
                                cy="50%"
                                innerRadius={60}
                                outerRadius={80}
                                paddingAngle={5}
                                dataKey="value"
                            >
                                {complianceData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Pie>
                            <Tooltip
                                contentStyle={{ backgroundColor: '#1E293B', borderColor: '#334155', color: '#F1F5F9' }}
                                itemStyle={{ color: '#F1F5F9' }}
                            />
                            <Legend wrapperStyle={{ paddingTop: '20px' }} />
                        </PieChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Top Issues Bar Chart */}
            <div className="bg-white dark:bg-slate-800 p-6 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700">
                <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-4">Top 5 Divergências</h3>
                <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={issuesData} layout="vertical" margin={{ left: 0, right: 30, top: 0, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#334155" opacity={0.3} />
                            <XAxis type="number" stroke="#94A3B8" />
                            <YAxis
                                dataKey="name"
                                type="category"
                                width={150}
                                tick={{ fontSize: 11, fill: '#94A3B8' }}
                                interval={0}
                            />
                            <Tooltip
                                cursor={{ fill: 'transparent' }}
                                contentStyle={{ backgroundColor: '#1E293B', borderColor: '#334155', color: '#F1F5F9' }}
                            />
                            <Bar dataKey="value" fill="#6366F1" radius={[0, 4, 4, 0]} barSize={20} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );
};
