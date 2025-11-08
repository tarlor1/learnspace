"use client"

import { useState } from "react"
import { ThumbsUp, ThumbsDown } from "lucide-react"

interface ShortResponseCardProps {
  id: string
  chapter: string
  question: string
}

export default function ShortResponseCard({ id, chapter, question }: ShortResponseCardProps) {
  const [answer, setAnswer] = useState("")
  const [reaction, setReaction] = useState<"like" | "dislike" | null>(null)

  return (
    <div className="bg-card border border-border rounded-2xl shadow-sm hover:shadow-lg transition-shadow p-4 mb-4">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-xs font-semibold text-primary px-3 py-1 bg-primary/10 rounded-full">{chapter}</span>
      </div>

      <p className="text-card-foreground font-medium text-base mb-4">{question}</p>

      <div className="border-t border-border pt-4">
        <input
          type="text"
          placeholder="Type your answer here..."
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          className="w-full bg-background border border-input rounded-lg px-3 py-2 text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring transition"
        />
        <div className="flex gap-2 mt-3 justify-between items-center">
          <div className="flex gap-2">
            <button className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition font-medium text-sm">
              Check Answer
            </button>
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => setReaction(reaction === "like" ? null : "like")}
              className={`p-2 rounded-lg transition ${
                reaction === "like"
                  ? "bg-green-100 text-green-600"
                  : "bg-background border border-border text-muted-foreground hover:border-green-500 hover:text-green-600"
              }`}
              title="Like this question subject"
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
              title="Dislike this question subject"
            >
              <ThumbsDown size={20} />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
