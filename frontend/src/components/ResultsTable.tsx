import React, { useState, useMemo } from 'react';
import { CheckCircle, AlertTriangle, ChevronDown, ChevronRight, Search, CheckSquare, Square, Save } from 'lucide-react';
import { AuditItem, AuditResultsResponse, toggleItemReview, finalizeAudit } from '../api';

interface ResultsTableProps {
    results: AuditResultsResponse;
    onUpdate?: () => void;
}

const ResultsTable: React.FC<ResultsTableProps> = ({ results, onUpdate }) => {
    const { items, audit_id, is_fully_reviewed } = results;
    const [filter, setFilter] = useState<'all' | 'compliant' | 'divergent'>('all');
    const [searchTerm, setSearchTerm] = useState('');
    const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());
    const [isFinalizing, setIsFinalizing] = useState(false);

    const toggleRow = (index: number) => {
        const newExpanded = new Set(expandedRows);
        if (newExpanded.has(index)) {
            newExpanded.delete(index);
        } else {
            newExpanded.add(index);
        }
        setExpandedRows(newExpanded);
    };

    const handleToggleReview = async (e: React.MouseEvent, itemIndex: number, currentStatus: boolean) => {
        e.stopPropagation();
        try {
            await toggleItemReview(audit_id, itemIndex, !currentStatus);
            if (onUpdate) onUpdate();
        } catch (error) {
            alert('Erro ao atualizar status do item');
        }
    };

    const handleFinalize = async () => {
        if (!allChecked) return;
        setIsFinalizing(true);
        try {
            await finalizeAudit(audit_id);
            if (onUpdate) onUpdate();
            alert('Auditoria finalizada com sucesso!');
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Erro ao finalizar auditoria');
        } finally {
            setIsFinalizing(false);
        }
    };

    const allChecked = useMemo(() => items.every(item => item.is_reviewed), [items]);

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
            <div className="p-2 md:p-4 border-b border-slate-100 flex flex-col lg:flex-row justify-between items-center gap-4 bg-slate-50">
                <div className="flex items-center gap-2 overflow-x-auto w-full lg:w-auto pb-2 lg:pb-0 no-scrollbar">
                    <div className="flex bg-white rounded-lg border border-slate-200 p-1 shadow-sm shrink-0">
                        <button
                            onClick={() => setFilter('all')}
                            className={`px-3 md:px-4 py-1.5 md:py-2 rounded-md text-xs md:text-sm font-medium transition-colors ${filter === 'all' ? 'bg-blue-100 text-blue-700' : 'text-slate-600 hover:bg-slate-50'}`}
                        >
                            Todos ({items.length})
                        </button>
                        <button
                            onClick={() => setFilter('compliant')}
                            className={`px-3 md:px-4 py-1.5 md:py-2 rounded-md text-xs md:text-sm font-medium transition-colors flex items-center gap-2 ${filter === 'compliant' ? 'bg-green-100 text-green-700' : 'text-slate-600 hover:bg-slate-50'}`}
                        >
                            <CheckCircle size={14} />
                            OK
                        </button>
                        <button
                            onClick={() => setFilter('divergent')}
                            className={`px-3 md:px-4 py-1.5 md:py-2 rounded-md text-xs md:text-sm font-medium transition-colors flex items-center gap-2 ${filter === 'divergent' ? 'bg-orange-100 text-orange-700' : 'text-slate-600 hover:bg-slate-50'}`}
                        >
                            <AlertTriangle size={14} />
                            Div
                        </button>
                    </div>
                </div>

                <div className="relative w-full lg:w-64">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <Search size={16} className="text-slate-400" />
                    </div>
                    <input
                        type="text"
                        placeholder="Buscar item..."
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
                                            <th className="px-4 py-3 w-10 text-center">OK</th>
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
                                                <td colSpan={10} className="px-6 py-12 text-center text-slate-500">
                                                    Nenhum item encontrado com os filtros atuais.
                                                </td>
                                            </tr>
                                        ) : (
                                            filteredItems.map((item) => (
                                                <React.Fragment key={item.item_index}>
                                                    <tr
                                                        onClick={() => toggleRow(item.item_index)}
                                                        className={`hover:bg-slate-50 cursor-pointer transition-colors ${expandedRows.has(item.item_index) ? 'bg-slate-50' : ''} ${item.is_reviewed ? 'bg-green-50/30' : ''}`}
                                                    >
                                                        <td className="px-6 py-4 text-slate-400">
                                                            {expandedRows.has(item.item_index) ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                                                        </td>
                                                        <td className="px-4 py-4 text-center">
                                                            <button 
                                                                onClick={(e) => handleToggleReview(e, item.item_index, item.is_reviewed)}
                                                                className={`transition-colors ${item.is_reviewed ? 'text-green-600' : 'text-slate-300 hover:text-slate-400'}`}
                                                                disabled={is_fully_reviewed}
                                                            >
                                                                {item.is_reviewed ? <CheckSquare size={20} /> : <Square size={20} />}
                                                            </button>
                                                        </td>
                                                        <td className="px-6 py-4 font-mono text-slate-600">#{item.item_index}</td>                                        <td className="px-6 py-4">
                                            <div className="font-medium text-slate-800">{item.product_name}</div>
                                            <div className="flex gap-3 mt-1">
                                                <span className="text-xs text-slate-500 font-mono">Cód: {item.product_code}</span>
                                                {item.details?.gtin && item.details.gtin !== 'SEM GTIN' && (
                                                    <span className="text-xs text-slate-500 font-mono">GTIN: {item.details.gtin}</span>
                                                )}
                                            </div>
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
                                                                <span className="block text-gray-500 text-xs">GTIN Tributário</span>
                                                                <span className="font-mono">{item.details?.gtin_tax || '-'}</span>
                                                            </div>
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
                                                                <span className="block text-gray-500 text-xs">UF Origem</span>
                                                                <span className="font-mono">{item.details?.origin_uf || '-'}</span>
                                                            </div>
                                                            <div>
                                                                <span className="block text-gray-500 text-xs">Base Calc. ICMS</span>
                                                                <span>{item.details?.tax_base ? new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(item.details.tax_base) : '-'}</span>
                                                            </div>
                                                            <div>
                                                                <span className="block text-gray-500 text-xs">Aliq. ICMS (Inter)</span>
                                                                <span>{item.details?.icms_interestadual_rate ? `${item.details.icms_interestadual_rate}%` : '-'}</span>
                                                            </div>
                                                            <div>
                                                                <span className="block text-gray-500 text-xs">Aliq. ICMS (Intra)</span>
                                                                <span>{item.details?.tax_rate ? `${item.details.tax_rate}%` : '-'}</span>
                                                            </div>
                                                            <div>
                                                                <span className="block text-gray-500 text-xs">Valor ICMS</span>
                                                                <span>{item.details?.tax_value ? new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(item.details.tax_value) : '-'}</span>
                                                            </div>
                                                        </div>

                                                        {/* ICMS ST Section (only if exists) */}
                                                        {(item.details?.icms_st_value || 0) > 0 && (
                                                            <div className="mt-4 pt-2 border-t border-slate-100">
                                                                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Substituição Tributária (ST)</span>
                                                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mt-1">
                                                                    <div>
                                                                        <span className="block text-gray-500 text-xs">Base ST</span>
                                                                        <span>{item.details?.icms_st_base ? new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(item.details.icms_st_base) : '-'}</span>
                                                                    </div>
                                                                    <div>
                                                                        <span className="block text-gray-500 text-xs">Aliq. ST</span>
                                                                        <span>{item.details?.icms_st_rate ? `${item.details.icms_st_rate}%` : '-'}</span>
                                                                    </div>
                                                                    <div>
                                                                        <span className="block text-gray-500 text-xs">Valor ST</span>
                                                                        <span className="font-medium">{item.details?.icms_st_value ? new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(item.details.icms_st_value) : '-'}</span>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        )}
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
                                                                    <span className="block text-gray-500 text-xs">Aliq. Inter (SEFAZ)</span>
                                                                    <span>{item.details.sefaz_interestadual_rate ? `${item.details.sefaz_interestadual_rate}%` : '-'}</span>
                                                                </div>
                                                                <div>
                                                                    <span className="block text-gray-500 text-xs">MVA Ajustada</span>
                                                                    <span>{item.details.sefaz_mva_percent}%</span>
                                                                </div>
                                                                <div>
                                                                    <span className="block text-gray-500 text-xs">Base ST (SEFAZ)</span>
                                                                    <span>{item.details.sefaz_st_base ? new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(item.details.sefaz_st_base) : '-'}</span>
                                                                </div>
                                                                <div>
                                                                    <span className="block text-gray-500 text-xs">Aliq. ST (SEFAZ)</span>
                                                                    <span>{item.details.sefaz_st_rate ? `${item.details.sefaz_st_rate}%` : '-'}</span>
                                                                </div>
                                                                <div>
                                                                    <span className="block text-gray-500 text-xs">Aliq. Interna (SEFAZ)</span>
                                                                    <span>{item.details.tax_rate}%</span>
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
                                                            <div className="overflow-hidden border border-red-100 rounded-lg">
                                                                <table className="w-full text-left text-xs">
                                                                    <thead className="bg-red-50 text-red-700 font-semibold">
                                                                        <tr>
                                                                            <th className="px-3 py-2">Campo</th>
                                                                            <th className="px-3 py-2">Valor XML</th>
                                                                            <th className="px-3 py-2">Valor SEFAZ</th>
                                                                            <th className="px-3 py-2">Mensagem</th>
                                                                        </tr>
                                                                    </thead>
                                                                    <tbody className="divide-y divide-red-50">
                                                                        {item.issues.map((issue, idx) => (
                                                                            <tr key={idx} className="bg-white">
                                                                                <td className="px-3 py-2 font-bold text-red-600 uppercase">{issue.field}</td>
                                                                                <td className="px-3 py-2 font-mono">{issue.xml_value}</td>
                                                                                <td className="px-3 py-2 font-mono">{issue.sefaz_value}</td>
                                                                                <td className="px-3 py-2 text-slate-600 italic">{issue.message}</td>
                                                                            </tr>
                                                                        ))}
                                                                    </tbody>
                                                                </table>
                                                            </div>
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
            <div className="bg-slate-50 px-4 md:px-6 py-4 border-t border-slate-200 flex flex-col sm:flex-row justify-between items-center gap-4">
                <span className="text-xs text-slate-500 order-2 sm:order-1">Exibindo {filteredItems.length} de {items.length} itens</span>
                
                <div className="flex items-center gap-4 w-full sm:w-auto order-1 sm:order-2">
                    {is_fully_reviewed ? (
                        <div className="flex items-center justify-center gap-2 px-4 py-2 bg-green-100 text-green-700 rounded-lg text-sm font-bold w-full sm:w-auto">
                            <CheckCircle size={18} />
                            Auditoria Finalizada
                        </div>
                    ) : (
                        <button
                            onClick={handleFinalize}
                            disabled={!allChecked || isFinalizing}
                            className={`flex items-center justify-center gap-2 px-6 py-3 sm:py-2 rounded-lg text-sm font-bold transition-all shadow-sm w-full sm:w-auto
                                ${allChecked 
                                    ? 'bg-blue-600 text-white hover:bg-blue-700 active:scale-95' 
                                    : 'bg-slate-200 text-slate-400 cursor-not-allowed'
                                }`}
                        >
                            {isFinalizing ? 'Processando...' : 'Finalizar Revisão'}
                            <Save size={16} />
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ResultsTable;
