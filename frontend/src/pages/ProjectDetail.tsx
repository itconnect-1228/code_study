import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Pencil, Trash2, Loader2, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { projectService } from '@/services/project-service'
import { taskService, type TaskCreateData } from '@/services/task-service'
import { TaskCard } from '@/components/task/TaskCard'
import { CreateTaskModal } from '@/components/task/CreateTaskModal'
import { toast } from 'sonner'

const SUPPORTED_LANGUAGES = ['javascript', 'typescript', 'python', 'java', 'go', 'rust', 'c', 'cpp']

/**
 * Format date to Korean locale string
 */
function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/**
 * ProjectDetail - displays project information and task timeline
 *
 * Features:
 * - Project header with title and description
 * - Project metadata (created, last activity)
 * - Task timeline placeholder (will be implemented in Phase 5)
 * - Edit and delete actions
 */
export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [showEditDialog, setShowEditDialog] = useState(false)
  const [showCreateTaskModal, setShowCreateTaskModal] = useState(false)
  const [editTitle, setEditTitle] = useState('')
  const [editDescription, setEditDescription] = useState('')

  // Fetch project
  const { data: project, isLoading, error } = useQuery({
    queryKey: ['project', id],
    queryFn: () => projectService.getProject(id!),
    enabled: !!id,
  })

  // Fetch tasks
  const { data: tasksData, isLoading: isLoadingTasks } = useQuery({
    queryKey: ['tasks', id],
    queryFn: () => taskService.getTasks(id!),
    enabled: !!id,
  })

  // Edit mutation
  const editMutation = useMutation({
    mutationFn: (data: { title?: string; description?: string }) =>
      projectService.updateProject(id!, data),
    onSuccess: (updatedProject) => {
      queryClient.invalidateQueries({ queryKey: ['project', id] })
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      toast.success(`"${updatedProject.title}" 프로젝트가 수정되었습니다.`)
      setShowEditDialog(false)
    },
    onError: () => {
      toast.error('프로젝트 수정에 실패했습니다.')
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: () => projectService.deleteProject(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      navigate('/dashboard')
    },
  })

  // Create task mutation
  const createTaskMutation = useMutation({
    mutationFn: (data: TaskCreateData) => taskService.createTask(id!, data),
    onSuccess: (newTask) => {
      queryClient.invalidateQueries({ queryKey: ['tasks', id] })
      queryClient.invalidateQueries({ queryKey: ['project', id] })
      toast.success(`"${newTask.title}" 태스크가 생성되었습니다.`)
      setShowCreateTaskModal(false)
    },
    onError: (error: unknown) => {
      // Extract error message from backend response
      let errorMessage = '태스크 생성에 실패했습니다. 다시 시도해주세요.'
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { data?: { detail?: string } } }
        if (axiosError.response?.data?.detail) {
          errorMessage = axiosError.response.data.detail
        }
      }
      toast.error(errorMessage)
    },
  })

  const handleCreateTask = async (data: TaskCreateData) => {
    await createTaskMutation.mutateAsync(data)
  }

  const tasks = tasksData?.tasks ?? []
  const taskCount = tasksData?.total ?? 0

  const handleOpenEditDialog = () => {
    if (project) {
      setEditTitle(project.title)
      setEditDescription(project.description || '')
      setShowEditDialog(true)
    }
  }

  const handleEdit = () => {
    const updates: { title?: string; description?: string } = {}

    if (editTitle.trim() !== project?.title) {
      updates.title = editTitle.trim()
    }
    if (editDescription !== (project?.description || '')) {
      updates.description = editDescription
    }

    if (Object.keys(updates).length > 0) {
      editMutation.mutate(updates)
    } else {
      setShowEditDialog(false)
    }
  }

  const handleDelete = () => {
    deleteMutation.mutate()
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Skeleton className="h-8 w-32 mb-6" />
        <Skeleton className="h-10 w-96 mb-4" />
        <Skeleton className="h-6 w-64 mb-8" />
        <div className="grid gap-4 md:grid-cols-3">
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
        </div>
      </div>
    )
  }

  // Error state
  if (error || !project) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center py-12">
          <h2 className="text-xl font-semibold text-destructive mb-2">
            프로젝트를 찾을 수 없습니다
          </h2>
          <p className="text-muted-foreground mb-4">
            프로젝트가 삭제되었거나 접근 권한이 없습니다.
          </p>
          <Button asChild>
            <Link to="/dashboard">대시보드로 돌아가기</Link>
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Back button */}
      <Button variant="ghost" asChild className="mb-6">
        <Link to="/dashboard">
          <ArrowLeft className="mr-2 h-4 w-4" />
          대시보드
        </Link>
      </Button>

      {/* Project Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">{project.title}</h1>
          {project.description && (
            <p className="text-muted-foreground text-lg">{project.description}</p>
          )}
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleOpenEditDialog}>
            <Pencil className="mr-2 h-4 w-4" />
            편집
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="text-destructive"
            onClick={() => setShowDeleteDialog(true)}
          >
            <Trash2 className="mr-2 h-4 w-4" />
            삭제
          </Button>
        </div>
      </div>

      {/* Project Stats */}
      <div className="grid gap-4 md:grid-cols-3 mb-8">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              생성일
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg font-semibold">{formatDate(project.createdAt)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              마지막 활동
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg font-semibold">{formatDate(project.lastActivityAt)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              학습 태스크
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg font-semibold">{taskCount}개</p>
          </CardContent>
        </Card>
      </div>

      {/* Task Timeline */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>학습 태스크 타임라인</CardTitle>
          <Button size="sm" onClick={() => setShowCreateTaskModal(true)}>
            <Plus className="mr-2 h-4 w-4" />
            새 태스크
          </Button>
        </CardHeader>
        <CardContent>
          {isLoadingTasks ? (
            <div className="space-y-4">
              <Skeleton className="h-24" />
              <Skeleton className="h-24" />
            </div>
          ) : tasks.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <p className="mb-2">아직 태스크가 없습니다.</p>
              <p className="text-sm">코드를 업로드하여 첫 번째 학습 태스크를 만들어보세요.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {tasks.map((task, index) => (
                <TaskCard
                  key={task.id}
                  task={task}
                  isLast={index === tasks.length - 1}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create Task Modal */}
      <CreateTaskModal
        open={showCreateTaskModal}
        onOpenChange={setShowCreateTaskModal}
        onSubmit={handleCreateTask}
        languages={SUPPORTED_LANGUAGES}
      />

      {/* Edit Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>프로젝트 편집</DialogTitle>
            <DialogDescription>
              프로젝트 제목과 설명을 수정할 수 있습니다.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="edit-title">프로젝트 제목 *</Label>
              <Input
                id="edit-title"
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                placeholder="프로젝트 제목을 입력하세요"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-description">설명 (선택)</Label>
              <Textarea
                id="edit-description"
                value={editDescription}
                onChange={(e) => setEditDescription(e.target.value)}
                placeholder="프로젝트 설명을 입력하세요"
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditDialog(false)}>
              취소
            </Button>
            <Button
              onClick={handleEdit}
              disabled={!editTitle.trim() || editMutation.isPending}
            >
              {editMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  저장 중...
                </>
              ) : (
                '저장'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>프로젝트를 삭제하시겠습니까?</AlertDialogTitle>
            <AlertDialogDescription>
              "{project.title}" 프로젝트가 휴지통으로 이동됩니다.
              30일 후 영구 삭제되며, 그 전에 복원할 수 있습니다.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>취소</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive text-white hover:bg-destructive/90"
            >
              {deleteMutation.isPending ? '삭제 중...' : '삭제'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
