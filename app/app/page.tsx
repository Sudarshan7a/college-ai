import { ChatWidget } from "@/components/ChatWidget";

export default function Home() {
  return (
    <div
      className="min-h-screen bg-cover bg-center bg-no-repeat relative"
      style={{
        backgroundImage: "url('/background.png')",
      }}
    >
      {/* Dark overlay for better contrast */}
      <div className="absolute inset-0" />

      {/* Floating Chat Widget */}
      <ChatWidget />
    </div>
  );
}
