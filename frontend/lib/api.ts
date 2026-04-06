import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

// Create axios instance with interceptor for JWT
const api = axios.create({
    baseURL: API_BASE_URL,
});

// Add auth token to every request automatically
api.interceptors.request.use((config) => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Handle 401 responses globally (token expired or invalid)
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401 && typeof window !== 'undefined') {
            localStorage.removeItem('auth_token');
            localStorage.removeItem('auth_user');
            window.location.reload();
        }
        return Promise.reject(error);
    }
);

export interface Filters {
    category?: string[];
    region?: string[];
    start_date?: string;
    end_date?: string;
}


export interface FilterOptions {
    categories: string[];
    regions: string[];
    min_date: string;
    max_date: string;
}

export interface KPIData {
    total_sales: number;
    total_profit: number;
    total_orders: number;
    avg_discount: number;
}

export interface SalesTrendItem {
    "Order Date": string;
    Sales: number;
}

export interface CategorySaleItem {
    Category: string;
    Sales: number;
}

export interface RegionSaleItem {
    Region: string;
    Sales: number;
}

export interface ForecastItem {
    ds: string;
    yhat: number;
    yhat_lower: number;
    yhat_upper: number;
}

export interface CustomerSegment {
    segment: string;
    customer_count: number;
    avg_recency: number;
    avg_frequency: number;
    avg_monetary: number;
}

export interface CustomerData {
    "Customer ID": string;
    "Customer Name": string;
    Recency: number;
    Frequency: number;
    Monetary: number;
    Segment: string;
}

export interface SegmentationResponse {
    segments: CustomerSegment[];
    customers: CustomerData[];
}

export interface HeatmapData {
    day: string;
    value: number;
}

export interface AnalysisRunResponse {
    analysis_run_id: string;
    dataset_id: string;
    status: string;
    filters: Filters;
}

export interface AIInsightWidget {
    id?: string;
    widget_type: 'insight' | 'risk' | 'what_if';
    severity: 'low' | 'medium' | 'high';
    title: string;
    content_markdown: string;
    evidence_json: Record<string, unknown>;
}

export interface AIInsightsResponse {
    analysis_run_id: string;
    executive_summary_markdown: string;
    widgets: AIInsightWidget[];
    suggested_prompts: string[];
}

export interface AIChatResponse {
    answer_markdown: string;
    followups: string[];
}

export type InsightDetailLevel = "short" | "medium" | "detailed";
export type InsightLocale = "vi" | "en";

export interface ChartSelectionPayload {
    x?: string | number;
    y?: number;
    label?: string;
    timestamp?: string;
}

export interface ChartInsightRequest {
    chartId: string;
    chartType: string;
    selection?: { point?: ChartSelectionPayload } | null;
    aggregates?: {
        sum?: number;
        mean?: number;
        min?: number;
        max?: number;
        stddev?: number;
        pct_change?: number;
        slope?: number;
    };
    filters: Record<string, unknown>;
    timeRange?: { from: string; to: string };
    detailLevel: InsightDetailLevel;
    locale: InsightLocale;
    context?: string;
}

export interface ChartInsightResponse {
    id: string;
    summary: string;
    highlights: string[];
    explanations: Array<{ text: string; metric_reference?: string | null }>;
    actions: string[];
    confidence: number;
    model_meta: { model_name: string; latency_ms: number };
    cached: boolean;
    status?: "succeeded" | "processing" | "failed";
}

export const fetchFilters = async (): Promise<FilterOptions> => {
    const response = await api.get<FilterOptions>('/filters');
    return response.data;
};

export const fetchKPIs = async (filters: Filters): Promise<KPIData> => {
    const response = await api.get<KPIData>('/kpis', { params: filters });
    return response.data;
};

export const fetchSalesTrend = async (filters: Filters): Promise<SalesTrendItem[]> => {
    const response = await api.get<SalesTrendItem[]>('/charts/sales-trend', { params: filters });
    return response.data;
};

export const fetchCategorySales = async (filters: Filters): Promise<CategorySaleItem[]> => {
    const response = await api.get<CategorySaleItem[]>('/charts/category-sales', { params: filters });
    return response.data;
};

export const fetchRegionSales = async (filters: Filters): Promise<RegionSaleItem[]> => {
    const response = await api.get<RegionSaleItem[]>('/charts/region-sales', { params: filters });
    return response.data;
};

export const fetchForecast = async (filters: Filters): Promise<ForecastItem[]> => {
    const response = await api.get<ForecastItem[]>('/forecast', { params: filters });
    return response.data;
};

export const fetchCustomerSegmentation = async (filters: Omit<Filters, 'start_date' | 'end_date'>): Promise<SegmentationResponse> => {
    const response = await api.get<SegmentationResponse>('/customer-segmentation', { params: filters });
    return response.data;
};

export const fetchSalesHeatmap = async (filters: Filters): Promise<HeatmapData[]> => {
    const response = await api.get<HeatmapData[]>('/sales-heatmap', { params: filters });
    return response.data;
};

export const runAnalysis = async (filters: Filters): Promise<AnalysisRunResponse> => {
    const response = await api.post<AnalysisRunResponse>('/analysis/run', {
        dataset_id: null,
        filters,
    });
    return response.data;
};

export const fetchAIInsights = async (analysisRunId: string): Promise<AIInsightsResponse> => {
    const response = await api.post<AIInsightsResponse>('/ai/insights', {
        analysis_run_id: analysisRunId,
    });
    return response.data;
};

export const sendAIChat = async (analysisRunId: string, message: string): Promise<AIChatResponse> => {
    const response = await api.post<AIChatResponse>('/ai/chat', {
        analysis_run_id: analysisRunId,
        message,
    });
    return response.data;
};

export const fetchChartInsight = async (payload: ChartInsightRequest): Promise<ChartInsightResponse> => {
    const response = await api.post<ChartInsightResponse>('/ai/insights', payload);
    return response.data;
};

export const getChartInsight = async (id: string): Promise<ChartInsightResponse> => {
    const response = await api.get<ChartInsightResponse>(`/ai/insights/${id}`);
    return response.data;
};

export const sendChartInsightFeedback = async (id: string, useful: boolean, comment?: string): Promise<{ ok: boolean }> => {
    const response = await api.post<{ ok: boolean }>(`/ai/insights/${id}/feedback`, { useful, comment });
    return response.data;
};
