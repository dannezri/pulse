/**
 * Hook pour capturer et stocker toutes les requêtes API
 */

import { create } from 'zustand';

export type RequestMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
export type RequestStatus = 'pending' | 'success' | 'error';

export interface ApiRequest {
  id: string;
  method: RequestMethod;
  url: string;
  status: RequestStatus;
  statusCode?: number;
  timestamp: Date;
  duration?: number;
  requestBody?: any;
  responseBody?: any;
  error?: string;
}

interface ApiLoggerState {
  requests: ApiRequest[];
  addRequest: (request: Omit<ApiRequest, 'id' | 'timestamp'>) => void;
  updateRequest: (id: string, updates: Partial<ApiRequest>) => void;
  clearRequests: () => void;
}

export const useApiLogger = create<ApiLoggerState>((set) => ({
  requests: [],
  
  addRequest: (request) => {
    const newRequest: ApiRequest = {
      ...request,
      id: `${Date.now()}-${Math.random()}`,
      timestamp: new Date(),
    };
    
    set((state) => ({
      requests: [newRequest, ...state.requests].slice(0, 100), // Garder seulement les 100 dernières
    }));
    
    return newRequest.id;
  },
  
  updateRequest: (id, updates) => {
    set((state) => ({
      requests: state.requests.map((req) =>
        req.id === id ? { ...req, ...updates } : req
      ),
    }));
  },
  
  clearRequests: () => {
    set({ requests: [] });
  },
}));

/**
 * Wrapper pour fetch qui log automatiquement les requêtes
 */
export async function loggedFetch(
  url: string,
  options?: RequestInit
): Promise<Response> {
  const { addRequest, updateRequest } = useApiLogger.getState();
  
  const method = (options?.method || 'GET') as RequestMethod;
  const startTime = Date.now();
  
  const requestId = addRequest({
    method,
    url,
    status: 'pending',
    requestBody: options?.body ? JSON.parse(options.body as string) : undefined,
  });
  
  try {
    const response = await fetch(url, options);
    const duration = Date.now() - startTime;
    
    let responseBody;
    try {
      responseBody = await response.clone().json();
    } catch {
      // Si la réponse n'est pas du JSON, on l'ignore
    }
    
    updateRequest(requestId, {
      status: response.ok ? 'success' : 'error',
      statusCode: response.status,
      duration,
      responseBody,
      error: response.ok ? undefined : `HTTP ${response.status}`,
    });
    
    return response;
  } catch (error) {
    const duration = Date.now() - startTime;
    
    updateRequest(requestId, {
      status: 'error',
      duration,
      error: error instanceof Error ? error.message : 'Unknown error',
    });
    
    throw error;
  }
}
