import { LucideProvider } from "lucide-react";

/**
 * Wraps the app so every lucide icon inherits one stroke weight and picks up
 * the `.icon` sizing rule in Global.css — which reads --icon-size and
 * --icon-color, so icons stay controlled from variables.css.
 */
function IconProvider({ children }) {
  return (
    <LucideProvider className="icon" strokeWidth={1.6}>
      {children}
    </LucideProvider>
  );
}

export default IconProvider;
