"use client"

import { useState } from "react"
import { ThumbsUp, ThumbsDown } from "lucide-react"

interface MCQCardProps {
  id: string
  chapter: string
  question: string
  options: string[]
}

export default function MCQCard({ id, chapter, question, options }: MCQCardProps) {
  const [selected, setSelected] = useState<string | null>(null)
  const [reaction, setReaction] = useState<"like" | "dislike" | null>(null)

  return (
    <div className="bg-card border border-border rounded-2xl shadow-sm hover:shadow-lg transition-shadow p-4 mb-4">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-xs font-semibold text-primary px-3 py-1 bg-primary/10 rounded-full">{chapter}</span>
      </div>

      <p className="text-card-foreground font-medium text-base mb-4">{question}</p>

      <div className="border-t border-border pt-4 space-y-2">
        {options.map((option, index) => (
          <button
            key={index}
            onClick={() => setSelected(option)}
            className={`w-full p-3 rounded-lg border-2 transition text-left font-medium ${
              selected === option
                ? "border-primary bg-primary/10 text-primary"
                : "border-border bg-background text-foreground hover:border-primary/50"
            }`}
          >
            {option}
          </button>
        ))}
        <div className="flex gap-2 mt-4 justify-between items-center">
          <div className="flex gap-2">
            <button className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition font-medium text-sm">
              Submit
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
