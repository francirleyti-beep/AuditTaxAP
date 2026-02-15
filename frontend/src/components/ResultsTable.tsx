import React, { useState, useMemo } from 'react';
import { CheckCircle, AlertTriangle, ChevronDown, ChevronRight, Search, Filter } from 'lucide-react';
import { AuditItem } from '../api';

interface ResultsTableProps {
    items: AuditItem[];
}

type FilterType = 'all' | 'compliant' | 'divergent';

const ResultsTable: React.FC<ResultsTableProps> = ({ items }) => {
    const [filter, setFilter] = useState<FilterType>('all');
    const [searchTerm, setSearchTerm] = useState('');
    const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());

    const toggleRow = (index: number) => {
        const newExpanded = new Set(expandedRows);
        if (newExpanded.has(index)) {
            newExpanded.delete(index);
        } else {
            newExpanded.add(index);
        }
        setExpandedRows(newExpanded);
    };

    const filteredItems = useMemo(() => {
        return items.filter(item => {
            // Filter by status
            if (filter === 'compliant' && item.status !== 'compliant') return false;
            if (filter === 'divergent' && item.status !== 'divergent') return false;

            // Filter by search term
            if (searchTerm) {
                const searchLower = searchTerm.toLowerCase();
                return (
                    item.product_code.toLowerCase().includes(searchLower) ||
                    item.product_name.toLowerCase().includes(searchLower) ||
                    item.item_index.toString().includes(searchLower)
                );
            }

            return true;
        });
    }, [items, filter, searchTerm]);

    return (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            {/* Filters Header */}
            <div className="p-4 border-b border-slate-100 flex flex-col md:flex-row justify-between items-center gap-4 bg-slate-50">
                <div className="flex items-center gap-2">
                    <div className="flex bg-white rounded-lg border border-slate-200 p-1 shadow-sm">
                        <button
                            onClick={() => setFilter('all')}
                            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${filter === 'all' ? 'bg-blue-100 text-blue-700' : 'text-slate-600 hover:bg-slate-50'}`}
                        >
                            Todos ({items.length})
                        </button>
                        <button
                            onClick={() => setFilter('compliant')}
                            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${filter === 'compliant' ? 'bg-green-100 text-green-700' : 'text-slate-600 hover:bg-slate-50'}`}
                        >
                            <CheckCircle size={14} />
                            Conformes
                        </button>
                        <button
                            onClick={() => setFilter('divergent')}
                            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${filter === 'divergent' ? 'bg-orange-100 text-orange-700' : 'text-slate-600 hover:bg-slate-50'}`}
                        >
                            <AlertTriangle size={14} />
                            Divergentes
                        </button>
                    </div>
                </div>

                <div className="relative w-full md:w-64">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <Search size={16} className="text-slate-400" />
                    </div>
                    <input
                        type="text"
                        placeholder="Buscar item, código..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="block w-full pl-10 pr-3 py-2 border border-slate-200 rounded-lg text-sm placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                    />
                </div>
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                    <thead className="bg-slate-50 text-slate-500 font-medium">
                        <tr>
                            <th className="px-6 py-3 w-10"></th>
                            <th className="px-6 py-3 w-20">Item</th>
                            <th className="px-6 py-3">Produto</th>
                            <th className="px-4 py-3 text-right">Qtd</th>
                            <th className="px-4 py-3 text-right">V. Unit</th>
                            <th className="px-4 py-3 text-right">V. Total</th>
                            <th className="px-6 py-3 text-center">Status</th>
                            <th className="px-6 py-3 text-center">Divergências</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                        {filteredItems.length === 0 ? (
                            <tr>
                                <td colSpan={9} className="px-6 py-12 text-center text-slate-500">
                                    Nenhum item encontrado com os filtros atuais.
                                </td>
                            </tr>
                        ) : (
                            filteredItems.map((item) => (
                                <React.Fragment key={item.item_index}>
                                    <tr
                                        onClick={() => toggleRow(item.item_index)}
                                        className={`hover:bg-slate-50 cursor-pointer transition-colors ${expandedRows.has(item.item_index) ? 'bg-slate-50' : ''}`}
                                    >
                                        <td className="px-6 py-4 text-slate-400">
                                            {expandedRows.has(item.item_index) ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                                        </td>
                                        <td className="px-6 py-4 font-mono text-slate-600">#{item.item_index}</td>
                                        <td className="px-6 py-4">
                                            <div className="font-medium text-slate-800">{item.product_name}</div>
                                            <div className="text-xs text-slate-500 font-mono">Código: {item.product_code}</div>
                                        </td>
                                        <td className="px-4 py-4 text-right text-slate-700">
                                            {item.details?.quantity ? new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 0 }).format(item.details.quantity) : '-'}
                                        </td>
                                        <td className="px-4 py-4 text-right text-slate-700">
                                            {item.details?.unit_price ? new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(item.details.unit_price) : '-'}
                                        </td>
                                        <td className="px-4 py-4 text-right font-medium text-slate-900">
                                            {item.details?.amount_total ? new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(item.details.amount_total) : '-'}
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            {item.status === 'compliant' ? (
                                                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">
                                                    <CheckCircle size={12} />
                                                    Conforme
                                                </span>
                                            ) : (
                                                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-700">
                                                    <AlertTriangle size={12} />
                                                    Divergente
                                                </span>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 text-center text-slate-500">
                                            {item.issues.length > 0 ? (
                                                <span className="text-orange-600 font-medium">{item.issues.length}</span>
                                            ) : (
                                                <span className="text-green-600">-</span>
                                            )}
                                        </td>
                                    </tr>
                                    {expandedRows.has(item.item_index) && (
                                        <tr className="bg-slate-50">
                                            <td colSpan={9} className="px-6 py-4 pl-16">
                                                <div className="bg-white rounded-lg border border-slate-200 p-4 shadow-sm space-y-4">
                                                    {/* Detalhes Fiscais */}
                                                    <div>
                                                        <h4 className="font-semibold text-slate-800 mb-2 border-b pb-1">Dados Fiscais (XML)</h4>
                                                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                                                            <div>
                                                                <span className="block text-gray-500 text-xs">NCM</span>
                                                                <span className="font-mono">{item.details?.ncm || '-'}</span>
                                                            </div>
                                                            <div>
                                                                <span className="block text-gray-500 text-xs">CEST</span>
                                                                <span className="font-mono">{item.details?.cest || '-'}</span>
                                                            </div>
                                                            <div>
                                                                <span className="block text-gray-500 text-xs">CFOP</span>
                                                                <span className="font-mono">{item.details?.cfop || '-'}</span>
                                                            </div>
                                                            <div>
                                                                <span className="block text-gray-500 text-xs">CST</span>
                                                                <span className="font-mono">{item.details?.cst || '-'}</span>
                                                            </div>
                                                            <div>
                                                                <span className="block text-gray-500 text-xs">Base Calc. ICMS</span>
                                                                <span>{item.details?.tax_base ? new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(item.details.tax_base) : '-'}</span>
                                                            </div>
                                                            <div>
                                                                <span className="block text-gray-500 text-xs">Aliq. ICMS</span>
                                                                <span>{item.details?.tax_rate ? `${item.details.tax_rate}%` : '-'}</span>
                                                            </div>
                                                            <div>
                                                                <span className="block text-gray-500 text-xs">Valor ICMS</span>
                                                                <span>{item.details?.tax_value ? new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(item.details.tax_value) : '-'}</span>
                                                            </div>
                                                        </div>
                                                    </div>

                                                    {/* Comparação SEFAZ (se houver dados extras) */}
                                                    {item.details && (
                                                        <div>
                                                            <h4 className="font-semibold text-slate-800 mb-2 border-b pb-1">Dados Calculados SEFAZ</h4>
                                                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                                                                <div>
                                                                    <span className="block text-gray-500 text-xs">Valor Cobrado</span>
                                                                    <span className="font-medium text-blue-700">
                                                                        {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(item.details.sefaz_tax_value)}
                                                                    </span>
                                                                </div>
                                                                <div>
                                                                    <span className="block text-gray-500 text-xs">MVA Ajustada</span>
                                                                    <span>{item.details.sefaz_mva_percent}%</span>
                                                                </div>
                                                                {item.details.sefaz_benefit_value > 0 && (
                                                                    <div>
                                                                        <span className="block text-gray-500 text-xs">Benefício SUFRAMA</span>
                                                                        <span className="text-green-600">
                                                                            {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(item.details.sefaz_benefit_value)}
                                                                        </span>
                                                                    </div>
                                                                )}
                                                            </div>
                                                        </div>
                                                    )}

                                                    {/* Lista de Divergências */}
                                                    <div>
                                                        <h4 className="font-semibold text-slate-800 mb-2 border-b pb-1">Divergências Encontradas</h4>
                                                        {item.issues.length > 0 ? (
                                                            <ul className="space-y-2">
                                                                {item.issues.map((issue, idx) => (
                                                                    <li key={idx} className="flex items-start gap-2 text-sm text-slate-700 bg-red-50 p-2 rounded border border-red-100">
                                                                        <AlertTriangle size={16} className="text-red-500 mt-0.5 flex-shrink-0" />
                                                                        <span>{issue}</span>
                                                                    </li>
                                                                ))}
                                                            </ul>
                                                        ) : (
                                                            <p className="text-sm text-green-700 flex items-center gap-2">
                                                                <CheckCircle size={16} />
                                                                Nenhuma divergência encontrada. XML e SEFAZ conferem.
                                                            </p>
                                                        )}
                                                    </div>
                                                </div>
                                            </td>
                                        </tr>
                                    )}
                                </React.Fragment>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Footer Summary */}
            <div className="bg-slate-50 px-6 py-3 border-t border-slate-200 text-xs text-slate-500 flex justify-between">
                <span>Exibindo {filteredItems.length} de {items.length} itens</span>
                <span>AuditTax AP &copy; 2026</span>
            </div>
        </div>
    );
};

export default ResultsTable;
