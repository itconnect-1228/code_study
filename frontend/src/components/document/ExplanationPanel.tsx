import { useState, useCallback } from 'react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Chapter4LineByLine } from './chapters/Chapter4'
import type { LearningDocument } from '@/services/document-service'
import {
  FileText,
  Lightbulb,
  Target,
  List,
  BookOpen,
  Repeat,
  PenTool,
} from 'lucide-react'

/**
 * 챕터 타입 정의
 */
export type ChapterKey =
  | 'summary'
  | 'prerequisites'
  | 'coreLogic'
  | 'lineByLine'
  | 'syntaxReference'
  | 'commonPatterns'
  | 'exercises'

/**
 * 챕터 설정
 */
const CHAPTERS: { key: ChapterKey; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { key: 'summary', label: '요약', icon: FileText },
  { key: 'prerequisites', label: '사전 지식', icon: Lightbulb },
  { key: 'coreLogic', label: '핵심 로직', icon: Target },
  { key: 'lineByLine', label: '라인별', icon: List },
  { key: 'syntaxReference', label: '문법', icon: BookOpen },
  { key: 'commonPatterns', label: '패턴', icon: Repeat },
  { key: 'exercises', label: '연습', icon: PenTool },
]

export interface ExplanationPanelProps {
  /** 학습 문서 데이터 */
  document: LearningDocument
  /** 현재 선택된 챕터 (외부에서 제어할 경우) */
  currentChapter?: ChapterKey
  /** 챕터 변경 콜백 */
  onChapterChange?: (chapter: ChapterKey) => void
  /** 선택된 라인 번호 */
  selectedLine?: number
  /** 라인 선택 콜백 */
  onLineSelect?: (lineNumber: number) => void
  /** 추가 CSS 클래스 */
  className?: string
}

/**
 * ExplanationPanel - 학습 문서 설명 패널
 *
 * Features:
 * - 7개 챕터 네비게이션
 * - 현재 챕터 하이라이트
 * - 챕터별 콘텐츠 렌더링
 */
export function ExplanationPanel({
  document,
  currentChapter: controlledChapter,
  onChapterChange,
  selectedLine,
  onLineSelect,
  className,
}: ExplanationPanelProps) {
  const [internalChapter, setInternalChapter] = useState<ChapterKey>('summary')

  // 외부 제어 또는 내부 상태 사용
  const activeChapter = controlledChapter ?? internalChapter

  const handleChapterClick = useCallback(
    (chapter: ChapterKey) => {
      if (!controlledChapter) {
        setInternalChapter(chapter)
      }
      onChapterChange?.(chapter)
    },
    [controlledChapter, onChapterChange]
  )

  const renderChapterContent = () => {
    const chapters = document.chapters

    switch (activeChapter) {
      case 'summary':
        return (
          <div className="prose dark:prose-invert max-w-none">
            <h2>{chapters.summary.title}</h2>
            <p>{chapters.summary.content}</p>
          </div>
        )

      case 'prerequisites':
        return (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">{chapters.prerequisites.title}</h2>
            <div className="grid gap-4">
              {chapters.prerequisites.concepts.map((concept, index) => (
                <div
                  key={index}
                  className="p-4 rounded-lg border bg-card"
                >
                  <h3 className="font-semibold text-lg mb-2">{concept.name}</h3>
                  <p className="text-muted-foreground mb-2">{concept.explanation}</p>
                  <div className="text-sm italic text-primary">
                    <span className="font-medium">비유: </span>
                    {concept.analogy}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )

      case 'coreLogic':
        return (
          <div className="prose dark:prose-invert max-w-none">
            <h2>{chapters.coreLogic.title}</h2>
            <p>{chapters.coreLogic.content}</p>
          </div>
        )

      case 'lineByLine':
        return (
          <Chapter4LineByLine
            data={chapters.lineByLine}
            selectedLine={selectedLine}
            onLineSelect={onLineSelect}
          />
        )

      case 'syntaxReference':
        return (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">{chapters.syntaxReference.title}</h2>
            <div className="space-y-2">
              {chapters.syntaxReference.items.map((item, index) => (
                <div
                  key={index}
                  className="flex items-start gap-3 p-3 rounded-lg border bg-card"
                >
                  <code className="flex-shrink-0 px-2 py-1 rounded bg-primary/10 text-primary font-mono text-sm">
                    {item.syntax}
                  </code>
                  <span className="text-sm text-muted-foreground">{item.description}</span>
                </div>
              ))}
            </div>
          </div>
        )

      case 'commonPatterns':
        return (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">{chapters.commonPatterns.title}</h2>
            <div className="space-y-3">
              {chapters.commonPatterns.patterns.map((pattern, index) => (
                <div
                  key={index}
                  className="p-4 rounded-lg border bg-card"
                >
                  <h3 className="font-semibold mb-2">{pattern.name}</h3>
                  <p className="text-sm text-muted-foreground">{pattern.description}</p>
                </div>
              ))}
            </div>
          </div>
        )

      case 'exercises':
        return (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">{chapters.exercises.title}</h2>
            <div className="space-y-3">
              {chapters.exercises.items.map((exercise, index) => (
                <div
                  key={index}
                  className="p-4 rounded-lg border bg-card"
                >
                  <div className="flex items-start gap-3">
                    <span className="flex-shrink-0 w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-semibold">
                      {index + 1}
                    </span>
                    <div>
                      <p className="font-medium mb-2">{exercise.question}</p>
                      <p className="text-sm text-muted-foreground">
                        <span className="font-medium">힌트: </span>
                        {exercise.hint}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )

      default:
        return null
    }
  }

  return (
    <div className={cn('explanation-panel flex flex-col h-full', className)}>
      {/* 챕터 네비게이션 */}
      <div className="flex-shrink-0 border-b bg-muted/50">
        <nav className="flex overflow-x-auto p-2 gap-1" role="tablist">
          {CHAPTERS.map(({ key, label, icon: Icon }) => (
            <Button
              key={key}
              variant="ghost"
              size="sm"
              role="tab"
              data-active={activeChapter === key}
              aria-selected={activeChapter === key}
              onClick={() => handleChapterClick(key)}
              className={cn(
                'flex items-center gap-2 flex-shrink-0',
                activeChapter === key && 'bg-background shadow-sm'
              )}
            >
              <Icon className="h-4 w-4" />
              <span>{label}</span>
            </Button>
          ))}
        </nav>
      </div>

      {/* 챕터 콘텐츠 */}
      <ScrollArea className="flex-1">
        <div className="p-4">{renderChapterContent()}</div>
      </ScrollArea>
    </div>
  )
}

export default ExplanationPanel
