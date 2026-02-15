import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

export interface AuditStatus {
    audit_id: string;
    status: 'ready' | 'processing' | 'completed' | 'error';
    progress: number;
    step: string;
    result?: any;
    error?: string;
    report_path?: string;
}

export const uploadXml = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await axios.post(`${API_URL}/audit/upload`, formData);
    return response.data;
};

export const startAudit = async (auditId: string) => {
    const response = await axios.post(`${API_URL}/audit/start/${auditId}`);
    return response.data;
};

export const getAuditStatus = async (auditId: string): Promise<AuditStatus> => {
    const response = await axios.get(`${API_URL}/audit/status/${auditId}`);
    return response.data;
};

export const getDownloadUrl = (auditId: string) => {
    return `${API_URL}/audit/download/${auditId}`;
};

export interface InvoiceHeader {
    access_key: string;
    number: number;
    series: number;
    issue_date: string;
    emitter_name: string;
    emitter_cnpj: string;
    recipient_name: string;
    recipient_doc: string;
    total_products: number;
    total_invoice: number;
    total_icms: number;
    protocol_number: string;
}

export interface ConsistencyError {
    field: string;
    xml_value: string;
    sefaz_value: string;
    message: string;
}

export interface AuditItemDetails {
    product_description: string;
    quantity: number;
    unit_price: number;
    ncm: string;
    cest: string;
    cfop: string;
    cst: string;
    amount_total: number;
    tax_base: number;
    tax_rate: number;
    tax_value: number;
    mva_percent: number;
    sefaz_tax_value: number;
    sefaz_mva_percent: number;
    sefaz_benefit_value: number;
}

export interface AuditItem {
    item_index: number;
    product_code: string;
    product_name: string;
    status: 'compliant' | 'divergent';
    issues: string[];
    details?: AuditItemDetails; // [NEW]
}

export interface AuditResultsResponse {
    audit_id: string;
    summary: {
        total: number;
        compliant: number;
        divergent: number;
        consistency_issues?: number; // [NEW]
    };
    invoice_header?: InvoiceHeader;       // [NEW]
    consistency_errors?: ConsistencyError[]; // [NEW]
    items: AuditItem[];
}

export const getAuditResults = async (auditId: string): Promise<AuditResultsResponse> => {
    const response = await axios.get(`${API_URL}/audit/${auditId}/results`);
    return response.data;
};

export interface AuditSummary {
    id: string;
    nfe_key: string;
    status: string;
    created_at: string;
    completed_at: string | null;
    summary: {
        total: number;
        compliant: number;
        divergent: number;
    } | null;
}

export const getAudits = async (skip = 0, limit = 20): Promise<AuditSummary[]> => {
    const response = await axios.get(`${API_URL}/audits?skip=${skip}&limit=${limit}`);
    return response.data;
};
