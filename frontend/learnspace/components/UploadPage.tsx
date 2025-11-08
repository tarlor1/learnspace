"use client"

import { UploadIcon, ChevronDown, FileText } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { mockDocuments } from "@/app/lib/data"
import { useState } from "react"

export default function UploadPage() {
  const [expandedDoc, setExpandedDoc] = useState<string | null>(null)

  return (
    <div className="max-w-2xl mx-auto px-4 w-full">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-foreground">My Documents</h2>
        <p className="text-muted-foreground text-sm mt-1">Manage your uploaded documents and track progress</p>
      </div>

      {/* Upload Section */}
      <Card className="mb-8 border-2 border-dashed">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <UploadIcon className="w-5 h-5" />
            Upload New Document
          </CardTitle>
          <CardDescription>Drag and drop your PDF or click to browse</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="border-2 border-dashed border-border rounded-lg p-8 text-center hover:bg-muted/50 transition-colors cursor-pointer">
            <UploadIcon className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
            <p className="font-medium text-foreground mb-1">Drop your document here</p>
            <p className="text-sm text-muted-foreground">or click to select a file</p>
          </div>
        </CardContent>
      </Card>

      {/* Documents List */}
      <div className="space-y-4">
        <h3 className="font-semibold text-foreground">Your Documents ({mockDocuments.length})</h3>

        {mockDocuments.map((doc) => {
          const isExpanded = expandedDoc === doc.id
          const totalCards = doc.chapters.reduce((sum, ch) => sum + ch.totalCards, 0)
          const completedCards = doc.chapters.reduce((sum, ch) => sum + ch.completedCards, 0)
          const progressPercent = Math.round((completedCards / totalCards) * 100)

          return (
            <Card key={doc.id} className="overflow-hidden">
              <button onClick={() => setExpandedDoc(isExpanded ? null : doc.id)} className="w-full text-left">
                <CardHeader className="pb-3 hover:bg-muted/30 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <FileText className="w-4 h-4 text-primary" />
                        <CardTitle className="text-lg">{doc.title}</CardTitle>
                      </div>
                      <CardDescription>Uploaded {doc.uploadDate}</CardDescription>
                    </div>
                    <ChevronDown
                      className={`w-5 h-5 text-muted-foreground transition-transform ${isExpanded ? "rotate-180" : ""}`}
                    />
                  </div>

                  {/* Progress Bar */}
                  <div className="mt-4">
                    <div className="flex items-center justify-between text-sm mb-2">
                      <span className="text-muted-foreground">Progress</span>
                      <span className="font-semibold text-foreground">
                        {completedCards} / {totalCards}
                      </span>
                    </div>
                    <div className="w-full bg-muted rounded-full h-2">
                      <div
                        className="bg-primary h-2 rounded-full transition-all"
                        style={{ width: `${progressPercent}%` }}
                      />
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">{progressPercent}% complete</p>
                  </div>
                </CardHeader>
              </button>

              {/* Chapters List */}
              {isExpanded && (
                <CardContent className="pt-0 space-y-3">
                  <div className="border-t border-border pt-4">
                    <h4 className="font-medium text-foreground mb-3 text-sm">Chapters</h4>
                    <div className="space-y-2">
                      {doc.chapters.map((chapter, idx) => (
                        <div key={idx} className="flex items-center justify-between p-2 rounded bg-muted/30">
                          <div className="flex-1">
                            <p className="text-sm font-medium text-foreground">{chapter.name}</p>
                            <p className="text-xs text-muted-foreground">
                              {chapter.completedCards} / {chapter.totalCards} cards
                            </p>
                          </div>
                          <div className="text-right">
                            <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
                              <span className="text-xs font-bold text-primary">
                                {chapter.completed
                                  ? "✓"
                                  : Math.round((chapter.completedCards / chapter.totalCards) * 100) + "%"}
                              </span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              )}
            </Card>
          )
        })}
      </div>
    </div>
  )
}
