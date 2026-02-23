import React, { useState, useMemo } from 'react';
import { CheckCircle, AlertTriangle, ChevronDown, ChevronRight, Search, CheckSquare, Square, Save, Info, FileText } from 'lucide-react';
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

    const toggleAllRows = () => {
        if (expandedRows.size === filteredItems.length && filteredItems.length > 0) {
            setExpandedRows(new Set());
        } else {
            const allIndices = new Set(filteredItems.map(item => item.item_index));
            setExpandedRows(allIndices);
        }
    };

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
            if (filter === 'compliant' && item.status !== 'compliant') return false;
            if (filter === 'divergent' && item.status !== 'divergent') return false;

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

    const formatBRL = (val: number) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);

    return (
        <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden flex flex-col">
            {/* Table Controls */}
            <div className="p-4 border-b border-slate-100 dark:border-slate-800 flex flex-col md:flex-row justify-between items-center gap-4 bg-slate-50/50 dark:bg-slate-900/50">
                <div className="flex bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-1 shadow-sm shrink-0">
                    <button
                        onClick={() => setFilter('all')}
                        className={`px-4 py-2 rounded-lg text-xs md:text-sm font-bold transition-all ${filter === 'all' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-500 hover:bg-slate-50 dark:hover:bg-slate-700'}`}
                    >
                        Todos ({items.length})
                    </button>
                    <button
                        onClick={() => setFilter('compliant')}
                        className={`px-4 py-2 rounded-lg text-xs md:text-sm font-bold transition-all flex items-center gap-2 ${filter === 'compliant' ? 'bg-emerald-600 text-white shadow-md' : 'text-slate-500 hover:bg-slate-50 dark:hover:bg-slate-700'}`}
                    >
                        <CheckCircle size={14} /> OK
                    </button>
                    <button
                        onClick={() => setFilter('divergent')}
                        className={`px-4 py-2 rounded-lg text-xs md:text-sm font-bold transition-all flex items-center gap-2 ${filter === 'divergent' ? 'bg-orange-600 text-white shadow-md' : 'text-slate-500 hover:bg-slate-50 dark:hover:bg-slate-700'}`}
                    >
                        <AlertTriangle size={14} /> Divergentes
                    </button>
                </div>

                <div className="flex items-center gap-3 w-full md:w-auto">
                    <button
                        onClick={toggleAllRows}
                        className="px-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-all shadow-sm flex items-center gap-2 shrink-0"
                    >
                        {expandedRows.size > 0 && expandedRows.size === filteredItems.length ? (
                            <>Recolher Tudo</>
                        ) : (
                            <>Expandir Tudo</>
                        )}
                    </button>
                    
                    <div className="relative w-full md:w-80">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <Search size={16} className="text-slate-400" />
                        </div>
                        <input
                            type="text"
                            placeholder="Pesquisar código ou descrição..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="block w-full pl-10 pr-3 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm text-slate-700 dark:text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all shadow-sm"
                        />
                    </div>
                </div>
            </div>

            {/* Table Content */}
            <div className="overflow-x-auto">
                <table className="w-full text-left text-sm border-collapse">
                    <thead>
                        <tr className="bg-slate-50 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400 font-bold uppercase tracking-wider text-[10px] border-b border-slate-200 dark:border-slate-800">
                            <th className="px-6 py-4 w-12"></th>
                            <th className="px-2 py-4 w-12 text-center">Revisão</th>
                            <th className="px-6 py-4 w-20">Item</th>
                            <th className="px-6 py-4">Produto</th>
                            <th className="px-4 py-4 text-right">Qtd</th>
                            <th className="px-4 py-4 text-right">V. Unit</th>
                            <th className="px-4 py-4 text-right">V. Total</th>
                            <th className="px-6 py-4 text-center">Status</th>
                            <th className="px-6 py-4 text-center">Divergências</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                        {filteredItems.length === 0 ? (
                            <tr>
                                <td colSpan={10} className="px-6 py-16 text-center text-slate-400 dark:text-slate-600 italic">
                                    Nenhum item localizado com estes critérios.
                                </td>
                            </tr>
                        ) : (
                            filteredItems.map((item) => (
                                <React.Fragment key={item.item_index}>
                                    <tr
                                        onClick={() => toggleRow(item.item_index)}
                                        className={`group hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer transition-colors ${expandedRows.has(item.item_index) ? 'bg-slate-50 dark:bg-slate-800/80 shadow-inner' : ''} ${item.is_reviewed ? 'bg-emerald-50/20 dark:bg-emerald-900/10' : ''}`}
                                    >
                                        <td className="px-6 py-4 text-slate-400 dark:text-slate-600 group-hover:text-indigo-500 transition-colors">
                                            {expandedRows.has(item.item_index) ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
                                        </td>
                                        <td className="px-2 py-4 text-center">
                                            <button 
                                                onClick={(e) => handleToggleReview(e, item.item_index, item.is_reviewed)}
                                                className={`transition-all transform active:scale-90 ${item.is_reviewed ? 'text-emerald-500 dark:text-emerald-400' : 'text-slate-300 dark:text-slate-700 hover:text-slate-400'}`}
                                                disabled={is_fully_reviewed}
                                            >
                                                {item.is_reviewed ? <CheckSquare size={20} /> : <Square size={20} />}
                                            </button>
                                        </td>
                                        <td className="px-6 py-4 font-mono font-bold text-indigo-600 dark:text-indigo-400">#{item.item_index}</td>
                                        <td className="px-6 py-4">
                                            <div className="font-bold text-slate-800 dark:text-slate-100 leading-snug">{item.product_name}</div>
                                            <div className="flex gap-4 mt-1">
                                                <span className="text-[10px] text-slate-500 dark:text-slate-400 font-bold uppercase">Cód: {item.product_code}</span>
                                                {item.details?.gtin && item.details.gtin !== 'SEM GTIN' && (
                                                    <span className="text-[10px] text-slate-500 dark:text-slate-400 font-bold uppercase">EAN: {item.details.gtin}</span>
                                                )}
                                            </div>
                                        </td>
                                        <td className="px-4 py-4 text-right font-medium text-slate-600 dark:text-slate-300">
                                            {item.details?.quantity?.toLocaleString('pt-BR')}
                                        </td>
                                        <td className="px-4 py-4 text-right text-slate-600 dark:text-slate-300">
                                            {item.details?.unit_price ? formatBRL(item.details.unit_price) : '-'}
                                        </td>
                                        <td className="px-4 py-4 text-right font-bold text-slate-900 dark:text-slate-100">
                                            {item.details?.amount_total ? formatBRL(item.details.amount_total) : '-'}
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            {item.status === 'compliant' ? (
                                                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300">
                                                    Conforme
                                                </span>
                                            ) : (
                                                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-orange-100 dark:bg-orange-900/40 text-orange-700 dark:text-orange-300">
                                                    Divergente
                                                </span>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            {item.issues.length > 0 ? (
                                                <div className="flex items-center justify-center h-6 w-6 mx-auto rounded-full bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 text-xs font-bold ring-2 ring-white dark:ring-slate-900 shadow-sm">
                                                    {item.issues.length}
                                                </div>
                                            ) : (
                                                <div className="h-6 w-6 mx-auto rounded-full bg-emerald-50 dark:bg-emerald-900/10 text-emerald-500 opacity-30 flex items-center justify-center">
                                                    <CheckCircle size={14} />
                                                </div>
                                            )}
                                        </td>
                                    </tr>
                                    
                                    {/* EXPANDED DETAILS PANEL */}
                                    {expandedRows.has(item.item_index) && (
                                        <tr className="bg-slate-100/50 dark:bg-slate-950/50 animate-in slide-in-from-top-2 duration-300 overflow-hidden">
                                            <td colSpan={9} className="px-8 py-6">
                                                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                                    {/* Panel: XML Information */}
                                                    <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-5 shadow-sm space-y-5">
                                                        <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-700 pb-3">
                                                            <div className="flex items-center gap-2">
                                                                <FileText size={16} className="text-slate-400" />
                                                                <h4 className="text-xs font-bold uppercase text-slate-800 dark:text-white tracking-widest">Atributos XML (Contribuinte)</h4>
                                                            </div>
                                                            <span className="text-[10px] font-mono text-slate-400">ITEM #{item.item_index}</span>
                                                        </div>
                                                        
                                                        <div className="grid grid-cols-2 md:grid-cols-4 gap-y-6 gap-x-4">
                                                            {[
                                                                { label: 'NCM', value: item.details?.ncm },
                                                                { label: 'CEST', value: item.details?.cest },
                                                                { label: 'CFOP', value: item.details?.cfop },
                                                                { label: 'CST', value: item.details?.cst },
                                                                { label: 'UF Origem', value: item.details?.origin_uf },
                                                                { label: 'MVA XML', value: item.details?.mva_percent ? `${item.details.mva_percent}%` : '0%' },
                                                                { label: 'Aliq. ICMS', value: item.details?.tax_rate ? `${item.details.tax_rate}%` : '0%' },
                                                                { label: 'vICMS', value: item.details?.tax_value ? formatBRL(item.details.tax_value) : '-' }
                                                            ].map((field, i) => (
                                                                <div key={i}>
                                                                    <p className="text-[9px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-1">{field.label}</p>
                                                                    <p className="text-sm font-bold text-slate-700 dark:text-slate-200 font-mono">{field.value || '-'}</p>
                                                                </div>
                                                            ))}
                                                        </div>

                                                        {/* ST Highlight Section */}
                                                        {(item.details?.icms_st_value || 0) > 0 && (
                                                            <div className="bg-indigo-50/50 dark:bg-indigo-900/10 p-4 rounded-xl border border-indigo-100/50 dark:border-indigo-900/30">
                                                                <p className="text-[10px] font-bold text-indigo-600 dark:text-indigo-400 uppercase tracking-widest mb-3 flex items-center gap-2">
                                                                    <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse"></div>
                                                                    Substituição Tributária Destacada
                                                                </p>
                                                                <div className="grid grid-cols-3 gap-4">
                                                                    <div>
                                                                        <p className="text-[9px] text-indigo-400/80 uppercase font-bold mb-1 tracking-tight">Base ST</p>
                                                                        <p className="text-sm font-bold text-indigo-900 dark:text-indigo-200">{formatBRL(item.details!.icms_st_base!)}</p>
                                                                    </div>
                                                                    <div>
                                                                        <p className="text-[9px] text-indigo-400/80 uppercase font-bold mb-1 tracking-tight">Aliq. ST</p>
                                                                        <p className="text-sm font-bold text-indigo-900 dark:text-indigo-200">{item.details!.icms_st_rate}%</p>
                                                                    </div>
                                                                    <div>
                                                                        <p className="text-[9px] text-indigo-400/80 uppercase font-bold mb-1 tracking-tight">Valor ST</p>
                                                                        <p className="text-sm font-bold text-indigo-900 dark:text-indigo-200">{formatBRL(item.details!.icms_st_value!)}</p>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        )}
                                                    </div>

                                                    {/* Panel: SEFAZ Comparison */}
                                                    {item.details && (
                                                        <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-5 shadow-sm space-y-5">
                                                            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-700 pb-3">
                                                                <div className="flex items-center gap-2">
                                                                    <Info size={16} className="text-blue-500" />
                                                                    <h4 className="text-xs font-bold uppercase text-slate-800 dark:text-white tracking-widest">Memorial de Cálculo (SEFAZ-AP)</h4>
                                                                </div>
                                                                <span className="text-[10px] font-mono text-slate-400">DADOS EXTRAÍDOS</span>
                                                            </div>

                                                            <div className="grid grid-cols-3 gap-6">
                                                                <div className="col-span-3 lg:col-span-1 bg-blue-50/50 dark:bg-blue-900/10 p-3 rounded-xl border border-blue-100 dark:border-blue-900/20">
                                                                    <p className="text-[9px] font-bold text-blue-500 uppercase tracking-widest mb-1">Valor Cobrado</p>
                                                                    <p className="text-lg font-black text-blue-700 dark:text-blue-400">{formatBRL(item.details.sefaz_tax_value)}</p>
                                                                </div>
                                                                <div>
                                                                    <p className="text-[9px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-1">MVA Ajustada</p>
                                                                    <p className="text-sm font-bold text-slate-700 dark:text-slate-200">{item.details.sefaz_mva_percent}%</p>
                                                                </div>
                                                                <div>
                                                                    <p className="text-[9px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-1">Aliq. Interna</p>
                                                                    <p className="text-sm font-bold text-slate-700 dark:text-slate-200">{item.details.tax_rate}%</p>
                                                                </div>
                                                            </div>

                                                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                                                                <div>
                                                                    <span className="block text-slate-400 font-bold text-[9px] uppercase mb-1">Base de Cálculo ST</span>
                                                                    <span className="font-bold text-slate-700 dark:text-slate-200">{item.details.sefaz_st_base ? formatBRL(item.details.sefaz_st_base) : '-'}</span>
                                                                </div>
                                                                <div>
                                                                    <span className="block text-slate-400 font-bold text-[9px] uppercase mb-1">Aliq. Interestadual</span>
                                                                    <span className="font-bold text-slate-700 dark:text-slate-200">{item.details.sefaz_interestadual_rate ? `${item.details.sefaz_interestadual_rate}%` : '-'}</span>
                                                                </div>
                                                                {item.details.sefaz_benefit_value > 0 && (
                                                                    <div className="col-span-2">
                                                                        <span className="block text-emerald-500 font-bold text-[9px] uppercase mb-1">Benefício SUFRAMA Extraído</span>
                                                                        <span className="font-bold text-emerald-600 dark:text-emerald-400">{formatBRL(item.details.sefaz_benefit_value)}</span>
                                                                    </div>
                                                                )}
                                                            </div>
                                                        </div>
                                                    )}

                                                    {/* Panel: Issues/Audit Differences (Spans full width) */}
                                                    <div className="lg:col-span-2 mt-2">
                                                        <h4 className="text-xs font-bold uppercase text-slate-800 dark:text-white tracking-widest mb-4 flex items-center gap-2">
                                                            <div className="w-2 h-2 rounded-full bg-orange-500"></div>
                                                            Análise de Divergências
                                                        </h4>
                                                        {item.issues.length > 0 ? (
                                                            <div className="overflow-hidden border border-orange-100 dark:border-orange-900/30 rounded-2xl shadow-sm">
                                                                <table className="w-full text-left">
                                                                    <thead className="bg-orange-50 dark:bg-orange-900/20 text-orange-700 dark:text-orange-400 font-bold text-[10px] uppercase tracking-wider">
                                                                        <tr>
                                                                            <th className="px-5 py-3">Ponto de Auditoria</th>
                                                                            <th className="px-5 py-3">Valor XML</th>
                                                                            <th className="px-5 py-3">Valor SEFAZ-AP</th>
                                                                            <th className="px-5 py-3">Observação Técnica</th>
                                                                        </tr>
                                                                    </thead>
                                                                    <tbody className="divide-y divide-orange-50 dark:divide-orange-900/20 bg-white dark:bg-slate-800">
                                                                        {item.issues.map((issue, idx) => (
                                                                            <tr key={idx} className="hover:bg-orange-50/30 dark:hover:bg-orange-900/5 transition-colors">
                                                                                <td className="px-5 py-4">
                                                                                    <div className="flex flex-col">
                                                                                        <span className="text-[11px] font-black text-slate-900 dark:text-white uppercase leading-none mb-1">{issue.field.replace('_', ' ')}</span>
                                                                                        <span className="text-[10px] text-orange-600 dark:text-orange-500 font-bold uppercase tracking-tight">Discrepância Detectada</span>
                                                                                    </div>
                                                                                </td>
                                                                                <td className="px-5 py-4">
                                                                                    <div className="text-[13px] font-bold text-slate-600 dark:text-slate-300 font-mono bg-slate-100 dark:bg-slate-700/50 px-2 py-1 rounded inline-block">
                                                                                        {issue.xml_value}
                                                                                    </div>
                                                                                </td>
                                                                                <td className="px-5 py-4">
                                                                                    <div className="text-[13px] font-bold text-blue-600 dark:text-blue-400 font-mono bg-blue-50 dark:bg-blue-900/20 px-2 py-1 rounded inline-block">
                                                                                        {issue.sefaz_value}
                                                                                    </div>
                                                                                </td>
                                                                                <td className="px-5 py-4 text-xs text-slate-500 dark:text-slate-400 leading-relaxed italic border-l border-slate-100 dark:border-slate-700 ml-4">
                                                                                    {issue.message}
                                                                                </td>
                                                                            </tr>
                                                                        ))}
                                                                    </tbody>
                                                                </table>
                                                            </div>
                                                        ) : (
                                                            <div className="bg-emerald-50 dark:bg-emerald-900/20 rounded-2xl p-6 border border-emerald-100 dark:border-emerald-900/30 flex items-center justify-center gap-4">
                                                                <div className="p-3 bg-white dark:bg-slate-800 rounded-full text-emerald-500 shadow-sm border border-emerald-100 dark:border-emerald-900/50">
                                                                    <CheckCircle size={32} />
                                                                </div>
                                                                <div>
                                                                    <p className="text-sm font-black text-emerald-800 dark:text-emerald-300 uppercase tracking-widest leading-none mb-1">Item em Plena Conformidade</p>
                                                                    <p className="text-xs text-emerald-600 dark:text-emerald-500">Nenhuma divergência detectada no cruzamento de dados.</p>
                                                                </div>
                                                            </div>
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

            {/* Sticky Table Footer */}
            <div className="bg-slate-50 dark:bg-slate-900 px-6 py-6 border-t border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row justify-between items-center gap-6 mt-auto">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700">
                        <Info size={16} className="text-slate-400" />
                    </div>
                    <span className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-widest">
                        Exibindo {filteredItems.length} de {items.length} itens auditados
                    </span>
                </div>
                
                <div className="flex items-center gap-4 w-full sm:w-auto">
                    {is_fully_reviewed ? (
                        <div className="flex items-center justify-center gap-2 px-8 py-3 bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300 rounded-xl text-sm font-black uppercase tracking-widest w-full sm:w-auto border border-emerald-200 dark:border-emerald-800">
                            <CheckCircle size={18} />
                            Auditoria Finalizada
                        </div>
                    ) : (
                        <button
                            onClick={handleFinalize}
                            disabled={!allChecked || isFinalizing}
                            className={`flex items-center justify-center gap-3 px-10 py-3 rounded-xl text-sm font-black uppercase tracking-widest transition-all shadow-xl w-full sm:w-auto
                                ${allChecked 
                                    ? 'bg-indigo-600 hover:bg-indigo-700 text-white active:scale-95 shadow-indigo-600/30' 
                                    : 'bg-slate-200 dark:bg-slate-800 text-slate-400 dark:text-slate-600 cursor-not-allowed border border-slate-300 dark:border-slate-700'
                                }`}
                        >
                            {isFinalizing ? 'Processando...' : 'Finalizar Revisão'}
                            <Save size={18} />
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ResultsTable;
