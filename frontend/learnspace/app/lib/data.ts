export interface Card {
  id: string
  type: "short" | "mcq" | "index"
  chapter: string
  question?: string
  options?: string[]
  correctAnswer?: string
  text?: string
}

export interface User {
  id: string
  name: string
  email: string
  joinDate: string
  totalCardsCompleted: number
}

export interface Document {
  id: string
  title: string
  uploadDate: string
  chapters: {
    name: string
    completed: boolean
    totalCards: number
    completedCards: number
  }[]
}

export const mockUser: User = {
  id: "user-1",
  name: "Alex Johnson",
  email: "alex.johnson@email.com",
  joinDate: "January 15, 2024",
  totalCardsCompleted: 42,
}

export const mockDocuments: Document[] = [
  {
    id: "doc-1",
    title: "Biology Fundamentals",
    uploadDate: "March 10, 2024",
    chapters: [
      { name: "Chapter 1: Cell Biology", completed: true, totalCards: 12, completedCards: 12 },
      { name: "Chapter 2: Photosynthesis", completed: true, totalCards: 8, completedCards: 8 },
      { name: "Chapter 3: Genetics", completed: false, totalCards: 10, completedCards: 5 },
      { name: "Chapter 4: Evolution", completed: false, totalCards: 9, completedCards: 2 },
      { name: "Chapter 5: Ecology", completed: false, totalCards: 7, completedCards: 0 },
    ],
  },
  {
    id: "doc-2",
    title: "Chemistry Basics",
    uploadDate: "February 28, 2024",
    chapters: [
      { name: "Chapter 1: Atoms and Molecules", completed: true, totalCards: 15, completedCards: 15 },
      { name: "Chapter 2: Chemical Bonds", completed: false, totalCards: 11, completedCards: 6 },
    ],
  },
]

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
