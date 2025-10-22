import { ChatWidget } from "@/components/ChatWidget";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5">
      <main className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto text-center space-y-8">
          {/* Hero Section */}
          <div className="space-y-4">
            <h1 className="text-5xl font-bold bg-gradient-to-r from-[hsl(262_83%_58%)] to-[hsl(217_91%_60%)] bg-clip-text text-transparent">
              College AI Assistant
            </h1>
            <p className="text-xl text-muted-foreground">
              Get instant answers about our college, programs, admissions, and placements
            </p>
          </div>

          {/* Feature Cards */}
          <div className="grid md:grid-cols-3 gap-6 mt-12">
            <div className="p-6 rounded-2xl bg-card border border-border shadow-lg hover:shadow-xl transition-shadow">
              <div className="text-3xl mb-3">🎓</div>
              <h3 className="font-semibold text-lg mb-2">Academic Programs</h3>
              <p className="text-sm text-muted-foreground">
                Explore our diverse range of undergraduate and postgraduate programs
              </p>
            </div>
            
            <div className="p-6 rounded-2xl bg-card border border-border shadow-lg hover:shadow-xl transition-shadow">
              <div className="text-3xl mb-3">💼</div>
              <h3 className="font-semibold text-lg mb-2">Placements</h3>
              <p className="text-sm text-muted-foreground">
                Learn about our placement records and recruiting companies
              </p>
            </div>
            
            <div className="p-6 rounded-2xl bg-card border border-border shadow-lg hover:shadow-xl transition-shadow">
              <div className="text-3xl mb-3">📝</div>
              <h3 className="font-semibold text-lg mb-2">Admissions</h3>
              <p className="text-sm text-muted-foreground">
                Get information about admission process and requirements
              </p>
            </div>
          </div>

          {/* CTA */}
          <div className="mt-16 p-8 rounded-2xl bg-gradient-to-r from-[hsl(262_83%_58%)] to-[hsl(217_91%_60%)] text-white">
            <h2 className="text-2xl font-bold mb-4">Start Chatting Now</h2>
            <p className="text-white/90 mb-6">
              Click the chat icon in the bottom-right corner to begin your conversation with our AI assistant
            </p>
            <div className="inline-flex items-center gap-2 text-sm">
              <span className="animate-bounce">👇</span>
              <span>Look for the chat button</span>
            </div>
          </div>
        </div>
      </main>

      {/* Floating Chat Widget */}
      <ChatWidget />
    </div>
  );
}
