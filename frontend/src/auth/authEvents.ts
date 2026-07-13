// Lightweight bus so the API client can signal auth outcomes to the app shell
// (which owns routing) without importing React Router.

type Handler = () => void;

const handlers: { unauthorized: Handler[]; forbidden: Handler[] } = {
  unauthorized: [],
  forbidden: [],
};

export const authEvents = {
  onUnauthorized(fn: Handler): () => void {
    handlers.unauthorized.push(fn);
    return () => {
      handlers.unauthorized = handlers.unauthorized.filter((h) => h !== fn);
    };
  },
  onForbidden(fn: Handler): () => void {
    handlers.forbidden.push(fn);
    return () => {
      handlers.forbidden = handlers.forbidden.filter((h) => h !== fn);
    };
  },
  emitUnauthorized(): void {
    handlers.unauthorized.forEach((h) => h());
  },
  emitForbidden(): void {
    handlers.forbidden.forEach((h) => h());
  },
};
