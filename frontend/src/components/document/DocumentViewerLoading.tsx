import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  AlertCircle,
  FileText,
  Loader2,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import type { DocumentStatus } from "@/services/document-service";

export interface DocumentViewerLoadingProps {
  /** 현재 문서 상태 */
  status: DocumentStatus;
  /** 생성 진행률 (0-100) */
  progress?: number;
  /** 에러 메시지 */
  errorMessage?: string;
  /** 재시도 콜백 */
  onRetry?: () => void;
  /** 문서 생성 시작 콜백 */
  onGenerate?: () => void;
  /** 추가 CSS 클래스 */
  className?: string;
}

/**
 * DocumentViewerLoading - 문서 로딩/생성 상태 표시
 *
 * Features:
 * - 상태별 메시지 표시 (pending, generating, error)
 * - 진행률 표시기
 * - 재시도 버튼
 * - 문서 생성 시작 버튼
 */
export function DocumentViewerLoading({
  status,
  progress,
  errorMessage,
  onRetry,
  onGenerate,
  className,
}: DocumentViewerLoadingProps) {
  const renderContent = () => {
    switch (status) {
      case "pending":
        return (
          <div className="text-center space-y-6">
            <div className="flex justify-center">
              <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center">
                <FileText className="h-10 w-10 text-primary" />
              </div>
            </div>
            <div>
              <h3 className="text-lg font-semibold mb-2">문서 생성 대기 중</h3>
              <p className="text-sm text-muted-foreground max-w-md mx-auto">
                AI가 코드를 분석하여 학습 문서를 생성합니다.
                <br />
                문서 생성을 시작하려면 아래 버튼을 클릭하세요.
              </p>
            </div>
            {onGenerate && (
              <Button onClick={onGenerate} className="gap-2">
                <Sparkles className="h-4 w-4" />
                문서 생성
              </Button>
            )}
          </div>
        );

      case "generating":
        return (
          <div className="text-center space-y-6">
            <div className="flex justify-center">
              {progress !== undefined ? (
                <div className="relative w-20 h-20">
                  <svg
                    className="w-full h-full -rotate-90"
                    viewBox="0 0 100 100"
                  >
                    <circle
                      className="text-muted stroke-current"
                      strokeWidth="8"
                      fill="transparent"
                      r="40"
                      cx="50"
                      cy="50"
                    />
                    <circle
                      className="text-primary stroke-current transition-all duration-300"
                      strokeWidth="8"
                      strokeLinecap="round"
                      fill="transparent"
                      r="40"
                      cx="50"
                      cy="50"
                      style={{
                        strokeDasharray: `${2 * Math.PI * 40}`,
                        strokeDashoffset: `${2 * Math.PI * 40 * (1 - progress / 100)}`,
                      }}
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-lg font-semibold">{progress}%</span>
                  </div>
                </div>
              ) : (
                <div
                  data-testid="loading-spinner"
                  className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center"
                >
                  <Loader2 className="h-10 w-10 text-primary animate-spin" />
                </div>
              )}
            </div>
            <div>
              <h3 className="text-lg font-semibold mb-2">문서 생성 중...</h3>
              <p className="text-sm text-muted-foreground max-w-md mx-auto">
                AI가 코드를 분석하고 학습 문서를 생성하고 있습니다.
                <br />
                잠시만 기다려주세요.
              </p>
            </div>
            {progress !== undefined && (
              <div className="max-w-xs mx-auto">
                <Progress value={progress} className="h-2" />
              </div>
            )}
          </div>
        );

      case "error":
        return (
          <div className="text-center space-y-6">
            <div className="flex justify-center">
              <div className="w-20 h-20 rounded-full bg-destructive/10 flex items-center justify-center">
                <AlertCircle className="h-10 w-10 text-destructive" />
              </div>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-destructive mb-2">
                오류가 발생했습니다
              </h3>
              {errorMessage && (
                <p className="text-sm text-muted-foreground max-w-md mx-auto mb-4">
                  {errorMessage}
                </p>
              )}
              <p className="text-sm text-muted-foreground">
                문서 생성 중 문제가 발생했습니다.
              </p>
            </div>
            {onRetry && (
              <Button onClick={onRetry} variant="outline" className="gap-2">
                <RefreshCw className="h-4 w-4" />
                다시 시도
              </Button>
            )}
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div
      className={cn(
        "document-viewer-loading flex items-center justify-center min-h-[400px] p-8",
        className,
      )}
    >
      {renderContent()}
    </div>
  );
}

export default DocumentViewerLoading;
