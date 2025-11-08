"use client"

import ShortResponseCard from "@/components/cards/ShortResponseCard"
import MCQCard from "@/components/cards/MCQCard"
import IndexCard from "@/components/cards/IndexCard"
import { mockCards } from "@/app/lib/data"

export default function StudyPage() {
  return (
    <div className="max-w-2xl mx-auto px-4 w-full">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-foreground">Study Cards</h2>
        <p className="text-muted-foreground text-sm mt-1">Review your practice questions</p>
      </div>

      {mockCards.map((card) => {
        if (card.type === "short") {
          return <ShortResponseCard key={card.id} id={card.id} chapter={card.chapter} question={card.question!} />
        } else if (card.type === "mcq") {
          return (
            <MCQCard
              key={card.id}
              id={card.id}
              chapter={card.chapter}
              question={card.question!}
              options={card.options!}
            />
          )
        } else if (card.type === "index") {
          return <IndexCard key={card.id} id={card.id} chapter={card.chapter} text={card.text!} />
        }
      })}
    </div>
  )
}
