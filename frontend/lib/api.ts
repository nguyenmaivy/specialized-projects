import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

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

export const fetchFilters = async (): Promise<FilterOptions> => {
    const response = await axios.get<FilterOptions>(`${API_BASE_URL}/filters`);
    return response.data;
};

export const fetchKPIs = async (filters: Filters): Promise<KPIData> => {
    const response = await axios.get<KPIData>(`${API_BASE_URL}/kpis`, { params: filters });
    return response.data;
};

export const fetchSalesTrend = async (filters: Filters): Promise<SalesTrendItem[]> => {
    const response = await axios.get<SalesTrendItem[]>(`${API_BASE_URL}/charts/sales-trend`, { params: filters });
    return response.data;
};

export const fetchCategorySales = async (filters: Filters): Promise<CategorySaleItem[]> => {
    const response = await axios.get<CategorySaleItem[]>(`${API_BASE_URL}/charts/category-sales`, { params: filters });
    return response.data;
};

export const fetchRegionSales = async (filters: Filters): Promise<RegionSaleItem[]> => {
    const response = await axios.get<RegionSaleItem[]>(`${API_BASE_URL}/charts/region-sales`, { params: filters });
    return response.data;
};

export const fetchForecast = async (filters: Filters): Promise<ForecastItem[]> => {
    const response = await axios.get<ForecastItem[]>(`${API_BASE_URL}/forecast`, { params: filters });
    return response.data;
};
