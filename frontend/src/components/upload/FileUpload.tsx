import {
  useRef,
  useState,
  useCallback,
  type DragEvent,
  type ChangeEvent,
} from "react";
import { Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface FileUploadProps {
  onFileSelect: (files: File[]) => void;
  onError?: (message: string) => void;
  acceptedTypes?: string[];
  maxSize?: number;
  disabled?: boolean;
}

/**
 * FileUpload - File upload component with drag-and-drop and file picker
 *
 * Features:
 * - Drag and drop file upload
 * - Click to open file picker
 * - Multiple file selection
 * - File type filtering
 * - File size validation
 */
export function FileUpload({
  onFileSelect,
  onError,
  acceptedTypes,
  maxSize,
  disabled = false,
}: FileUploadProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFiles = useCallback(
    (files: File[]): File[] | null => {
      if (maxSize) {
        const oversizedFile = files.find((file) => file.size > maxSize);
        if (oversizedFile) {
          onError?.(`파일 크기가 너무 큽니다: ${oversizedFile.name}`);
          return null;
        }
      }
      return files;
    },
    [maxSize, onError],
  );

  const handleFiles = useCallback(
    (files: FileList | null) => {
      if (!files || files.length === 0) return;

      const fileArray = Array.from(files);
      const validatedFiles = validateFiles(fileArray);

      if (validatedFiles) {
        onFileSelect(validatedFiles);
      }
    },
    [onFileSelect, validateFiles],
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

  const handleFileInputChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      handleFiles(e.target.files);
      // Reset input value to allow selecting the same file again
      e.target.value = "";
    },
    [handleFiles],
  );

  const handleButtonClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  return (
    <div
      data-testid="file-drop-zone"
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
      <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
      <p className="text-muted-foreground mb-4">
        파일을 드래그하여 업로드하거나
      </p>
      <Button
        type="button"
        variant="outline"
        onClick={handleButtonClick}
        disabled={disabled}
      >
        파일 선택
      </Button>
      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        multiple
        accept={acceptedTypes?.join(",")}
        onChange={handleFileInputChange}
        disabled={disabled}
      />
      {acceptedTypes && (
        <p className="text-xs text-muted-foreground mt-4">
          지원 형식: {acceptedTypes.join(", ")}
        </p>
      )}
    </div>
  );
}

export default FileUpload;
