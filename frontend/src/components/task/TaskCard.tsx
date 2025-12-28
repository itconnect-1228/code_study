import { Link } from "react-router-dom";
import { FileCode, FolderOpen, ClipboardPaste } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { Task } from "@/services/task-service";

export type TaskStatus = "pending" | "generating" | "completed" | "error";
export type UploadType = "file" | "folder" | "paste";

// Re-export Task type for backwards compatibility
export type { Task };

export interface TaskCardProps {
  task: Task;
  onClick?: (task: Task) => void;
  isLast?: boolean;
}

const uploadTypeConfig = {
  file: {
    label: "파일",
    icon: FileCode,
  },
  folder: {
    label: "폴더",
    icon: FolderOpen,
  },
  paste: {
    label: "붙여넣기",
    icon: ClipboardPaste,
  },
};

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

/**
 * TaskCard - Display a task in the timeline
 *
 * Features:
 * - Shows task number, title, upload type
 * - Timeline connector for non-last items
 * - Click handler or link navigation
 */
export function TaskCard({ task, onClick, isLast = false }: TaskCardProps) {
  // Get upload type config, fallback to 'file' if uploadMethod is null
  const uploadMethod = task.uploadMethod || "file";
  const uploadType = uploadTypeConfig[uploadMethod];
  const UploadIcon = uploadType.icon;

  const cardContent = (
    <Card
      role="article"
      className={cn(
        "transition-all cursor-pointer hover:shadow-md",
        onClick && "active:scale-[0.99]",
      )}
      onClick={onClick ? () => onClick(task) : undefined}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-sm font-semibold text-primary">
                Task {task.taskNumber}
              </span>
            </div>
            <h3 className="text-base font-medium truncate">{task.title}</h3>
            <div className="flex items-center gap-3 mt-2 text-sm text-muted-foreground">
              <div className="flex items-center gap-1">
                <UploadIcon className="h-3.5 w-3.5" />
                <span>{uploadType.label}</span>
              </div>
              <span>{formatDate(task.createdAt)}</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div
      data-testid="task-card-container"
      className={cn("relative", !isLast && "task-card-with-connector pb-4")}
    >
      {onClick ? (
        cardContent
      ) : (
        <Link to={`/tasks/${task.id}`}>{cardContent}</Link>
      )}
    </div>
  );
}

export default TaskCard;
