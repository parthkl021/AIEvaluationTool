// Auth utilities for managing tokens
export const AUTH_KEYS = {
  ACCESS_TOKEN: 'access_token',
  REFRESH_TOKEN: 'refresh_token',
  USER_NAME: 'user_name',
  ROLE: 'role'
};

export const getStoredTokens = () => ({
  accessToken: localStorage.getItem(AUTH_KEYS.ACCESS_TOKEN),
  refreshToken: localStorage.getItem(AUTH_KEYS.REFRESH_TOKEN),
  userName: localStorage.getItem(AUTH_KEYS.USER_NAME),
  role: localStorage.getItem(AUTH_KEYS.ROLE),
});

export const setStoredTokens = (tokens: {
  access_token: string;
  refresh_token: string;
  user_name: string;
  role: string;
}) => {
  localStorage.setItem(AUTH_KEYS.ACCESS_TOKEN, tokens.access_token);
  localStorage.setItem(AUTH_KEYS.REFRESH_TOKEN, tokens.refresh_token);
  localStorage.setItem(AUTH_KEYS.USER_NAME, tokens.user_name);
  localStorage.setItem(AUTH_KEYS.ROLE, tokens.role);
};

export const clearStoredTokens = () => {
  localStorage.removeItem(AUTH_KEYS.ACCESS_TOKEN);
  localStorage.removeItem(AUTH_KEYS.REFRESH_TOKEN);
  localStorage.removeItem(AUTH_KEYS.USER_NAME);
  localStorage.removeItem(AUTH_KEYS.ROLE);
};

export const isAuthenticated = () => !!localStorage.getItem(AUTH_KEYS.ACCESS_TOKEN);

export const parseUrlHashTokens = () => {
  const hash = window.location.hash.replace(/^#/, '');
  if (!hash) return null;
  const values = Object.fromEntries(new URLSearchParams(hash));

  if (values.access_token && values.refresh_token) {
    setStoredTokens({
      access_token: values.access_token,
      refresh_token: values.refresh_token,
      user_name: values.user_name || '',
      role: values.role || '',
    });
    window.history.replaceState({}, document.title, window.location.pathname + window.location.search);
    return values;
  }

  return null;
};

export const refreshAccessToken = async (refreshUrl: string): Promise<boolean> => {
  const refreshToken = localStorage.getItem(AUTH_KEYS.REFRESH_TOKEN);
  if (!refreshToken) return false;

  try {
    const response = await fetch(refreshUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (response.ok) {
      const data = await response.json();
      setStoredTokens(data);
      return true;
    }
  } catch (error) {
    console.error('Token refresh failed:', error);
  }

  return false;
};