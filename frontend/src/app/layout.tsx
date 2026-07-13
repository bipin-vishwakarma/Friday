import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'FRIDAY AI',
  description: 'Your Iron Man AI Desktop Assistant',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#020b18] text-[#d0e8ff] antialiased overflow-hidden">
        {children}
      </body>
    </html>
  )
}