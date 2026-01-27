/**
 * Client API avec logging automatique
 * Wrapper autour de fetch qui log toutes les requêtes
 */

import { useApiLogger } from '../hooks/useApiLogger';
import type { RequestMethod } from '../hooks/useApiLogger';

/**
 * Effectue une requête HTTP avec logging automatique
 */
export async function apiRequest<T = any>(
  url: string,
  options?: RequestInit
): Promise<T> {
  const { addRequest, updateRequest } = useApiLogger.getState();
  
  const method = (options?.method || 'GET') as RequestMethod;
  const startTime = Date.now();
  
  // Log la requête
  const requestId = addRequest({
    method,
    url,
    status: 'pending',
    requestBody: options?.body ? tryParseJSON(options.body as string) : undefined,
  });
  
  try {
    const response = await fetch(url, options);
    const duration = Date.now() - startTime;
    
    // Essayer de parser la réponse
    let responseBody;
    const contentType = response.headers.get('content-type');
    
    if (contentType?.includes('application/json')) {
      try {
        responseBody = await response.clone().json();
      } catch {
        // Si on ne peut pas parser, on ignore
      }
    }
    
    // Mettre à jour le log
    updateRequest(requestId, {
      status: response.ok ? 'success' : 'error',
      statusCode: response.status,
      duration,
      responseBody,
      error: response.ok ? undefined : `HTTP ${response.status} ${response.statusText}`,
    });
    
    // Si erreur HTTP, throw
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return responseBody as T;
  } catch (error) {
    const duration = Date.now() - startTime;
    
    // Mettre à jour le log avec l'erreur
    updateRequest(requestId, {
      status: 'error',
      duration,
      error: error instanceof Error ? error.message : 'Unknown error',
    });
    
    throw error;
  }
}

/**
 * Helpers pour les méthodes HTTP courantes
 */
export const api = {
  get: <T = any>(url: string, options?: Omit<RequestInit, 'method'>) =>
    apiRequest<T>(url, { ...options, method: 'GET' }),
  
  post: <T = any>(url: string, body?: any, options?: Omit<RequestInit, 'method' | 'body'>) =>
    apiRequest<T>(url, {
      ...options,
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    }),
  
  put: <T = any>(url: string, body?: any, options?: Omit<RequestInit, 'method' | 'body'>) =>
    apiRequest<T>(url, {
      ...options,
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    }),
  
  patch: <T = any>(url: string, body?: any, options?: Omit<RequestInit, 'method' | 'body'>) =>
    apiRequest<T>(url, {
      ...options,
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    }),
  
  delete: <T = any>(url: string, options?: Omit<RequestInit, 'method'>) =>
    apiRequest<T>(url, { ...options, method: 'DELETE' }),
};

/**
 * Essaie de parser du JSON, retourne undefined si échec
 */
function tryParseJSON(text: string): any {
  try {
    return JSON.parse(text);
  } catch {
    return undefined;
  }
}
