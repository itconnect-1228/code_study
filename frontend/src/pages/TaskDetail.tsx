import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, FileCode, FolderOpen, ClipboardPaste, Book, Dumbbell, MessageSquare, CheckCircle, Loader2, Clock, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { taskService } from '@/services/task-service'
import { documentService } from '@/services/document-service'
import { DocumentViewer } from '@/components/document/DocumentViewer'
import { DocumentViewerLoading } from '@/components/document/DocumentViewerLoading'

const uploadMethodConfig = {
  file: { label: '파일', icon: FileCode },
  folder: { label: '폴더', icon: FolderOpen },
  paste: { label: '붙여넣기', icon: ClipboardPaste },
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

  const queryClient = useQueryClient()

  const { data: task, isLoading, error } = useQuery({
    queryKey: ['task', id],
    queryFn: () => taskService.getTask(id!),
    enabled: !!id,
  })

  // Fetch code files for the task
  const { data: codeFilesData } = useQuery({
    queryKey: ['taskCode', id],
    queryFn: () => taskService.getTaskCode(id!),
    enabled: !!id,
  })

  // Fetch learning document
  const { data: document, isLoading: isDocumentLoading, refetch: refetchDocument } = useQuery({
    queryKey: ['document', id],
    queryFn: () => documentService.getDocument(id!),
    enabled: !!id,
    refetchInterval: (query) => {
      // Poll every 3 seconds if document is generating
      const doc = query.state.data
      if (doc?.status === 'generating') {
        return 3000
      }
      return false
    },
  })

  // Generate document mutation
  const generateDocumentMutation = useMutation({
    mutationFn: () => documentService.generateDocument(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['document', id] })
    },
  })

  const handleGenerateDocument = () => {
    generateDocumentMutation.mutate()
  }

  const handleRetryDocument = () => {
    refetchDocument()
  }

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

  const uploadMethod = task.uploadMethod || 'file'
  const uploadConfig = uploadMethodConfig[uploadMethod]
  const UploadIcon = uploadConfig.icon

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Back button */}
      <Button variant="ghost" asChild className="mb-6">
        <Link to={`/projects/${task.projectId}`}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          뒤로
        </Link>
      </Button>

      {/* Task Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <span className="text-lg font-semibold text-primary">Task {task.taskNumber}</span>
            <Badge variant="outline" className="flex items-center gap-1">
              <UploadIcon className="h-3.5 w-3.5" />
              <span>{uploadConfig.label}</span>
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
                {document?.status === 'completed' && (
                  <Badge variant="secondary" className="gap-1">
                    <CheckCircle className="h-3 w-3" />
                    완료
                  </Badge>
                )}
                {document?.status === 'generating' && (
                  <Badge variant="outline" className="gap-1">
                    <Loader2 className="h-3 w-3 animate-spin" />
                    생성중
                  </Badge>
                )}
                {document?.status === 'pending' && (
                  <Badge variant="outline" className="gap-1">
                    <Clock className="h-3 w-3" />
                    대기중
                  </Badge>
                )}
                {document?.status === 'error' && (
                  <Badge variant="destructive" className="gap-1">
                    <AlertCircle className="h-3 w-3" />
                    오류
                  </Badge>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {/* Document content */}
              {isDocumentLoading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
              ) : document?.status === 'completed' ? (
                <div className="h-[600px]">
                  <DocumentViewer
                    document={document}
                    codeFile={codeFilesData?.files?.[0]}
                  />
                </div>
              ) : document?.status === 'generating' ? (
                <DocumentViewerLoading
                  status="generating"
                  progress={undefined}
                />
              ) : document?.status === 'error' ? (
                <DocumentViewerLoading
                  status="error"
                  errorMessage={document.errorMessage}
                  onRetry={handleRetryDocument}
                />
              ) : (
                /* No document or pending status */
                <div className="text-center py-12 text-muted-foreground">
                  <Book className="mx-auto h-12 w-12 mb-4" />
                  <p className="mb-2">학습 문서가 준비되었습니다.</p>
                  <p className="text-sm mb-4">AI가 코드를 분석하여 학습 문서를 생성합니다.</p>
                  <Button onClick={handleGenerateDocument} disabled={generateDocumentMutation.isPending}>
                    {generateDocumentMutation.isPending ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        생성 중...
                      </>
                    ) : (
                      '문서 생성'
                    )}
                  </Button>
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
