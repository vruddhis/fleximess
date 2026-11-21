import { createContext, useContext } from 'react';

export const AuthContext = createContext(null); //thisa context object stores the user info

export function useAuth() {
  //we call this to use the context value
  const context = useContext(AuthContext);
  if  (!context) {
    throw new Error('useAuth must be used within an AuthProvider.'); //like it shouild be inside <AuthProvider>
  }
  return context;
}
