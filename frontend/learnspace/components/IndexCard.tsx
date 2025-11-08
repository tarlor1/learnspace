"use client"

import { useState } from "react"
import { ThumbsUp, ThumbsDown } from "lucide-react"

interface IndexCardProps {
  id: string
  chapter: string
  text: string
}

export default function IndexCard({ id, chapter, text }: IndexCardProps) {
  const [reaction, setReaction] = useState<"like" | "dislike" | null>(null)

  return (
    <div className="bg-card border border-border rounded-2xl shadow-sm hover:shadow-lg transition-shadow p-4 mb-4">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-xs font-semibold text-primary px-3 py-1 bg-primary/10 rounded-full">{chapter}</span>
      </div>

      <p className="text-card-foreground font-medium leading-relaxed mb-4">{text}</p>

      <div className="flex gap-2 pt-3 border-t border-border">
        <button
          onClick={() => setReaction(reaction === "like" ? null : "like")}
          className={`p-2 rounded-lg transition ${
            reaction === "like"
              ? "bg-green-100 text-green-600"
              : "bg-background border border-border text-muted-foreground hover:border-green-500 hover:text-green-600"
          }`}
          title="Like this subject"
        >
          <ThumbsUp size={20} />
        </button>
        <button
          onClick={() => setReaction(reaction === "dislike" ? null : "dislike")}
          className={`p-2 rounded-lg transition ${
            reaction === "dislike"
              ? "bg-red-100 text-red-600"
              : "bg-background border border-border text-muted-foreground hover:border-red-500 hover:text-red-600"
          }`}
          title="Dislike this subject"
        >
          <ThumbsDown size={20} />
        </button>
      </div>
    </div>
  )
}
