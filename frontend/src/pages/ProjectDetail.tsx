import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Pencil, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
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
import { projectService } from '@/services/project-service'

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

  // Fetch project
  const { data: project, isLoading, error } = useQuery({
    queryKey: ['project', id],
    queryFn: () => projectService.getProject(id!),
    enabled: !!id,
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: () => projectService.deleteProject(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      navigate('/dashboard')
    },
  })

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
          <Button variant="outline" size="sm" disabled>
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
            <p className="text-lg font-semibold">0개</p>
            <p className="text-xs text-muted-foreground">Phase 5에서 구현 예정</p>
          </CardContent>
        </Card>
      </div>

      {/* Task Timeline Placeholder */}
      <Card>
        <CardHeader>
          <CardTitle>학습 태스크 타임라인</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12 text-muted-foreground">
            <p className="mb-2">아직 태스크가 없습니다.</p>
            <p className="text-sm">Phase 5에서 코드 업로드 기능이 구현될 예정입니다.</p>
          </div>
        </CardContent>
      </Card>

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
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deleteMutation.isPending ? '삭제 중...' : '삭제'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
