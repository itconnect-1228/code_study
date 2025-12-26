import { useState, useCallback } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { FileUpload } from '@/components/upload/FileUpload'
import { FolderUpload } from '@/components/upload/FolderUpload'
import { PasteCode, type PasteCodeData } from '@/components/upload/PasteCode'
import { FileCode, FolderOpen, ClipboardPaste } from 'lucide-react'

export interface TaskCreateData {
  title: string
  uploadType: 'file' | 'folder' | 'paste'
  files?: File[]
  code?: string
  language?: string
}

export interface CreateTaskModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSubmit: (data: TaskCreateData) => Promise<void>
  languages: string[]
}

type UploadTab = 'file' | 'folder' | 'paste'

/**
 * CreateTaskModal - Modal for creating a new task with code upload
 *
 * Features:
 * - Title input
 * - Three upload methods: File, Folder, Paste
 * - Tabs for switching between upload methods
 * - Validation before submission
 */
export function CreateTaskModal({
  open,
  onOpenChange,
  onSubmit,
  languages,
}: CreateTaskModalProps) {
  const [title, setTitle] = useState('')
  const [activeTab, setActiveTab] = useState<UploadTab>('file')
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [pastedCode, setPastedCode] = useState<PasteCodeData | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const resetForm = useCallback(() => {
    setTitle('')
    setActiveTab('file')
    setSelectedFiles([])
    setPastedCode(null)
    setError(null)
  }, [])

  const handleFileSelect = useCallback((files: File[]) => {
    setSelectedFiles(files)
    setError(null)
  }, [])

  const handleFolderSelect = useCallback((files: File[]) => {
    setSelectedFiles(files)
    setError(null)
  }, [])

  const handlePaste = useCallback((data: PasteCodeData) => {
    setPastedCode(data)
    setError(null)
  }, [])

  const handleUploadError = useCallback((message: string) => {
    setError(message)
  }, [])

  const isFormValid = useCallback(() => {
    if (!title.trim()) return false

    switch (activeTab) {
      case 'file':
      case 'folder':
        return selectedFiles.length > 0
      case 'paste':
        return pastedCode !== null && pastedCode.code.trim().length > 0
      default:
        return false
    }
  }, [title, activeTab, selectedFiles, pastedCode])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!title.trim()) {
      setError('제목을 입력해주세요.')
      return
    }

    if (activeTab === 'paste' && !pastedCode?.code.trim()) {
      setError('코드를 입력해주세요.')
      return
    }

    if ((activeTab === 'file' || activeTab === 'folder') && selectedFiles.length === 0) {
      setError('파일을 선택해주세요.')
      return
    }

    setIsSubmitting(true)
    try {
      let data: TaskCreateData

      if (activeTab === 'paste' && pastedCode) {
        data = {
          title: title.trim(),
          uploadType: 'paste',
          code: pastedCode.code,
          language: pastedCode.language,
        }
      } else {
        data = {
          title: title.trim(),
          uploadType: activeTab,
          files: selectedFiles,
        }
      }

      await onSubmit(data)
      resetForm()
      onOpenChange(false)
    } catch (err) {
      setError('태스크 생성에 실패했습니다. 다시 시도해주세요.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleClose = () => {
    if (!isSubmitting) {
      resetForm()
      onOpenChange(false)
    }
  }

  const handleTabChange = (value: string) => {
    setActiveTab(value as UploadTab)
    setSelectedFiles([])
    setPastedCode(null)
    setError(null)
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[600px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>새 태스크 만들기</DialogTitle>
            <DialogDescription>
              코드를 업로드하고 학습 문서를 생성합니다.
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="title">태스크 제목 *</Label>
              <Input
                id="title"
                placeholder="예: JavaScript 비동기 처리 학습"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                disabled={isSubmitting}
                autoFocus
              />
            </div>

            <Tabs value={activeTab} onValueChange={handleTabChange}>
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="file" disabled={isSubmitting}>
                  <FileCode className="h-4 w-4 mr-2" />
                  파일
                </TabsTrigger>
                <TabsTrigger value="folder" disabled={isSubmitting}>
                  <FolderOpen className="h-4 w-4 mr-2" />
                  폴더
                </TabsTrigger>
                <TabsTrigger value="paste" disabled={isSubmitting}>
                  <ClipboardPaste className="h-4 w-4 mr-2" />
                  붙여넣기
                </TabsTrigger>
              </TabsList>

              <TabsContent value="file" className="mt-4">
                <FileUpload
                  onFileSelect={handleFileSelect}
                  onError={handleUploadError}
                  disabled={isSubmitting}
                />
                {selectedFiles.length > 0 && activeTab === 'file' && (
                  <p className="text-sm text-muted-foreground mt-2">
                    {selectedFiles.length}개 파일 선택됨
                  </p>
                )}
              </TabsContent>

              <TabsContent value="folder" className="mt-4">
                <FolderUpload
                  onFolderSelect={handleFolderSelect}
                  onError={handleUploadError}
                  disabled={isSubmitting}
                />
                {selectedFiles.length > 0 && activeTab === 'folder' && (
                  <p className="text-sm text-muted-foreground mt-2">
                    {selectedFiles.length}개 파일 선택됨
                  </p>
                )}
              </TabsContent>

              <TabsContent value="paste" className="mt-4">
                <PasteCode
                  onPaste={handlePaste}
                  languages={languages}
                  disabled={isSubmitting}
                />
              </TabsContent>
            </Tabs>

            {error && (
              <p className="text-sm text-destructive">{error}</p>
            )}
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose} disabled={isSubmitting}>
              취소
            </Button>
            <Button type="submit" disabled={isSubmitting || !isFormValid()}>
              {isSubmitting ? '생성 중...' : '태스크 만들기'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default CreateTaskModal
