import { useCallback, useEffect, useMemo, useState } from 'react';
import { AuthContext } from './authContext';

//we can define this env variable, or else port 8000 is our default
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000')
  .replace(/\/+$/, ''); //this regex removes all trailing slashes
  //https://vite.dev/guide/env-and-mode 

const DEMO_MODE = import.meta.env.VITE_AUTH_MODE !== 'api'; //demo mode on unless AUTH_MODE is API

const DEMO_SESSION_KEY = 'hostelPortal.demoUsername';


function getInitialAuthState() {

  if (!DEMO_MODE) {
    return { user: null, status: 'loading' };
  }

  //this is what happens in demo mode
  const username = localStorage.getItem(DEMO_SESSION_KEY);
  return username
    ? { user: { username, name: username }, status: 'authenticated' } 
    : { user: null, status: 'unauthenticated' };
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: 'include',
    headers: {
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      ...options.headers,
    },
  });

  const contentType = response.headers.get('content-type') || '';
  const result = contentType.includes('application/json')
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const detail = typeof result === 'object' && result !== null
      ? result.detail || result.message
      : result;
    const error = new Error(detail || `Request failed (${response.status})`);
    error.status = response.status;
    throw error;
  }

  return result;
}

function getUser(result) {
  const user = result?.user ?? result;
  if (!user || typeof user !== 'object' || Array.isArray(user)) {
    throw new Error('data type mismatch');
  }
  return user;
}

export function AuthProvider({ children }) {

  const [initialAuthState]= useState(getInitialAuthState);
  const [user, setUser] = useState(initialAuthState.user);
  const [status, setStatus] = useState(initialAuthState.status);

  const [authError, setAuthError] = useState('');

  const refreshUser =  useCallback(async () => {
    if (DEMO_MODE) {
      const  username = localStorage.getItem(DEMO_SESSION_KEY);
      setUser(username ? { username,  name: username } : null);
      setStatus(username  ? 'authenticated' : 'unauthenticated');
      setAuthError('');
      return;
    }
    
    //not demo mode
    setStatus('loading');
    setAuthError('');
    try {
      const result = await request('/auth/me');
      setUser(getUser(result));
      setStatus('authenticated');
    } catch (error) {
      if (error.status === 401) {
        setUser(null);
        setStatus('unauthenticated');
      } else {
        setStatus('error');
        setAuthError(error.message);
      }
    }
  }, []);

  useEffect(() => {
    if (DEMO_MODE) return undefined;

    let active = true;
    request('/auth/me')
      .then((result) => {
        if (active) {
          setUser(getUser(result));
          setStatus('authenticated');
        }
      })
      .catch((error) => {
        if (!active) return;
        if (error.status === 401) {
          setUser(null);
          setStatus('unauthenticated');
        } else {
          setStatus('error');
          setAuthError(error.message);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  const login = useCallback(async (username, password) => {
    if (DEMO_MODE) {
      const demoUsername = username.trim();
      if (!demoUsername || password !== 'dummy') {
        throw new Error('password  is "dummy"');
      }

      localStorage.setItem(DEMO_SESSION_KEY, demoUsername);
      const demoUser = { username: demoUsername, name: demoUsername };
      setUser(demoUser);
      setStatus('authenticated');
      setAuthError('');
      return demoUser;
    }

    await request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    const result = await  request('/auth/me');
    const  authenticatedUser = getUser(result);
  setUser(authenticatedUser);
    setStatus('authenticated');
    setAuthError('');
    return authenticatedUser;
  }, []);

  const logout = useCallback(async () => {
    setAuthError('');
    if (DEMO_MODE) {
      localStorage.removeItem(DEMO_SESSION_KEY);
      setUser(null);
      setStatus('unauthenticated');
      return true;
    }

    try {
      await request('/auth/logout', { method: 'POST' });
      setUser(null);
      setStatus('unauthenticated');
      return true;
    } catch (error) {
      setAuthError(`Could not sign out: ${error.message}`);
      return false;
    }
  }, []);

  const value = useMemo(() => ({
    user,
    status,
    authError,
    login,
    logout,
    refreshUser,
  }), [user, status, authError, login, logout, refreshUser]);

  return (
    <AuthContext.Provider value={value}>
      {children}
      {authError && (
        <div className="auth-error-banner" role="alert">
          <span>{authError}</span>
          <button type="button" onClick={() => setAuthError('')}>Dismiss</button>
        </div>
      )}
    </AuthContext.Provider>
  );
}
