import { Component, ErrorInfo, ReactNode } from "react";
import { Button } from "@/components/ui/button";

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error:", error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen flex-col items-center justify-center bg-background px-4 text-center">
          <div className="mb-8 flex h-20 w-20 items-center justify-center rounded-3xl bg-red-100 text-3xl font-bold text-red-500">
            !
          </div>
          <h1 className="mb-2 text-2xl font-bold tracking-tight">Something went wrong</h1>
          <p className="mb-8 text-neutral-dark max-w-md">
            {this.state.error?.message || "An unexpected error occurred in the application."}
          </p>
          <Button onClick={() => window.location.reload()}>
            Reload page
          </Button>
        </div>
      );
    }

    return this.props.children;
  }
}
