import React from 'react';
import { InvoiceHeader as InvoiceHeaderType } from '../api';
import { FileText, Building2, User, Hash, Calendar, DollarSign } from 'lucide-react';

interface Props {
    header: InvoiceHeaderType;
}

const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);
};

const formatDate = (dateStr: string) => {
    if (!dateStr) return "-";
    return new Date(dateStr).toLocaleDateString('pt-BR');
};

const InvoiceHeader: React.FC<Props> = ({ header }) => {
    return (
        <div className="bg-white dark:bg-slate-800/50 rounded-2xl border border-slate-200 dark:border-slate-700 overflow-hidden mb-6 shadow-sm transition-all">
            <div className="bg-slate-50 dark:bg-slate-800 px-6 py-3 border-b border-slate-200 dark:border-slate-700 flex items-center gap-2">
                <FileText size={18} className="text-blue-600 dark:text-blue-400" />
                <h2 className="text-sm font-bold text-slate-700 dark:text-slate-200 uppercase tracking-tight">Detalhes do Documento Fiscal</h2>
            </div>
            
            <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                    {/* ID & Date */}
                    <div className="space-y-4">
                        <div className="flex items-start gap-3">
                            <div className="p-2 bg-blue-50 dark:bg-blue-900/30 rounded-lg text-blue-600 dark:text-blue-400">
                                <Hash size={18} />
                            </div>
                            <div>
                                <p className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Número / Série</p>
                                <p className="text-sm font-bold text-slate-700 dark:text-slate-200">{header.number} / {header.series}</p>
                            </div>
                        </div>
                        <div className="flex items-start gap-3">
                            <div className="p-2 bg-indigo-50 dark:bg-indigo-900/30 rounded-lg text-indigo-600 dark:text-indigo-400">
                                <Calendar size={18} />
                            </div>
                            <div>
                                <p className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Emissão</p>
                                <p className="text-sm font-bold text-slate-700 dark:text-slate-200">{formatDate(header.issue_date)}</p>
                            </div>
                        </div>
                    </div>

                    {/* Emitter */}
                    <div className="space-y-4">
                        <div className="flex items-start gap-3">
                            <div className="p-2 bg-slate-100 dark:bg-slate-700 rounded-lg text-slate-600 dark:text-slate-300">
                                <Building2 size={18} />
                            </div>
                            <div className="min-w-0">
                                <p className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Emitente</p>
                                <p className="text-sm font-bold text-slate-700 dark:text-slate-200 truncate" title={header.emitter_name}>{header.emitter_name}</p>
                                <p className="text-xs text-slate-500 font-mono mt-0.5">{header.emitter_cnpj}</p>
                            </div>
                        </div>
                    </div>

                    {/* Recipient */}
                    <div className="space-y-4">
                        <div className="flex items-start gap-3">
                            <div className="p-2 bg-slate-100 dark:bg-slate-700 rounded-lg text-slate-600 dark:text-slate-300">
                                <User size={18} />
                            </div>
                            <div className="min-w-0">
                                <p className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Destinatário</p>
                                <p className="text-sm font-bold text-slate-700 dark:text-slate-200 truncate" title={header.recipient_name}>{header.recipient_name}</p>
                                <p className="text-xs text-slate-500 font-mono mt-0.5">{header.recipient_doc}</p>
                            </div>
                        </div>
                    </div>

                    {/* Totals - High Priority Card */}
                    <div className="bg-slate-900 dark:bg-blue-600 p-4 rounded-xl text-white shadow-lg shadow-blue-600/20">
                        <div className="flex items-center gap-2 mb-3 border-b border-white/10 pb-2">
                            <DollarSign size={16} />
                            <span className="text-[10px] uppercase font-bold tracking-widest opacity-80">Totais da Nota</span>
                        </div>
                        <div className="space-y-2">
                            <div className="flex justify-between text-xs">
                                <span className="opacity-70">ICMS Normal:</span>
                                <span className="font-medium">{formatCurrency(header.total_icms)}</span>
                            </div>
                            {header.total_st && header.total_st > 0 && (
                                <div className="flex justify-between text-xs">
                                    <span className="opacity-70">ICMS ST:</span>
                                    <span className="font-medium">{formatCurrency(header.total_st)}</span>
                                </div>
                            )}
                            <div className="flex justify-between text-base font-bold pt-1 border-t border-white/20 mt-1">
                                <span>Total:</span>
                                <span>{formatCurrency(header.total_invoice)}</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div className="mt-6 pt-4 border-t border-slate-100 dark:border-slate-700/50">
                   <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                            <span className="text-[10px] uppercase font-bold text-slate-400">Chave de Acesso:</span>
                            <span className="text-[11px] font-mono text-slate-600 dark:text-slate-400 select-all">{header.access_key}</span>
                        </div>
                        {header.protocol_number && (
                            <span className="text-[10px] font-medium text-slate-400 italic">Protocolo: {header.protocol_number}</span>
                        )}
                   </div>
                </div>
            </div>
        </div>
    );
};

export default InvoiceHeader;
