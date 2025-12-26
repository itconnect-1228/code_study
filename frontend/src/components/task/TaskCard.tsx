import { Link } from 'react-router-dom'
import { FileCode, FolderOpen, ClipboardPaste, Clock, CheckCircle2, Loader2, AlertCircle } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

export type TaskStatus = 'pending' | 'generating' | 'completed' | 'error'
export type UploadType = 'file' | 'folder' | 'paste'

export interface Task {
  id: string
  taskNumber: number
  title: string
  status: TaskStatus
  codeLanguage: string
  uploadType: UploadType
  createdAt: string
}

export interface TaskCardProps {
  task: Task
  onClick?: (task: Task) => void
  isLast?: boolean
}

const statusConfig = {
  pending: {
    label: '대기중',
    icon: Clock,
    className: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  },
  generating: {
    label: '생성중',
    icon: Loader2,
    className: 'bg-blue-100 text-blue-800 border-blue-200',
  },
  completed: {
    label: '완료',
    icon: CheckCircle2,
    className: 'bg-green-100 text-green-800 border-green-200',
  },
  error: {
    label: '오류',
    icon: AlertCircle,
    className: 'bg-red-100 text-red-800 border-red-200',
  },
}

const uploadTypeConfig = {
  file: {
    label: '파일',
    icon: FileCode,
  },
  folder: {
    label: '폴더',
    icon: FolderOpen,
  },
  paste: {
    label: '붙여넣기',
    icon: ClipboardPaste,
  },
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

/**
 * TaskCard - Display a task in the timeline
 *
 * Features:
 * - Shows task number, title, status, language, upload type
 * - Visual status indicators
 * - Timeline connector for non-last items
 * - Click handler or link navigation
 */
export function TaskCard({ task, onClick, isLast = false }: TaskCardProps) {
  const status = statusConfig[task.status]
  const uploadType = uploadTypeConfig[task.uploadType]
  const StatusIcon = status.icon
  const UploadIcon = uploadType.icon

  const cardContent = (
    <Card
      role="article"
      className={cn(
        'transition-all cursor-pointer hover:shadow-md',
        onClick && 'active:scale-[0.99]'
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
              <Badge variant="outline" className="text-xs capitalize">
                {task.codeLanguage}
              </Badge>
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
          <Badge
            variant="outline"
            className={cn('flex items-center gap-1 shrink-0', status.className)}
          >
            <StatusIcon
              className={cn(
                'h-3.5 w-3.5',
                task.status === 'generating' && 'animate-spin'
              )}
            />
            <span>{status.label}</span>
          </Badge>
        </div>
      </CardContent>
    </Card>
  )

  return (
    <div
      data-testid="task-card-container"
      className={cn(
        'relative',
        !isLast && 'task-card-with-connector pb-4'
      )}
    >
      {onClick ? (
        cardContent
      ) : (
        <Link to={`/tasks/${task.id}`}>{cardContent}</Link>
      )}
    </div>
  )
}

export default TaskCard
