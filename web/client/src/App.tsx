import { Switch, Route } from "wouter";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Welcome from "@/pages/Welcome";
import Dashboard from "@/pages/Dashboard";
import YourData from "@/pages/YourData";

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 60_000, retry: 1 } },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Switch>
        <Route path="/" component={Welcome} />
        <Route path="/dashboard" component={Dashboard} />
        <Route path="/your-data" component={YourData} />
        <Route>
          <div className="min-h-screen flex items-center justify-center text-muted-foreground">
            404 — Not Found
          </div>
        </Route>
      </Switch>
    </QueryClientProvider>
  );
}
