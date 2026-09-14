import { createContext, useContext } from "react";

/*
  Session state for the whole app.

  Split from the provider so this module exports no components, which keeps
  fast refresh working on the provider file.
*/
export const AuthContext = createContext(null);

export function useAuth() {
  const value = useContext(AuthContext);

  if (!value) {
    throw new Error("useAuth must be used inside <AuthProvider>.");
  }

  return value;
}
