"use client"

import Navbar from "@/components/Navbar"
import ShortResponseCard from "@/components/cards/ShortResponseCard"
import MCQCard from "@/components/cards/MCQCard"
import IndexCard from "@/components/cards/IndexCard"
import { mockCards } from "@/app/lib/data"

export default function Home() {
  return (
    <main className="bg-background min-h-screen">
      <Navbar />

      <div className="pt-20 pb-12">
        <div className="max-w-2xl mx-auto px-4 w-full">
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
      </div>
    </main>
  )
}
