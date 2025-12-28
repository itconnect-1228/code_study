import {
  useRef,
  useState,
  useCallback,
  type DragEvent,
  type ChangeEvent,
} from "react";
import { FolderOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface FolderUploadProps {
  onFolderSelect: (files: File[]) => void;
  onError?: (message: string) => void;
  maxFiles?: number;
  disabled?: boolean;
}

/**
 * FolderUpload - Folder upload component with drag-and-drop
 *
 * Features:
 * - Drag and drop folder upload
 * - Click to open folder picker
 * - Preserves directory structure via webkitRelativePath
 * - File count validation
 */
export function FolderUpload({
  onFolderSelect,
  onError,
  maxFiles,
  disabled = false,
}: FolderUploadProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const folderInputRef = useRef<HTMLInputElement>(null);

  const validateFiles = useCallback(
    (files: File[]): File[] | null => {
      if (maxFiles && files.length > maxFiles) {
        onError?.(
          `파일 수가 너무 많습니다. 최대 ${maxFiles}개까지 허용됩니다.`,
        );
        return null;
      }
      return files;
    },
    [maxFiles, onError],
  );

  const handleFiles = useCallback(
    (files: FileList | null) => {
      if (!files || files.length === 0) return;

      const fileArray = Array.from(files);
      const validatedFiles = validateFiles(fileArray);

      if (validatedFiles) {
        onFolderSelect(validatedFiles);
      }
    },
    [onFolderSelect, validateFiles],
  );

  const handleDragEnter = useCallback(
    (e: DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      e.stopPropagation();
      if (!disabled) {
        setIsDragOver(true);
      }
    },
    [disabled],
  );

  const handleDragLeave = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleDragOver = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback(
    (e: DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragOver(false);

      if (disabled) return;

      handleFiles(e.dataTransfer.files);
    },
    [disabled, handleFiles],
  );

  const handleFolderInputChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      handleFiles(e.target.files);
      // Reset input value to allow selecting the same folder again
      e.target.value = "";
    },
    [handleFiles],
  );

  const handleButtonClick = useCallback(() => {
    folderInputRef.current?.click();
  }, []);

  return (
    <div
      data-testid="folder-drop-zone"
      className={cn(
        "border-2 border-dashed rounded-lg p-8 text-center transition-colors",
        isDragOver
          ? "border-primary bg-primary/5"
          : "border-muted-foreground/25",
        disabled && "opacity-50 cursor-not-allowed",
      )}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
    >
      <FolderOpen className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
      <p className="text-muted-foreground mb-4">
        폴더를 드래그하여 업로드하거나
      </p>
      <Button
        type="button"
        variant="outline"
        onClick={handleButtonClick}
        disabled={disabled}
      >
        폴더 선택
      </Button>
      <input
        ref={folderInputRef}
        type="file"
        className="hidden"
        onChange={handleFolderInputChange}
        disabled={disabled}
        {...{ webkitdirectory: "" }}
      />
      <p className="text-xs text-muted-foreground mt-4">
        폴더 구조가 보존됩니다
      </p>
      {maxFiles && (
        <p className="text-xs text-muted-foreground">최대 {maxFiles}개 파일</p>
      )}
    </div>
  );
}

export default FolderUpload;
