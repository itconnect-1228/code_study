import { cn } from '@/lib/utils'
import { List } from 'lucide-react'
import type { DocumentChapters } from '@/services/document-service'

export interface Chapter4LineByLineProps {
  /** 챕터 데이터 */
  data: DocumentChapters['lineByLine']
  /** 현재 선택된 라인 번호 */
  selectedLine?: number
  /** 라인 선택 콜백 */
  onLineSelect?: (lineNumber: number) => void
  /** 추가 CSS 클래스 */
  className?: string
}

/**
 * Chapter4LineByLine - 라인별 설명 챕터 컴포넌트
 *
 * Features:
 * - 각 코드 라인에 대한 상세 설명
 * - 라인 번호 표시
 * - 라인 선택/하이라이트 기능
 * - 코드 에디터와의 동기화 지원
 */
export function Chapter4LineByLine({
  data,
  selectedLine,
  onLineSelect,
  className,
}: Chapter4LineByLineProps) {
  const isInteractive = !!onLineSelect

  return (
    <div className={cn('chapter-line-by-line space-y-6', className)}>
      {/* 챕터 헤더 */}
      <div className="flex items-center gap-3">
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-blue-500/10 flex items-center justify-center">
          <List className="h-5 w-5 text-blue-500" />
        </div>
        <h2 className="text-xl font-semibold">{data.title}</h2>
      </div>

      {/* 라인별 설명 목록 */}
      {data.explanations.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">
          <List className="mx-auto h-12 w-12 mb-4 opacity-50" />
          <p>라인별 설명이 없습니다.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {data.explanations.map((item) => {
            const isSelected = selectedLine === item.lineNumber
            const Component = isInteractive ? 'button' : 'div'

            return (
              <Component
                key={item.lineNumber}
                data-testid={`line-item-${item.lineNumber}`}
                data-selected={isSelected}
                onClick={isInteractive ? () => onLineSelect(item.lineNumber) : undefined}
                className={cn(
                  'w-full text-left p-4 rounded-lg border transition-all',
                  isInteractive && 'cursor-pointer hover:border-primary/50 hover:bg-accent/50',
                  isSelected
                    ? 'border-primary bg-primary/5 ring-2 ring-primary/20'
                    : 'border-border bg-card'
                )}
              >
                <div className="flex items-start gap-4">
                  {/* 라인 번호 */}
                  <span
                    className={cn(
                      'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-mono font-medium',
                      isSelected
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted text-muted-foreground'
                    )}
                  >
                    {item.lineNumber}
                  </span>

                  {/* 코드 및 설명 */}
                  <div className="flex-1 min-w-0 space-y-2">
                    {/* 코드 */}
                    <code className="block text-sm bg-muted/50 p-2 rounded font-mono overflow-x-auto whitespace-pre">
                      {item.code}
                    </code>

                    {/* 설명 */}
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {item.explanation}
                    </p>
                  </div>
                </div>
              </Component>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default Chapter4LineByLine
