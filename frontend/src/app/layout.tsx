import type { Metadata } from "next";
import "./globals.css";
import Providers from "./providers";
import AppLayout from "@/components/AppLayout";

export const metadata: Metadata = {
  title: "401(k) CRM",
  description: "Modern, high-performance plan prospecting and compliance diagnostic.",
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
          <AppLayout>
            {children}
          </AppLayout>
        </Providers>
      </body>
    </html>
  );
}
