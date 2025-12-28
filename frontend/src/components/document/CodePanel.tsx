import Editor from "@monaco-editor/react";
import { cn } from "@/lib/utils";

export interface CodePanelProps {
  /** 표시할 코드 */
  code: string;
  /** 프로그래밍 언어 (구문 강조용) */
  language: string;
  /** 하이라이트할 라인 번호들 */
  highlightedLines?: number[];
  /** 파일명 (선택사항) */
  filename?: string;
  /** 추가 CSS 클래스 */
  className?: string;
  /** 에디터 높이 (기본값: 100%) */
  height?: string;
}

/**
 * CodePanel - Monaco Editor를 사용한 코드 표시 패널 (읽기 전용)
 *
 * Features:
 * - Monaco Editor 기반 구문 강조
 * - 라인 번호 표시
 * - 특정 라인 하이라이트 지원
 * - 읽기 전용 모드
 */
export function CodePanel({
  code,
  language,
  highlightedLines = [],
  filename,
  className,
  height = "100%",
}: CodePanelProps) {
  return (
    <div className={cn("code-panel flex flex-col h-full", className)}>
      {/* 파일명 헤더 */}
      {filename && (
        <div
          data-testid="code-panel-header"
          className="flex items-center px-4 py-2 bg-muted border-b text-sm font-mono"
        >
          <span className="text-muted-foreground">{filename}</span>
        </div>
      )}

      {/* Monaco Editor */}
      <div className="flex-1 min-h-0">
        <Editor
          height={height}
          language={language}
          value={code}
          theme="vs-dark"
          options={{
            readOnly: true,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            fontSize: 14,
            lineNumbers: "on",
            renderLineHighlight: "all",
            wordWrap: "on",
            automaticLayout: true,
            folding: true,
            lineDecorationsWidth: 0,
            lineNumbersMinChars: 3,
            glyphMargin: highlightedLines.length > 0,
          }}
          onMount={(editor, monaco) => {
            // 하이라이트 라인 설정
            if (highlightedLines.length > 0) {
              const decorations = highlightedLines.map((line) => ({
                range: new monaco.Range(line, 1, line, 1),
                options: {
                  isWholeLine: true,
                  className: "highlighted-line",
                  glyphMarginClassName: "highlighted-line-glyph",
                },
              }));
              editor.createDecorationsCollection(decorations);
            }
          }}
        />
      </div>
    </div>
  );
}

export default CodePanel;
