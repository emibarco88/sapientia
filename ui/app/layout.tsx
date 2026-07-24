import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { EnterpriseProvider } from "@/components/enterprise/EnterpriseContext";
import "@xyflow/react/dist/style.css";
import "./globals.css";
import "./foundation.css";
import "./knowledge.css";
import "./intelligence.css";
import "./intelligence-experience.css";
import "./ai-advisor.css";
import "./polish.css";
import "./explorer.css";
import "./ux-v2.css";
import "./vnext.css";
import "./phase2c1.css";
import "./phase2c2.css";
import "./phase2c.css";
import "./phase2d.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = { title: "Sapientia | Enterprise Intelligence", description: "The Enterprise Intelligence Platform." };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}><body className="min-h-full"><EnterpriseProvider>{children}</EnterpriseProvider></body></html>;
}
