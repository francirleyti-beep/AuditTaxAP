import React from 'react';
import { AlertTriangle, AlertCircle } from 'lucide-react';
import { ConsistencyError } from '../api';

interface Props {
    errors: ConsistencyError[];
}

const ConsistencyAlert: React.FC<Props> = ({ errors }) => {
    if (errors.length === 0) return null;

    return (
        <div className="bg-orange-50 dark:bg-orange-950/20 rounded-2xl border border-orange-200 dark:border-orange-900/50 overflow-hidden mb-6 shadow-sm">
            <div className="px-6 py-3 bg-orange-100 dark:bg-orange-900/30 border-b border-orange-200 dark:border-orange-900/50 flex items-center gap-2">
                <AlertTriangle size={18} className="text-orange-600 dark:text-orange-400" />
                <h3 className="text-xs font-black uppercase text-orange-800 dark:text-orange-300 tracking-widest">Aviso de Inconsistência Interna (XML)</h3>
            </div>
            
            <div className="p-6">
                <p className="text-sm text-orange-700 dark:text-orange-400 mb-4 font-medium italic">
                    Foram detectadas discrepâncias nos totais do XML ou na lógica tributária dos itens:
                </p>
                
                <div className="space-y-3">
                    {errors.map((error, idx) => (
                        <div key={idx} className="flex gap-4 p-4 bg-white dark:bg-slate-900 rounded-xl border border-orange-100 dark:border-orange-900/30 shadow-sm">
                            <div className="shrink-0 p-2 bg-orange-50 dark:bg-orange-950/40 rounded-lg h-fit">
                                <AlertCircle size={16} className="text-orange-600" />
                            </div>
                            <div>
                                <p className="text-[10px] font-black uppercase text-orange-500 tracking-widest leading-none mb-1">{error.field}</p>
                                <p className="text-sm font-bold text-slate-800 dark:text-slate-200 leading-tight mb-1">{error.message}</p>
                                <div className="flex gap-4 text-[11px] font-mono text-slate-500 dark:text-slate-400 mt-2">
                                    <span>Declarado: <span className="font-bold text-slate-700 dark:text-slate-300">{error.xml_value}</span></span>
                                    <span>Calculado: <span className="font-bold text-slate-700 dark:text-slate-300">{error.sefaz_value}</span></span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default ConsistencyAlert;
