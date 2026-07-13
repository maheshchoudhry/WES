// Token persistence. "Remember me" uses localStorage (persists across browser
// sessions); otherwise sessionStorage (cleared when the tab closes).
//
// Falls back to an in-memory store when Web Storage is unavailable (private mode,
// SSR, or test environments), so the app never crashes on storage access.

const ACCESS = "wes.access_token";
const REFRESH = "wes.refresh_token";
const REMEMBER = "wes.remember";

class MemoryStorage {
  private map = new Map<string, string>();
  getItem(k: string): string | null {
    return this.map.has(k) ? this.map.get(k)! : null;
  }
  setItem(k: string, v: string): void {
    this.map.set(k, v);
  }
  removeItem(k: string): void {
    this.map.delete(k);
  }
}

const memLocal = new MemoryStorage();
const memSession = new MemoryStorage();

function pick(kind: "local" | "session"): Pick<Storage, "getItem" | "setItem" | "removeItem"> {
  try {
    const s = kind === "local" ? window.localStorage : window.sessionStorage;
    if (s) {
      // Probe to confirm it is actually usable.
      const probe = "__wes_probe__";
      s.setItem(probe, "1");
      s.removeItem(probe);
      return s;
    }
  } catch {
    // fall through to memory
  }
  return kind === "local" ? memLocal : memSession;
}

const local = () => pick("local");
const session = () => pick("session");

function primary() {
  return local().getItem(REMEMBER) === "1" ? local() : session();
}

export const tokenStore = {
  get access(): string | null {
    return local().getItem(ACCESS) ?? session().getItem(ACCESS);
  },
  get refresh(): string | null {
    return local().getItem(REFRESH) ?? session().getItem(REFRESH);
  },
  set(access: string, refresh: string, remember: boolean): void {
    this.clear();
    if (remember) local().setItem(REMEMBER, "1");
    const store = primary();
    store.setItem(ACCESS, access);
    store.setItem(REFRESH, refresh);
  },
  setAccess(access: string): void {
    primary().setItem(ACCESS, access);
  },
  clear(): void {
    for (const s of [local(), session()]) {
      s.removeItem(ACCESS);
      s.removeItem(REFRESH);
    }
    local().removeItem(REMEMBER);
  },
  get hasSession(): boolean {
    return this.access !== null;
  },
};
