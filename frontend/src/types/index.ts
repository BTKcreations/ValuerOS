// User & Auth
export interface User {
  id: string;
  email: string;
  full_name: string;
  license_number?: string;
  role: 'appraiser' | 'admin' | 'reviewer';
  is_active: boolean;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

// Property
export interface Property {
  id: string;
  address: string;
  city: string;
  state: string;
  zip_code: string;
  property_type: 'single_family' | 'multi_family' | 'condo' | 'commercial' | 'land';
  bedrooms?: number;
  bathrooms?: number;
  square_feet?: number;
  lot_size_sqft?: number;
  year_built?: number;
  latitude?: number;
  longitude?: number;
  owner_id: string;
  created_at: string;
  updated_at: string;
}

export interface PropertyCreate {
  address: string;
  city: string;
  state: string;
  zip_code: string;
  property_type: string;
  bedrooms?: number;
  bathrooms?: number;
  square_feet?: number;
  lot_size_sqft?: number;
  year_built?: number;
  latitude?: number;
  longitude?: number;
}

// Valuation
export type ValuationStatus = 'draft' | 'in_progress' | 'completed' | 'reviewed' | 'rejected';

export interface Valuation {
  id: string;
  property_id: string;
  appraiser_id: string;
  status: ValuationStatus;
  estimated_value?: number;
  confidence_score?: number;
  comparable_count?: number;
  methodology: 'sales_comparison' | 'income' | 'cost' | 'hybrid';
  notes?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export interface ValuationCreate {
  property_id: string;
  methodology: string;
  notes?: string;
}

export interface ComparableProperty {
  id: string;
  valuation_id: string;
  address: string;
  city: string;
  state: string;
  sale_price: number;
  sale_date: string;
  square_feet?: number;
  bedrooms?: number;
  bathrooms?: number;
  distance_miles?: number;
  price_per_sqft?: number;
  adjustment_factor?: number;
}

// Document
export type DocumentType = 'appraisal_report' | 'tax_assessment' | 'deed' | 'survey' | 'photo' | 'other';
export type DocumentStatus = 'uploaded' | 'processing' | 'ocr_complete' | 'failed';

export interface Document {
  id: string;
  valuation_id?: string;
  property_id?: string;
  filename: string;
  file_size: number;
  mime_type: string;
  document_type: DocumentType;
  status: DocumentStatus;
  ocr_text?: string;
  extracted_data?: Record<string, unknown>;
  storage_path: string;
  uploaded_by: string;
  created_at: string;
}

// Report
export type ReportStatus = 'draft' | 'generated' | 'reviewed' | 'final';

export interface Report {
  id: string;
  valuation_id: string;
  status: ReportStatus;
  content?: string;
  template_version: string;
  generated_by: string;
  created_at: string;
  updated_at: string;
  finalized_at?: string;
}

// API Responses
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ApiError {
  detail: string;
  code?: string;
  errors?: Record<string, string[]>;
}