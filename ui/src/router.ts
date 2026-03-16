type RouteHandler = (params: Record<string, string>) => void;

interface Route {
  pattern: RegExp;
  keys: string[];
  handler: RouteHandler;
}

const routes: Route[] = [];

export function addRoute(path: string, handler: RouteHandler): void {
  const keys: string[] = [];
  const pattern = new RegExp(
    "^" + path.replace(/:(\w+)/g, (_, key) => {
      keys.push(key);
      return "([^/]+)";
    }) + "$"
  );
  routes.push({ pattern, keys, handler });
}

export function navigate(hash: string): void {
  window.location.hash = hash;
}

export function startRouter(): void {
  function handleHash(): void {
    const hash = window.location.hash.slice(1) || "/";
    for (const route of routes) {
      const match = hash.match(route.pattern);
      if (match) {
        const params: Record<string, string> = {};
        route.keys.forEach((key, i) => {
          params[key] = match[i + 1];
        });
        route.handler(params);
        return;
      }
    }
    // Default: go home
    navigate("/");
  }

  window.addEventListener("hashchange", handleHash);
  handleHash();
}
