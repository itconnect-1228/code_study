import { cn } from "@/lib/utils";
import { FileText } from "lucide-react";
import type { DocumentChapters } from "@/services/document-service";

export interface Chapter1SummaryProps {
  /** 챕터 데이터 */
  data: DocumentChapters["summary"];
  /** 추가 CSS 클래스 */
  className?: string;
}

/**
 * Chapter1Summary - 코드 요약 챕터 컴포넌트
 *
 * Features:
 * - 코드 전체 요약 표시
 * - 마크다운 스타일 렌더링 지원
 */
export function Chapter1Summary({ data, className }: Chapter1SummaryProps) {
  // 간단한 인라인 코드 렌더링 (` 로 감싸진 텍스트)
  const renderContent = (content: string) => {
    if (!content) return null;

    // 인라인 코드 패턴 처리
    const parts = content.split(/(`[^`]+`)/);

    return parts.map((part, index) => {
      if (part.startsWith("`") && part.endsWith("`")) {
        const code = part.slice(1, -1);
        return (
          <code
            key={index}
            className="px-1.5 py-0.5 rounded bg-muted text-primary font-mono text-sm"
          >
            {code}
          </code>
        );
      }
      return <span key={index}>{part}</span>;
    });
  };

  return (
    <div className={cn("chapter-summary space-y-4", className)}>
      {/* 챕터 헤더 */}
      <div className="flex items-center gap-3">
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
          <FileText className="h-5 w-5 text-primary" />
        </div>
        <h2 className="text-xl font-semibold">{data.title}</h2>
      </div>

      {/* 요약 콘텐츠 */}
      <div className="prose dark:prose-invert max-w-none">
        {data.content.split("\n\n").map((paragraph, index) => (
          <p key={index} className="text-muted-foreground leading-relaxed">
            {renderContent(paragraph)}
          </p>
        ))}
      </div>
    </div>
  );
}

export default Chapter1Summary;
