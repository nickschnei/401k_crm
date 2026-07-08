import axios from 'axios';

const API_BASE = '/api/v1';

const getCookie = (name: string): string | null => {
  if (typeof document === 'undefined') return null;
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop()?.split(';').shift() || null;
  return null;
};

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = getCookie('auth_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface Prospect {
  employer_name: string;
  ein: string;
  total_assets: number;
  participants: number;
  status: string;
  notes: string;
  industry?: string;
  provider?: string;
  administrator?: string;
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
}

export interface FiduciaryAudit {
  ein: string;
  schedule_type?: string;
  total_assets?: number;
  active_participants?: number;
  total_eligible_employees?: number;
  admin_expenses?: number;
  corrective_distributions?: number;
  compliance_failed: boolean;
  participation_rate?: number;
  fee_ratio?: number;
  fee_red_flag: boolean;
  participation_red_flag: boolean;
  found: boolean;
}

export interface OutreachPitch {
  subject: string;
  body: string;
}

export interface DiscoveryFiling {
  employer_name: string;
  plan_name: string;
  total_assets: number;
  participants: number;
  dol_address: string;
  dol_city: string;
  dol_state: string;
  dol_zip: string;
  administrator: string;
  ein: string;
}

export interface TripStop {
  ein?: string;
  name: string;
  address: string;
  lat: number;
  lon: number;
  distance_from_last: number;
  leg_duration_minutes: number;
}

export interface TripResponse {
  total_distance_miles: number;
  total_duration_minutes: number;
  stops: TripStop[];
}

export const prospectsService = {
  getProspects: async (params?: {
    search?: string;
    min_assets?: number;
    max_assets?: number;
    min_participants?: number;
    max_participants?: number;
    status?: string;
    industry?: string;
    provider?: string;
    administrator?: string;
  }) => {
    const response = await api.get<Prospect[]>('/prospects/', { params });
    return response.data;
  },

  getProspectByEin: async (ein: string) => {
    const response = await api.get<Prospect>(`/prospects/${ein}`);
    return response.data;
  },

  updateProspectStatus: async (ein: string, status: string, notes: string) => {
    const response = await api.post<{ success: boolean; message: string }>(`/prospects/${ein}/status`, {
      status,
      notes,
    });
    return response.data;
  },

  enrichProspect: async (ein: string) => {
    const response = await api.post<Prospect>(`/prospects/${ein}/enrich`);
    return response.data;
  },
};

export const auditsService = {
  getAudit: async (ein: string) => {
    const response = await api.get<FiduciaryAudit>(`/audits/${ein}`);
    return response.data;
  },

  generatePitch: async (ein: string, employerName: string) => {
    const response = await api.post<OutreachPitch>(`/audits/${ein}/pitch`, null, {
      params: { employer_name: employerName },
    });
    return response.data;
  },

  getReportPdfUrl: (ein: string) => {
    return `${API_BASE}/audits/${ein}/pdf`;
  },
};

export const discoveryService = {
  getFilings: async (params?: {
    search?: string;
    min_assets?: number;
    max_assets?: number;
    min_participants?: number;
    max_participants?: number;
    industry?: string;
    provider?: string;
    administrator?: string;
    state?: string;
    schedule_type?: string;
    asset_ranges?: string;
    participant_ranges?: string;
    limit?: number;
    offset?: number;
  }) => {
    const response = await api.get<DiscoveryFiling[]>('/discovery/', { params });
    return response.data;
  },

  getSyncStatus: async () => {
    const response = await api.get<{
      is_running: boolean;
      last_run: string | null;
      error: string | null;
      summary: {
        files_scanned: number;
        new_records_added: number;
        audits_completed: number;
        execution_duration_sec: number;
        status: string;
      } | null;
    }>('/discovery/sync/status');
    return response.data;
  },

  triggerSync: async () => {
    const response = await api.post<{ success: boolean; message: string; task_id?: string }>('/discovery/sync');
    return response.data;
  },
};

export const tripService = {
  planTrip: async (req: {
    start_location: string;
    eins: string[];
    round_trip?: boolean;
  }) => {
    const response = await api.post<TripResponse>('/trip/planner', req);
    return response.data;
  },
};

export const authService = {
  login: async (req: LoginRequest) => {
    const response = await api.post<TokenResponse>('/auth/login', req);
    return response.data;
  },
  register: async (req: RegisterRequest) => {
    const response = await api.post<TokenResponse>('/auth/register', req);
    return response.data;
  },
  me: async () => {
    const response = await api.get<UserProfileResponse>('/auth/me');
    return response.data;
  },
};

export interface LoginRequest {
  email: string;
  password?: string;
}

export interface RegisterRequest {
  email: string;
  password?: string;
  first_name?: string;
  last_name?: string;
  company_name?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserProfileResponse {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  role: string;
  tenant_id?: string;
}

export default api;
