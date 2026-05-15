/**
 * Utility to manage the 'app' query parameter required by the Semicolons deployment portal.
 * Preserves the app ID across session navigation and appends it to API/WebSocket requests.
 */

export const getAppId = (): string | null => {
  // 1. Check URL query string first
  const urlParams = new URLSearchParams(window.location.search);
  let appId = urlParams.get('app');
  
  if (appId) {
    // Store in sessionStorage to persist across internal navigation
    sessionStorage.setItem('semicolons_app_id', appId);
  } else {
    // 2. Fallback to stored ID if not in URL
    appId = sessionStorage.getItem('semicolons_app_id');
  }
  
  return appId;
};

/**
 * Appends the 'app' parameter to a URL if it exists.
 */
export const withAppId = (url: string): string => {
  const appId = getAppId();
  if (!appId) return url;
  
  try {
    const urlObj = new URL(url, window.location.origin);
    urlObj.searchParams.set('app', appId);
    return urlObj.toString();
  } catch (e) {
    // Handle relative paths or invalid URLs
    const separator = url.includes('?') ? '&' : '?';
    return `${url}${separator}app=${appId}`;
  }
};

/**
 * Returns the query string part for the app parameter.
 */
export const getAppQueryString = (): string => {
  const appId = getAppId();
  return appId ? `app=${appId}` : '';
};
