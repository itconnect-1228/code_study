import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { Chapter1Summary } from './Chapter1'
import type { DocumentChapters } from '@/services/document-service'

describe('Chapter1Summary', () => {
  const sampleChapter: DocumentChapters['summary'] = {
    title: '코드 요약',
    content: '이 코드는 간단한 Hello World 프로그램입니다. 함수를 정의하고 호출하는 기본적인 JavaScript 패턴을 보여줍니다.',
  }

  describe('렌더링', () => {
    it('챕터 타이틀이 렌더링되어야 함', () => {
      render(<Chapter1Summary data={sampleChapter} />)

      expect(screen.getByRole('heading', { name: /코드 요약/i })).toBeInTheDocument()
    })

    it('챕터 콘텐츠가 렌더링되어야 함', () => {
      render(<Chapter1Summary data={sampleChapter} />)

      expect(screen.getByText(/Hello World 프로그램/)).toBeInTheDocument()
    })

    it('여러 단락의 콘텐츠를 처리할 수 있어야 함', () => {
      const multiParagraph = {
        ...sampleChapter,
        content: '첫 번째 단락입니다.\n\n두 번째 단락입니다.',
      }
      render(<Chapter1Summary data={multiParagraph} />)

      expect(screen.getByText(/첫 번째 단락/)).toBeInTheDocument()
    })
  })

  describe('스타일링', () => {
    it('컨테이너에 기본 클래스가 적용되어야 함', () => {
      const { container } = render(<Chapter1Summary data={sampleChapter} />)

      const chapter = container.firstChild
      expect(chapter).toHaveClass('chapter-summary')
    })

    it('커스텀 className을 적용할 수 있어야 함', () => {
      const { container } = render(
        <Chapter1Summary data={sampleChapter} className="custom-class" />
      )

      const chapter = container.firstChild
      expect(chapter).toHaveClass('custom-class')
    })
  })

  describe('빈 콘텐츠 처리', () => {
    it('빈 콘텐츠를 처리할 수 있어야 함', () => {
      const emptyContent = { ...sampleChapter, content: '' }
      render(<Chapter1Summary data={emptyContent} />)

      expect(screen.getByRole('heading', { name: /코드 요약/i })).toBeInTheDocument()
    })
  })

  describe('마크다운 렌더링', () => {
    it('코드 블록이 있는 콘텐츠를 렌더링해야 함', () => {
      const withCode = {
        ...sampleChapter,
        content: '다음 코드를 사용합니다: `console.log()`',
      }
      render(<Chapter1Summary data={withCode} />)

      expect(screen.getByText(/console.log/)).toBeInTheDocument()
    })
  })
})
