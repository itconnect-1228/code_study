import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'
import { Chapter4LineByLine } from './Chapter4'
import type { DocumentChapters } from '@/services/document-service'

describe('Chapter4LineByLine', () => {
  const sampleChapter: DocumentChapters['lineByLine'] = {
    title: '라인별 설명',
    explanations: [
      {
        lineNumber: 1,
        code: 'function hello() {',
        explanation: '함수를 선언합니다. "hello"라는 이름을 가진 함수를 정의하기 시작합니다.',
      },
      {
        lineNumber: 2,
        code: '  console.log("Hello, World!");',
        explanation: '콘솔에 "Hello, World!"라는 메시지를 출력합니다.',
      },
      {
        lineNumber: 3,
        code: '}',
        explanation: '함수 블록을 종료합니다.',
      },
      {
        lineNumber: 5,
        code: 'hello();',
        explanation: '위에서 정의한 hello 함수를 호출합니다. 이때 콘솔에 메시지가 출력됩니다.',
      },
    ],
  }

  describe('렌더링', () => {
    it('챕터 타이틀이 렌더링되어야 함', () => {
      render(<Chapter4LineByLine data={sampleChapter} />)

      expect(screen.getByRole('heading', { name: /라인별 설명/i })).toBeInTheDocument()
    })

    it('모든 라인 설명이 렌더링되어야 함', () => {
      render(<Chapter4LineByLine data={sampleChapter} />)

      expect(screen.getByText(/function hello/)).toBeInTheDocument()
      expect(screen.getByText(/console.log/)).toBeInTheDocument()
      expect(screen.getByText(/hello\(\);/)).toBeInTheDocument()
    })

    it('각 라인의 설명이 표시되어야 함', () => {
      render(<Chapter4LineByLine data={sampleChapter} />)

      expect(screen.getByText(/함수를 선언합니다/)).toBeInTheDocument()
      expect(screen.getByText(/콘솔에 "Hello, World!"라는 메시지/)).toBeInTheDocument()
    })

    it('라인 번호가 표시되어야 함', () => {
      render(<Chapter4LineByLine data={sampleChapter} />)

      expect(screen.getByText('1')).toBeInTheDocument()
      expect(screen.getByText('2')).toBeInTheDocument()
      expect(screen.getByText('3')).toBeInTheDocument()
      expect(screen.getByText('5')).toBeInTheDocument()
    })
  })

  describe('라인 선택 기능', () => {
    it('라인을 클릭하면 onLineSelect 콜백이 호출되어야 함', async () => {
      const user = userEvent.setup()
      const onLineSelect = vi.fn()
      render(<Chapter4LineByLine data={sampleChapter} onLineSelect={onLineSelect} />)

      const firstLine = screen.getByTestId('line-item-1')
      await user.click(firstLine)

      expect(onLineSelect).toHaveBeenCalledWith(1)
    })

    it('선택된 라인이 하이라이트되어야 함', () => {
      render(<Chapter4LineByLine data={sampleChapter} selectedLine={2} />)

      const selectedLine = screen.getByTestId('line-item-2')
      expect(selectedLine).toHaveAttribute('data-selected', 'true')
    })

    it('선택되지 않은 라인은 하이라이트되지 않아야 함', () => {
      render(<Chapter4LineByLine data={sampleChapter} selectedLine={2} />)

      const unselectedLine = screen.getByTestId('line-item-1')
      expect(unselectedLine).toHaveAttribute('data-selected', 'false')
    })
  })

  describe('스타일링', () => {
    it('컨테이너에 기본 클래스가 적용되어야 함', () => {
      const { container } = render(<Chapter4LineByLine data={sampleChapter} />)

      const chapter = container.firstChild
      expect(chapter).toHaveClass('chapter-line-by-line')
    })

    it('커스텀 className을 적용할 수 있어야 함', () => {
      const { container } = render(
        <Chapter4LineByLine data={sampleChapter} className="custom-class" />
      )

      const chapter = container.firstChild
      expect(chapter).toHaveClass('custom-class')
    })

    it('코드가 모노스페이스 폰트로 표시되어야 함', () => {
      render(<Chapter4LineByLine data={sampleChapter} />)

      const codeElement = screen.getByText(/function hello/).closest('code')
      expect(codeElement).toHaveClass('font-mono')
    })
  })

  describe('빈 설명 처리', () => {
    it('설명이 없을 때 적절한 메시지를 표시해야 함', () => {
      const emptyChapter = { ...sampleChapter, explanations: [] }
      render(<Chapter4LineByLine data={emptyChapter} />)

      expect(screen.getByText(/라인별 설명이 없습니다/i)).toBeInTheDocument()
    })
  })

  describe('접근성', () => {
    it('각 라인 항목이 접근 가능한 버튼으로 렌더링되어야 함', () => {
      render(<Chapter4LineByLine data={sampleChapter} onLineSelect={vi.fn()} />)

      const buttons = screen.getAllByRole('button')
      expect(buttons.length).toBeGreaterThanOrEqual(4)
    })
  })
})
