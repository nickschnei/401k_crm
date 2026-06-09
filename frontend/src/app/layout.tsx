import type { Metadata } from "next";
import "./globals.css";
import Providers from "./providers";
import Sidebar from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "401(k) Fiduciary CRM",
  description: "Modern, high-performance plan prospecting and fiduciary compliance diagnostic.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased dark">
      <body className="min-h-full flex bg-[#090d16] font-sans antialiased text-slate-100 selection:bg-blue-500/30 selection:text-blue-200">
        <Providers>
          <div className="flex h-screen w-screen overflow-hidden">
            <Sidebar />
            <main className="flex-1 h-full overflow-y-auto bg-[#020617] flex flex-col">
              {children}
            </main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
