import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AATES Autonomous AI Studio Operating System",
  description: "Autonomous AI Tamil Entertainment Studio Dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased font-sans">
      <body className="min-h-full flex flex-col bg-slate-950 text-slate-100">{children}</body>
    </html>
  );
}
