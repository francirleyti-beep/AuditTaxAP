import axios from 'axios';

const API_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000/api' 
    : `${window.location.origin}/api`;

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
    total_st?: number;     // [NEW]
    protocol_number: string;
}

export interface ConsistencyError {
    field: string;
    xml_value: string;
    sefaz_value: string;
    message: string;
}

export interface AuditDifference {
    field: string;
    xml_value: string;
    sefaz_value: string;
    message: string;
}

export interface AuditItemDetails {
    product_description: string;
    gtin?: string;                 // [NEW]
    gtin_tax?: string;             // [NEW]
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
    origin_uf?: string;            // [NEW]
    icms_interestadual_rate?: number; // Do XML
    sefaz_interestadual_rate?: number; // [NEW] Da SEFAZ
    icms_st_value?: number;
    icms_st_base?: number;         // [NEW]
    icms_st_rate?: number;         // [NEW]
    sefaz_tax_value: number;
    sefaz_mva_percent: number;
    sefaz_benefit_value: number;
    sefaz_st_base?: number;        // [NEW]
    sefaz_st_rate?: number;        // [NEW]
}

export interface AuditItem {
    item_index: number;
    product_code: string;
    product_name: string;
    status: 'compliant' | 'divergent';
    issues: AuditDifference[];
    is_reviewed: boolean; // [NEW]
    details?: AuditItemDetails;
}

export interface AuditResultsResponse {
    audit_id: string;
    is_fully_reviewed: boolean; // [NEW]
    summary: {
        total: number;
        compliant: number;
        divergent: number;
        consistency_issues?: number;
    };
    invoice_header?: InvoiceHeader;
    consistency_errors?: ConsistencyError[];
    items: AuditItem[];
}

export const toggleItemReview = async (auditId: string, itemIndex: number, reviewed: boolean) => {
    const response = await axios.patch(`${API_URL}/audit/item/${auditId}/${itemIndex}/review?reviewed=${reviewed}`);
    return response.data;
};

export const finalizeAudit = async (auditId: string) => {
    const response = await axios.post(`${API_URL}/audit/${auditId}/finalize`);
    return response.data;
};

export const deleteAudit = async (auditId: string) => {
    const response = await axios.delete(`${API_URL}/audit/${auditId}`);
    return response.data;
};

export const retryAudit = async (auditId: string) => {
    const response = await axios.post(`${API_URL}/audit/${auditId}/retry`);
    return response.data;
};

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
    is_fully_reviewed: boolean; // [NEW]
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
