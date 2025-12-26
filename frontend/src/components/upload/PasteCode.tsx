import { useState, useCallback } from 'react'
import { Code } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

export interface PasteCodeData {
  code: string
  language: string
}

export interface PasteCodeProps {
  onPaste: (data: PasteCodeData) => void
  languages: string[]
  defaultLanguage?: string
  disabled?: boolean
}

/**
 * PasteCode - Code paste component with language selector
 *
 * Features:
 * - Textarea for code input
 * - Language selection dropdown
 * - Submit button with validation
 */
export function PasteCode({
  onPaste,
  languages,
  defaultLanguage,
  disabled = false,
}: PasteCodeProps) {
  const [code, setCode] = useState('')
  const [language, setLanguage] = useState(defaultLanguage || languages[0] || '')

  const handleSubmit = useCallback(() => {
    if (!code.trim()) return

    onPaste({
      code: code.trim(),
      language,
    })

    // Clear the textarea after successful submit
    setCode('')
  }, [code, language, onPaste])

  const isSubmitDisabled = disabled || !code.trim()

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-muted-foreground">
        <Code className="h-5 w-5" />
        <span className="text-sm font-medium">코드 붙여넣기</span>
      </div>

      <div className="space-y-3">
        <div className="flex gap-2">
          <Select
            value={language}
            onValueChange={setLanguage}
            disabled={disabled}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="언어 선택" />
            </SelectTrigger>
            <SelectContent>
              {languages.map((lang) => (
                <SelectItem key={lang} value={lang}>
                  {lang.charAt(0).toUpperCase() + lang.slice(1)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <Textarea
          placeholder="코드를 붙여넣기하세요..."
          value={code}
          onChange={(e) => setCode(e.target.value)}
          disabled={disabled}
          className="min-h-[200px] font-mono text-sm"
        />

        <div className="flex justify-end">
          <Button
            onClick={handleSubmit}
            disabled={isSubmitDisabled}
          >
            코드 추가
          </Button>
        </div>
      </div>
    </div>
  )
}

export default PasteCode
