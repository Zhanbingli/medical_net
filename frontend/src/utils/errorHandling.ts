import axios from 'axios';

/**
 * Extract a user-friendly error message from various error types
 */
export const getErrorMessage = (error: unknown, fallbackMessage: string): string => {
  // Handle Axios errors
  if (axios.isAxiosError(error)) {
    // Server responded with error status
    if (error.response) {
      const data = error.response.data;

      // Check for common error message fields
      if (typeof data === 'object' && data !== null) {
        if ('message' in data && typeof data.message === 'string') {
          return data.message;
        }
        if ('error' in data && typeof data.error === 'string') {
          return data.error;
        }
      }

      // Use status-specific messages
      switch (error.response.status) {
        case 400:
          return '请求参数有误，请检查后重试。';
        case 401:
          return '未授权访问，请先登录。';
        case 403:
          return '没有访问权限。';
        case 404:
          return '请求的资源不存在。';
        case 500:
          return '服务器内部错误，请稍后重试。';
        case 503:
          return '服务暂时不可用，请稍后重试。';
        default:
          return error.message || fallbackMessage;
      }
    }

    // Network error (no response)
    if (error.request && !error.response) {
      return '网络连接失败，请检查网络后重试。';
    }

    // Request setup error
    return error.message || fallbackMessage;
  }

  // Handle standard Error objects
  if (error instanceof Error) {
    return error.message;
  }

  // Handle string errors
  if (typeof error === 'string') {
    return error;
  }

  // Fallback for unknown error types
  return fallbackMessage;
};

/**
 * Log error to console in development, and optionally to error reporting service in production
 */
export const logError = (error: unknown, context?: string): void => {
  if (process.env.NODE_ENV === 'development') {
    console.error(context ? `[${context}]` : '[Error]', error);
  } else {
    // In production, you could send to error tracking service
    // Example: Sentry.captureException(error, { tags: { context } });
  }
};

/**
 * Create error handler with consistent logging and message extraction
 */
export const createErrorHandler = (context: string, fallbackMessage: string) => {
  return (error: unknown): string => {
    logError(error, context);
    return getErrorMessage(error, fallbackMessage);
  };
};
