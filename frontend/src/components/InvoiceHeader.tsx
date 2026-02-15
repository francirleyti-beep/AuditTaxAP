import React from 'react';
import { InvoiceHeader as InvoiceHeaderType } from '../api';

interface Props {
    header: InvoiceHeaderType;
}

const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);
};

const formatDate = (dateStr: string) => {
    if (!dateStr) return "-";
    return new Date(dateStr).toLocaleString('pt-BR');
};

const InvoiceHeader: React.FC<Props> = ({ header }) => {
    return (
        <div className="bg-white shadow rounded-lg p-6 mb-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4 border-b pb-2">Dados da Nota Fiscal</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {/* Identificação */}
                <div className="space-y-1">
                    <p className="text-sm text-gray-500 font-medium">Chave de Acesso</p>
                    <p className="text-xs font-mono break-all">{header.access_key}</p>
                </div>
                <div>
                    <p className="text-sm text-gray-500 font-medium">Número / Série</p>
                    <p className="font-semibold">{header.number} / {header.series}</p>
                </div>
                <div>
                    <p className="text-sm text-gray-500 font-medium">Data Emissão</p>
                    <p>{formatDate(header.issue_date)}</p>
                </div>

                {/* Emitente */}
                <div className="col-span-1 md:col-span-2 lg:col-span-1">
                    <p className="text-sm text-gray-500 font-medium">Emitente</p>
                    <p className="font-semibold">{header.emitter_name}</p>
                    <p className="text-xs text-gray-600">CNPJ: {header.emitter_cnpj}</p>
                </div>

                {/* Destinatário */}
                <div className="col-span-1 md:col-span-2 lg:col-span-1">
                    <p className="text-sm text-gray-500 font-medium">Destinatário</p>
                    <p className="font-semibold">{header.recipient_name}</p>
                    <p className="text-xs text-gray-600">Doc: {header.recipient_doc}</p>
                </div>

                {/* Totais */}
                <div className="bg-gray-50 p-2 rounded col-span-1 md:col-span-2 lg:col-span-1">
                    <div className="flex justify-between items-center mb-1">
                        <span className="text-sm text-gray-600">Total Produtos:</span>
                        <span className="font-medium">{formatCurrency(header.total_products)}</span>
                    </div>
                    <div className="flex justify-between items-center mb-1">
                        <span className="text-sm text-gray-600">Total ICMS:</span>
                        <span className="font-medium">{formatCurrency(header.total_icms)}</span>
                    </div>
                    <div className="flex justify-between items-center border-t pt-1 mt-1">
                        <span className="text-sm font-bold text-gray-800">Total Nota:</span>
                        <span className="font-bold text-green-600">{formatCurrency(header.total_invoice)}</span>
                    </div>
                </div>
            </div>

            {header.protocol_number && (
                <div className="mt-4 pt-2 border-t text-xs text-gray-500">
                    Protocolo Autorização: {header.protocol_number}
                </div>
            )}
        </div>
    );
};

export default InvoiceHeader;
