const API_PREFIX = '/api';

export class ApiError extends Error {
  status: number;
  data: any;
  code?: string;

  constructor(status: number, message: string, data?: any, code?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
    this.code = code;
  }
}

function errorMessage(data: any, fallback: string): { message: string; code?: string } {
  // Backend envelope: { error: { code, message, details } }
  if (data && typeof data === 'object') {
    const err = (data as any).error;
    if (err && typeof err === 'object') {
      const details = err.details || {};
      const fieldBits = Array.isArray((details as any).fields)
        ? (details as any).fields.map((f: any) => f.reason || f.msg).filter(Boolean)
        : [];
      const suffix = fieldBits.length ? `: ${fieldBits.join('; ')}` : '';
      return {
        message: `${err.message || fallback}${suffix}`,
        code: err.code,
      };
    }
    if (typeof (data as any).detail === 'string') return { message: (data as any).detail };
    if (typeof (data as any).message === 'string') return { message: (data as any).message };
  }
  return { message: fallback };
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('token');
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };

  const response = await fetch(`${API_PREFIX}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 204) {
    return {} as T;
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const { message, code } = errorMessage(
      data,
      response.status === 401
        ? 'You must sign in to continue.'
        : 'An error occurred during request'
    );
    throw new ApiError(response.status, message, data, code);
  }

  return data as T;
}

export const api = {
  get: <T>(endpoint: string) => request<T>(endpoint, { method: 'GET' }),
  post: <T>(endpoint: string, body?: any) =>
    request<T>(endpoint, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    }),
  patch: <T>(endpoint: string, body?: any) =>
    request<T>(endpoint, {
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined,
    }),
  delete: <T>(endpoint: string) => request<T>(endpoint, { method: 'DELETE' }),
};
