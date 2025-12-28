import { cn } from "@/lib/utils";
import { Lightbulb, Sparkles } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DocumentChapters } from "@/services/document-service";

export interface Chapter2PrerequisitesProps {
  /** 챕터 데이터 */
  data: DocumentChapters["prerequisites"];
  /** 추가 CSS 클래스 */
  className?: string;
}

/**
 * Chapter2Prerequisites - 사전 지식 챕터 컴포넌트
 *
 * Features:
 * - 5개 개념 카드 표시
 * - 각 개념에 대한 설명과 비유 포함
 * - 시각적으로 구분된 카드 레이아웃
 */
export function Chapter2Prerequisites({
  data,
  className,
}: Chapter2PrerequisitesProps) {
  return (
    <div className={cn("chapter-prerequisites space-y-6", className)}>
      {/* 챕터 헤더 */}
      <div className="flex items-center gap-3">
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-yellow-500/10 flex items-center justify-center">
          <Lightbulb className="h-5 w-5 text-yellow-500" />
        </div>
        <h2 className="text-xl font-semibold">{data.title}</h2>
      </div>

      {/* 개념 카드 그리드 */}
      {data.concepts.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">
          <Lightbulb className="mx-auto h-12 w-12 mb-4 opacity-50" />
          <p>사전 지식이 없습니다.</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
          {data.concepts.map((concept, index) => (
            <Card key={index} role="article" className="overflow-hidden">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-primary/10 text-primary flex items-center justify-center text-xs font-mono">
                    {index + 1}
                  </span>
                  <h3 className="font-semibold">{concept.name}</h3>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {/* 설명 */}
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {concept.explanation}
                </p>

                {/* 비유 섹션 */}
                <div className="flex items-start gap-2 p-3 rounded-lg bg-gradient-to-r from-purple-500/5 to-pink-500/5 border border-purple-200/20">
                  <Sparkles className="h-4 w-4 text-purple-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <span className="text-xs font-medium text-purple-600 dark:text-purple-400">
                      비유
                    </span>
                    <p className="text-sm text-muted-foreground italic mt-1">
                      {concept.analogy}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

export default Chapter2Prerequisites;
