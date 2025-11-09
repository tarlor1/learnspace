"use client"

import { useState } from "react"
import { ThumbsUp, ThumbsDown, Loader2, AlertCircle, XCircle } from "lucide-react"
import { apiClient } from "@/lib/api"

interface ShortResponseCardProps {
  id: string
  topic: string
  question: string
}

interface ValidationResult {
  feedback?: string
  answer?: string  // NeuralSeek returns 'answer' field
}

export default function ShortResponseCard({ id, topic, question }: ShortResponseCardProps) {
  const [answer, setAnswer] = useState("")
  const [reaction, setReaction] = useState<"like" | "dislike" | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [validation, setValidation] = useState<ValidationResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const getAccessToken = async (): Promise<string> => {
    const res = await fetch("/api/auth/token")
    if (!res.ok) throw new Error("Authentication required")
    const data = await res.json()
    if (!data.accessToken) throw new Error("Authentication required")
    return data.accessToken
  }

  const handleSubmitAnswer = async () => {
    if (!answer.trim()) return

    setIsSubmitting(true)
    setError(null)
    setValidation(null)

    try {
      const token = await getAccessToken()
      console.log('🔍 Submitting answer:', { topic, question_id: id, answer: answer.trim() })
      const response = await apiClient.post(
        "/submit-answer",
        {
          topic,
          question_id: id,
          answer: answer.trim(),
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      )

      console.log('✅ Validation received:', response.data)
      setValidation(response.data.validation)
    } catch (err: any) {
      console.error('❌ Error submitting answer:', err)
      const errorMessage = err.response?.data?.detail || err.message || "Failed to submit answer"
      setError(errorMessage)
    } finally {
      setIsSubmitting(false)
    }
  }

  const getDisplayText = () => {
    if (!validation) return ""
    // NeuralSeek might return feedback in 'answer' or 'feedback' field
    const feedback = validation.feedback || validation.answer || ""
    
    // If there's any other data in validation, show it
    if (feedback) return feedback
    
    // Show the entire validation object as JSON if nothing else
    return JSON.stringify(validation, null, 2)
  }

  return (
    <div className="bg-card border border-border rounded-2xl shadow-sm hover:shadow-lg transition-shadow p-4 mb-4">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-xs font-semibold text-primary px-3 py-1 bg-primary/10 rounded-full">{topic}</span>
      </div>

      <p className="text-card-foreground font-medium text-base mb-4">{question}</p>

      <div className="border-t border-border pt-4">
        <textarea
          placeholder="Type your answer here..."
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          disabled={isSubmitting}
          rows={3}
          className="w-full bg-background border border-input rounded-lg px-3 py-2 text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring transition resize-none disabled:opacity-50"
        />

        {validation && (
          <div className="mt-3 p-3 rounded-lg bg-blue-50 border border-blue-200">
            <div className="flex items-start gap-2">
              <AlertCircle className="h-5 w-5 text-blue-600 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-medium text-blue-900">Feedback</p>
                <p className="text-sm mt-1 text-blue-800">{getDisplayText()}</p>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="mt-3 p-3 rounded-lg bg-red-50 text-red-600">
            <div className="flex items-start gap-2">
              <XCircle className="h-5 w-5 flex-shrink-0" />
              <p className="text-sm">{error}</p>
            </div>
          </div>
        )}

        <div className="flex gap-2 mt-3 justify-between items-center">
          <div className="flex gap-2">
            <button
              onClick={handleSubmitAnswer}
              disabled={isSubmitting || !answer.trim()}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition font-medium text-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
              {isSubmitting ? "Checking..." : "Check Answer"}
            </button>
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => setReaction(reaction === "like" ? null : "like")}
              disabled={isSubmitting}
              className={`p-2 rounded-lg transition disabled:opacity-50 ${
                reaction === "like"
                  ? "bg-green-100 text-green-600"
                  : "bg-background border border-border text-muted-foreground hover:border-green-500 hover:text-green-600"
              }`}
              title="Like this question"
            >
              <ThumbsUp size={20} />
            </button>
            <button
              onClick={() => setReaction(reaction === "dislike" ? null : "dislike")}
              disabled={isSubmitting}
              className={`p-2 rounded-lg transition disabled:opacity-50 ${
                reaction === "dislike"
                  ? "bg-red-100 text-red-600"
                  : "bg-background border border-border text-muted-foreground hover:border-red-500 hover:text-red-600"
              }`}
              title="Dislike this question"
            >
              <ThumbsDown size={20} />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
