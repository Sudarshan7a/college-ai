import { ChatWidget } from "@/components/ChatWidget";

const Index = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-secondary">
      {/* Demo Content */}
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto text-center space-y-8">
          <div className="space-y-4 animate-fade-in">
            <h1 className="text-5xl md:text-6xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
              Beautiful Chat Widget
            </h1>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              A modern, responsive floating chat interface with smooth animations, 
              expandable stages, and direct API integration.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 mt-12">
            <div className="p-6 bg-card rounded-2xl border border-border" style={{ boxShadow: "var(--shadow-soft)" }}>
              <div className="w-12 h-12 bg-gradient-to-r from-primary to-accent rounded-xl flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-primary-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-foreground mb-2">Lightning Fast</h3>
              <p className="text-muted-foreground">
                Smooth animations and transitions powered by Framer Motion
              </p>
            </div>

            <div className="p-6 bg-card rounded-2xl border border-border" style={{ boxShadow: "var(--shadow-soft)" }}>
              <div className="w-12 h-12 bg-gradient-to-r from-primary to-accent rounded-xl flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-primary-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-foreground mb-2">Responsive Design</h3>
              <p className="text-muted-foreground">
                Adapts perfectly to any screen size from mobile to desktop
              </p>
            </div>

            <div className="p-6 bg-card rounded-2xl border border-border" style={{ boxShadow: "var(--shadow-soft)" }}>
              <div className="w-12 h-12 bg-gradient-to-r from-primary to-accent rounded-xl flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-primary-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-foreground mb-2">Fully Customizable</h3>
              <p className="text-muted-foreground">
                Easy to integrate and customize with your brand colors
              </p>
            </div>
          </div>

          <div className="mt-16 p-8 bg-card rounded-2xl border border-border" style={{ boxShadow: "var(--shadow-elegant)" }}>
            <h2 className="text-2xl font-semibold text-foreground mb-4">Try It Out</h2>
            <p className="text-muted-foreground mb-6">
              Click the chat icon in the bottom-right corner to start a conversation. 
              Try expanding it to fullscreen or collapsing it back.
            </p>
            <div className="flex flex-wrap gap-4 justify-center">
              <span className="px-4 py-2 bg-primary/10 text-primary rounded-full text-sm font-medium">
                Smooth Animations
              </span>
              <span className="px-4 py-2 bg-accent/10 text-accent rounded-full text-sm font-medium">
                API Integration
              </span>
              <span className="px-4 py-2 bg-primary/10 text-primary rounded-full text-sm font-medium">
                Keyboard Accessible
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Chat Widget */}
      <ChatWidget />
    </div>
  );
};

export default Index;
