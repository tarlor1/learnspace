"use client"

export default function Navbar() {
  return (
    <nav className="fixed top-0 left-0 right-0 bg-card border-b border-border shadow-sm z-50">
      <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <span className="text-primary-foreground font-bold text-sm">PQ</span>
          </div>
          <h1 className="text-xl font-bold text-foreground">Practice Questions</h1>
        </div>
        <div className="text-sm text-muted-foreground">Study & Master</div>
      </div>
    </nav>
  )
}
