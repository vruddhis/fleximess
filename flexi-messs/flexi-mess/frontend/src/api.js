//small helper for reading data from the backend (menus, messes, foods)
//uses the same base URL and stored token as auth/AuthProvider.jsx
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api')
  .replace(/\/+$/, '');

const TOKEN_KEY = 'hostelPortal.accessToken';

export async function apiGet(path, params = {}, { signal } = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') query.append(key, value);
  });
  const queryString = query.toString();
  const token = localStorage.getItem(TOKEN_KEY);

  const response = await fetch(`${API_BASE_URL}${path}${queryString ? `?${queryString}` : ''}`, {
    signal,
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) {
    throw new Error(`Could not load data (${response.status})`);
  }
  return response.json();
}
