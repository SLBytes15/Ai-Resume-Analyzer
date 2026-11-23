/**
 * TalentLens Reusable API Error Handling Utility
 *
 * Safely parses and normalizes backend error responses (FastAPI detail strings,
 * Pydantic validation error arrays, structured error objects, HTTP status codes,
 * and network/timeout failures) into safe, human-readable strings.
 *
 * Guarantees that raw JavaScript objects, stack traces, SQL errors, or internal
 * implementation details are NEVER displayed to the user (no '[object Object]').
 */

export interface PydanticValidationError {
  loc?: Array<string | number>;
  msg?: string;
  type?: string;
  ctx?: Record<string, unknown>;
  input?: unknown;
}

export class ApiError extends Error {
  public status: number;
  public data: unknown;
  public isNetworkError: boolean;

  constructor(message: string, status: number = 0, data?: unknown, isNetworkError: boolean = false) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
    this.isNetworkError = isNetworkError;
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

/**
 * Checks if a string contains sensitive server or database details.
 */
function containsSensitiveDetails(text: string): boolean {
  const sensitivePatterns = [
    /select\s+.+\s+from/i,
    /insert\s+into/i,
    /update\s+.+\s+set/i,
    /delete\s+from/i,
    /sqlalchemy/i,
    /traceback\s+\(most recent call last\)/i,
    /psycopg/i,
    /asyncpg/i,
    /password_hash/i,
    /secret_key/i,
    /syntax error at or near/i,
    /pg_catalog/i,
  ];
  return sensitivePatterns.some((pattern) => pattern.test(text));
}

/**
 * Converts a camelCase or snake_case string into a capitalized Title Case string.
 */
function formatFieldName(fieldName: string): string {
  return fieldName
    .replace(/_/g, ' ')
    .replace(/([A-Z])/g, ' $1')
    .trim()
    .split(' ')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}

/**
 * Formats a FastAPI/Pydantic validation error item into a clean readable message.
 */
function formatPydanticItem(item: PydanticValidationError): string {
  if (!item || typeof item !== 'object') {
    return 'Invalid field value';
  }

  const rawMsg = typeof item.msg === 'string' ? item.msg : 'Invalid value';
  // Strip "Value error, " prefix often added by Pydantic validators
  const cleanMsg = rawMsg.replace(/^Value error,\s*/i, '');

  if (Array.isArray(item.loc) && item.loc.length > 0) {
    // Filter out root wrappers like "body", "query", "path"
    const relevantLocs = item.loc.filter(
      (loc) => typeof loc === 'string' && !['body', 'query', 'path', 'header'].includes(loc)
    );
    if (relevantLocs.length > 0) {
      const fieldName = formatFieldName(String(relevantLocs[relevantLocs.length - 1]));
      return `${fieldName}: ${cleanMsg}`;
    }
  }

  return cleanMsg;
}

/**
 * Returns a user-friendly default message for standard HTTP status codes.
 */
export function getStatusFallback(status: number): string {
  switch (status) {
    case 400:
      return 'The request was invalid. Please check your input and try again.';
    case 401:
      return 'Invalid email or password. Please check your credentials.';
    case 403:
      return 'You do not have permission to access this resource.';
    case 404:
      return 'The requested resource was not found.';
    case 409:
      return 'An account with this email already exists.';
    case 422:
      return 'Validation failed. Please verify the submitted information.';
    case 429:
      return 'Too many requests. Please wait a moment before trying again.';
    case 500:
      return 'An unexpected server error occurred. Please try again later.';
    case 502:
      return 'Gateway error. The server is temporarily unable to handle your request.';
    case 503:
      return 'Service temporarily unavailable. Please try again shortly.';
    case 504:
      return 'Gateway timeout. The server took too long to respond.';
    default:
      if (status >= 500) {
        return 'The service is temporarily unavailable. Please try again shortly.';
      }
      return 'An unexpected error occurred. Please try again.';
  }
}

/**
 * Extracts a safe, human-readable string from any API error payload.
 * NEVER returns "[object Object]".
 */
export function extractErrorMessage(data: unknown, status?: number, fallbackMessage?: string): string {
  const defaultFallback = fallbackMessage || (status ? getStatusFallback(status) : 'An unexpected error occurred');

  if (data === null || data === undefined) {
    return defaultFallback;
  }

  // 1. Primitive string detail or message
  if (typeof data === 'string') {
    const trimmed = data.trim();
    if (!trimmed || trimmed === '[object Object]') {
      return defaultFallback;
    }
    if (containsSensitiveDetails(trimmed)) {
      return status ? getStatusFallback(status) : 'A server error occurred. Please try again.';
    }
    return trimmed;
  }

  // 2. Objects containing FastAPI 'detail'
  if (typeof data === 'object') {
    const errorObj = data as Record<string, unknown>;

    // Case A: FastAPI detail is an array of validation errors (422)
    if (Array.isArray(errorObj.detail)) {
      if (errorObj.detail.length === 0) {
        return defaultFallback;
      }
      const formattedItems = errorObj.detail
        .map((item) => formatPydanticItem(item as PydanticValidationError))
        .filter((msg) => Boolean(msg && msg !== '[object Object]'));

      if (formattedItems.length > 0) {
        return formattedItems.join('. ') + '.';
      }
      return defaultFallback;
    }

    // Case B: FastAPI detail is a string
    if (typeof errorObj.detail === 'string' && errorObj.detail.trim()) {
      const trimmed = errorObj.detail.trim();
      if (trimmed === '[object Object]') {
        return defaultFallback;
      }
      if (containsSensitiveDetails(trimmed)) {
        return status ? getStatusFallback(status) : 'A server error occurred. Please try again.';
      }
      return trimmed;
    }

    // Case C: FastAPI detail is an object with nested message or error
    if (errorObj.detail && typeof errorObj.detail === 'object') {
      const nested = errorObj.detail as Record<string, unknown>;
      if (typeof nested.message === 'string' && nested.message.trim()) {
        return extractErrorMessage(nested.message, status, defaultFallback);
      }
      if (typeof nested.error === 'string' && nested.error.trim()) {
        return extractErrorMessage(nested.error, status, defaultFallback);
      }
    }

    // Case D: Top-level message or error property
    if (typeof errorObj.message === 'string' && errorObj.message.trim()) {
      return extractErrorMessage(errorObj.message, status, defaultFallback);
    }
    if (typeof errorObj.error === 'string' && errorObj.error.trim()) {
      return extractErrorMessage(errorObj.error, status, defaultFallback);
    }
  }

  return defaultFallback;
}

/**
 * Parses any caught exception (Error, ApiError, TypeError, network timeout) into a safe message.
 */
export function parseApiError(err: unknown, fallbackMessage?: string): string {
  if (err instanceof ApiError) {
    return err.message;
  }

  if (err instanceof Error) {
    const msg = err.message || '';

    // Network / offline errors
    if (
      err.name === 'TypeError' &&
      (msg.includes('Failed to fetch') || msg.includes('NetworkError') || msg.includes('Load failed'))
    ) {
      return 'Unable to connect to the server. Please check your network connection and verify the backend is running.';
    }

    // Timeout errors
    if (err.name === 'AbortError' || msg.toLowerCase().includes('timeout') || msg.toLowerCase().includes('timed out')) {
      return 'The request timed out. Please try again.';
    }

    // JSON syntax error (when backend returns HTML 502/503 page)
    if (err instanceof SyntaxError && msg.includes('JSON')) {
      return 'Invalid server response. The service may be temporarily unavailable.';
    }

    if (msg && msg !== '[object Object]') {
      if (containsSensitiveDetails(msg)) {
        return 'A server error occurred. Please try again.';
      }
      return msg;
    }
  }

  return fallbackMessage || 'An unexpected error occurred. Please try again.';
}

/**
 * Handles a fetch Response, parsing JSON safely and throwing an ApiError on failure.
 */
export async function handleApiResponse<T = unknown>(res: Response, fallbackMessage?: string): Promise<T> {
  let responseData: unknown = null;
  const contentType = res.headers.get('content-type') || '';

  if (contentType.includes('application/json')) {
    try {
      responseData = await res.json();
    } catch {
      responseData = null;
    }
  } else {
    try {
      responseData = await res.text();
    } catch {
      responseData = null;
    }
  }

  if (!res.ok) {
    const safeMessage = extractErrorMessage(responseData, res.status, fallbackMessage);
    throw new ApiError(safeMessage, res.status, responseData);
  }

  return responseData as T;
}
