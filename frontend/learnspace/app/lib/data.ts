export interface Card {
  id: string
  type: "short" | "mcq" | "index"
  chapter: string
  question?: string
  options?: string[]
  correctAnswer?: string
  text?: string
}

export const mockCards: Card[] = [
  {
    id: "1",
    type: "short",
    chapter: "Chapter 2: Photosynthesis",
    question: "What are the two main stages of photosynthesis?",
    correctAnswer: "Light-dependent reactions and light-independent reactions (Calvin cycle)",
  },
  {
    id: "2",
    type: "mcq",
    chapter: "Chapter 1: Cell Biology",
    question: "Which organelle is responsible for producing ATP?",
    options: ["Nucleus", "Mitochondria", "Ribosome", "Golgi Apparatus"],
    correctAnswer: "Mitochondria",
  },
  {
    id: "3",
    type: "index",
    chapter: "Chapter 3: Genetics",
    text: "Mendel's Law of Segregation states that alleles separate during gamete formation, with each gamete receiving only one allele for each gene.",
  },
  {
    id: "4",
    type: "short",
    chapter: "Chapter 4: Evolution",
    question: "Define natural selection in your own words.",
    correctAnswer:
      "The process by which organisms with favorable traits are more likely to survive and reproduce, passing those traits to offspring.",
  },
  {
    id: "5",
    type: "mcq",
    chapter: "Chapter 2: Photosynthesis",
    question: "In which part of the chloroplast does the Calvin cycle occur?",
    options: ["Thylakoid membrane", "Stroma", "Outer membrane", "Inner membrane"],
    correctAnswer: "Stroma",
  },
  {
    id: "6",
    type: "index",
    chapter: "Chapter 1: Cell Biology",
    text: "The cell membrane is a phospholipid bilayer that controls what substances enter and exit the cell, maintaining homeostasis.",
  },
  {
    id: "7",
    type: "mcq",
    chapter: "Chapter 5: Ecology",
    question: "What is the primary role of decomposers in an ecosystem?",
    options: [
      "Produce energy from sunlight",
      "Break down dead organic matter",
      "Consume other organisms",
      "Store energy",
    ],
    correctAnswer: "Break down dead organic matter",
  },
  {
    id: "8",
    type: "short",
    chapter: "Chapter 3: Genetics",
    question: "What is the difference between dominant and recessive alleles?",
    correctAnswer:
      "Dominant alleles are expressed when present and mask recessive alleles. Recessive alleles are only expressed when homozygous.",
  },
]
