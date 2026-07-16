/**
 * Authentication token management service.
 * Handles JWT token storage and retrieval from localStorage.
 */

const ACCESS_TOKEN_KEY = 'codementor_access_token';
const REFRESH_TOKEN_KEY = 'codementor_refresh_token';

/**
 * Get the stored access token.
 * @returns {string|null} The access token or null if not found
 */
export function getToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

/**
 * Get the stored refresh token.
 * @returns {string|null} The refresh token or null if not found
 */
export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

/**
 * Store authentication tokens.
 * @param {string} accessToken - The JWT access token
 * @param {string} refreshToken - The JWT refresh token
 */
export function setToken(accessToken, refreshToken) {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  if (refreshToken) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  }
}

/**
 * Remove all stored tokens (logout).
 */
export function removeToken() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

/**
 * Check if the user is authenticated.
 * @returns {boolean} True if access token exists
 */
export function isAuthenticated() {
  return !!getToken();
}
