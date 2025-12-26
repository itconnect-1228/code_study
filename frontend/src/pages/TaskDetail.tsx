import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Clock, CheckCircle2, Loader2, AlertCircle, FileCode, Book, Dumbbell, MessageSquare } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { taskService } from '@/services/task-service'
import { cn } from '@/lib/utils'

type TaskStatus = 'pending' | 'generating' | 'completed' | 'error'

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
 * TaskDetail - displays task information with tabs for Document, Practice, Q&A
 *
 * Features:
 * - Task header with title, status, language
 * - Three tabs: Document (학습 문서), Practice (실습), Q&A (질문과 답변)
 * - Placeholder content for future phases
 */
export default function TaskDetail() {
  const { id } = useParams<{ id: string }>()

  const { data: task, isLoading, error } = useQuery({
    queryKey: ['task', id],
    queryFn: () => taskService.getTask(id!),
    enabled: !!id,
  })

  // Loading state
  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Skeleton className="h-8 w-32 mb-6" />
        <Skeleton className="h-10 w-96 mb-4" />
        <Skeleton className="h-6 w-64 mb-8" />
        <Skeleton className="h-96" />
      </div>
    )
  }

  // Error state
  if (error || !task) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center py-12">
          <h2 className="text-xl font-semibold text-destructive mb-2">
            태스크를 찾을 수 없습니다
          </h2>
          <p className="text-muted-foreground mb-4">
            태스크가 삭제되었거나 접근 권한이 없습니다.
          </p>
          <Button asChild>
            <Link to="/dashboard">대시보드로 돌아가기</Link>
          </Button>
        </div>
      </div>
    )
  }

  const status = statusConfig[task.status as TaskStatus]
  const StatusIcon = status.icon

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Back button */}
      <Button variant="ghost" asChild className="mb-6">
        <Link to="/dashboard">
          <ArrowLeft className="mr-2 h-4 w-4" />
          뒤로
        </Link>
      </Button>

      {/* Task Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <span className="text-lg font-semibold text-primary">Task {task.taskNumber}</span>
            <Badge variant="outline" className="capitalize">
              {task.codeLanguage}
            </Badge>
            <Badge
              variant="outline"
              className={cn('flex items-center gap-1', status.className)}
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
          <h1 className="text-3xl font-bold mb-2">{task.title}</h1>
          <p className="text-sm text-muted-foreground">
            생성일: {formatDate(task.createdAt)}
          </p>
        </div>
      </div>

      {/* Content Tabs */}
      <Tabs defaultValue="document" className="space-y-4">
        <TabsList>
          <TabsTrigger value="document" className="gap-2">
            <Book className="h-4 w-4" />
            문서
          </TabsTrigger>
          <TabsTrigger value="practice" className="gap-2">
            <Dumbbell className="h-4 w-4" />
            실습
          </TabsTrigger>
          <TabsTrigger value="qna" className="gap-2">
            <MessageSquare className="h-4 w-4" />
            Q&A
          </TabsTrigger>
        </TabsList>

        {/* Document Tab */}
        <TabsContent value="document">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileCode className="h-5 w-5" />
                학습 문서
              </CardTitle>
            </CardHeader>
            <CardContent>
              {task.status === 'pending' && (
                <div className="text-center py-12 text-muted-foreground">
                  <Clock className="mx-auto h-12 w-12 mb-4" />
                  <p className="mb-2">문서 생성을 기다리고 있습니다.</p>
                  <p className="text-sm">잠시 후 자동으로 시작됩니다.</p>
                </div>
              )}
              {task.status === 'generating' && (
                <div className="text-center py-12 text-muted-foreground">
                  <Loader2 className="mx-auto h-12 w-12 mb-4 animate-spin" />
                  <p className="mb-2">학습 문서를 생성하고 있습니다...</p>
                  <p className="text-sm">AI가 코드를 분석하고 있습니다. 잠시만 기다려주세요.</p>
                </div>
              )}
              {task.status === 'completed' && (
                <div className="text-center py-12 text-muted-foreground">
                  <CheckCircle2 className="mx-auto h-12 w-12 mb-4 text-green-500" />
                  <p className="mb-2">학습 문서가 준비되었습니다.</p>
                  <p className="text-sm">Phase 6에서 문서 뷰어가 구현될 예정입니다.</p>
                </div>
              )}
              {task.status === 'error' && (
                <div className="text-center py-12 text-destructive">
                  <AlertCircle className="mx-auto h-12 w-12 mb-4" />
                  <p className="mb-2">문서 생성 중 오류가 발생했습니다.</p>
                  <p className="text-sm text-muted-foreground">
                    다시 시도하거나 관리자에게 문의해주세요.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Practice Tab */}
        <TabsContent value="practice">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Dumbbell className="h-5 w-5" />
                실습 문제
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12 text-muted-foreground">
                <Dumbbell className="mx-auto h-12 w-12 mb-4" />
                <p className="mb-2">실습 문제가 곧 제공됩니다.</p>
                <p className="text-sm">Phase 7에서 구현될 예정입니다.</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Q&A Tab */}
        <TabsContent value="qna">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5" />
                질문과 답변
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12 text-muted-foreground">
                <MessageSquare className="mx-auto h-12 w-12 mb-4" />
                <p className="mb-2">AI에게 질문할 수 있습니다.</p>
                <p className="text-sm">Phase 8에서 구현될 예정입니다.</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
