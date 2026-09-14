import { useCallback, useEffect, useMemo, useState } from "react";
import {
  clearSession,
  readToken,
  readUser,
  saveToken,
  saveUser,
} from "../api/auth.js";
import { decodeToken, isExpired } from "../utils/jwt.js";
import { AuthContext } from "./authContext.js";

const EMPTY = { token: null, user: null, role: null };

// Storage is the source of truth, so a reload and a fresh mount agree. An
// expired token is discarded here rather than being handed to a guard.
function readSession() {
  const token = readToken();
  if (!token) return EMPTY;

  const payload = decodeToken(token);
  if (!payload || isExpired(payload)) {
    clearSession();
    return EMPTY;
  }

  return { token, user: readUser(), role: payload.role ?? null };
}

function AuthProvider({ children }) {
  const [session, setSession] = useState(readSession);

  useEffect(() => {
    // Fires when another tab signs in or out. Without it, one tab keeps
    // showing a name whose token is already gone.
    const sync = () => setSession(readSession());
    window.addEventListener("storage", sync);
    return () => window.removeEventListener("storage", sync);
  }, []);

  const signIn = useCallback(({ token, user }) => {
    saveToken(token);
    saveUser(user);
    setSession(readSession());
  }, []);

  const signOut = useCallback(() => {
    clearSession();
    setSession(EMPTY);
  }, []);

  const value = useMemo(
    () => ({
      ...session,
      isAuthenticated: Boolean(session.token),
      signIn,
      signOut,
    }),
    [session, signIn, signOut],
  );

  return <AuthContext value={value}>{children}</AuthContext>;
}

export default AuthProvider;
