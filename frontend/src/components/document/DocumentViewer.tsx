import { useState, useCallback } from "react";
import { cn } from "@/lib/utils";
import { CodePanel } from "./CodePanel";
import { ExplanationPanel, type ChapterKey } from "./ExplanationPanel";
import { FileCode } from "lucide-react";
import type { LearningDocument } from "@/services/document-service";
import type { CodeFile } from "@/services/task-service";

export interface DocumentViewerProps {
  /** 학습 문서 데이터 */
  document: LearningDocument;
  /** 코드 파일 (선택사항) */
  codeFile?: CodeFile;
  /** 라인 선택 콜백 */
  onLineSelect?: (lineNumber: number) => void;
  /** 추가 CSS 클래스 */
  className?: string;
}

/**
 * DocumentViewer - 2단 레이아웃 문서 뷰어
 *
 * Features:
 * - 왼쪽: CodePanel (Monaco Editor)
 * - 오른쪽: ExplanationPanel (챕터 네비게이션 + 콘텐츠)
 * - 스크롤 동기화 (라인별 설명 ↔ 코드)
 */
export function DocumentViewer({
  document,
  codeFile,
  onLineSelect,
  className,
}: DocumentViewerProps) {
  const [currentChapter, setCurrentChapter] = useState<ChapterKey>("summary");
  const [selectedLine, setSelectedLine] = useState<number | undefined>();

  // 챕터 변경 핸들러
  const handleChapterChange = useCallback((chapter: ChapterKey) => {
    setCurrentChapter(chapter);
    // 챕터가 변경되면 라인 선택 초기화
    if (chapter !== "lineByLine") {
      setSelectedLine(undefined);
    }
  }, []);

  // 라인 선택 핸들러
  const handleLineSelect = useCallback(
    (lineNumber: number) => {
      setSelectedLine(lineNumber);
      onLineSelect?.(lineNumber);
    },
    [onLineSelect],
  );

  // 하이라이트할 라인 계산
  const highlightedLines = selectedLine ? [selectedLine] : [];

  return (
    <div className={cn("document-viewer h-full flex flex-col", className)}>
      <div className="document-viewer-layout flex-1 grid grid-cols-1 lg:grid-cols-2 gap-4 min-h-0">
        {/* 왼쪽: 코드 패널 */}
        <div
          data-testid="code-panel"
          className="flex flex-col min-h-0 border rounded-lg overflow-hidden bg-[#1e1e1e]"
        >
          {codeFile ? (
            <CodePanel
              code={codeFile.content}
              language={codeFile.language}
              filename={codeFile.filename}
              highlightedLines={highlightedLines}
              className="h-full"
            />
          ) : (
            <div className="flex-1 flex items-center justify-center text-muted-foreground">
              <div className="text-center p-8">
                <FileCode className="mx-auto h-12 w-12 mb-4 opacity-50" />
                <p>코드 파일이 없습니다.</p>
              </div>
            </div>
          )}
        </div>

        {/* 오른쪽: 설명 패널 */}
        <div
          data-testid="explanation-panel"
          className="flex flex-col min-h-0 border rounded-lg overflow-hidden bg-card"
        >
          <ExplanationPanel
            document={document}
            currentChapter={currentChapter}
            onChapterChange={handleChapterChange}
            selectedLine={selectedLine}
            onLineSelect={handleLineSelect}
            className="h-full"
          />
        </div>
      </div>
    </div>
  );
}

export default DocumentViewer;
