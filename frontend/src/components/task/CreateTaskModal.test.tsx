import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { CreateTaskModal, type CreateTaskModalProps } from './CreateTaskModal'

// Mock pointer capture methods for Radix UI
beforeEach(() => {
  Element.prototype.hasPointerCapture = vi.fn(() => false)
  Element.prototype.setPointerCapture = vi.fn()
  Element.prototype.releasePointerCapture = vi.fn()
})

// Create a mock FileList from an array of files
const createMockFileList = (files: File[]): FileList => {
  const fileList = {
    length: files.length,
    item: (index: number) => files[index] || null,
    [Symbol.iterator]: function* () {
      for (let i = 0; i < files.length; i++) {
        yield files[i]
      }
    },
  } as FileList

  files.forEach((file, index) => {
    Object.defineProperty(fileList, index, {
      value: file,
      enumerable: true,
    })
  })

  return fileList
}

describe('CreateTaskModal', () => {
  const defaultProps: CreateTaskModalProps = {
    open: true,
    onOpenChange: vi.fn(),
    onSubmit: vi.fn(),
    languages: ['javascript', 'typescript', 'python', 'java'],
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('rendering', () => {
    it('renders modal when open is true', () => {
      render(<CreateTaskModal {...defaultProps} />)
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })

    it('renders modal title', () => {
      render(<CreateTaskModal {...defaultProps} />)
      expect(screen.getByText(/새 태스크 만들기/i)).toBeInTheDocument()
    })

    it('renders title input field', () => {
      render(<CreateTaskModal {...defaultProps} />)
      expect(screen.getByLabelText(/태스크 제목/i)).toBeInTheDocument()
    })

    it('renders three upload method tabs', () => {
      render(<CreateTaskModal {...defaultProps} />)
      expect(screen.getByRole('tab', { name: /파일/i })).toBeInTheDocument()
      expect(screen.getByRole('tab', { name: /폴더/i })).toBeInTheDocument()
      expect(screen.getByRole('tab', { name: /붙여넣기/i })).toBeInTheDocument()
    })

    it('renders submit and cancel buttons', () => {
      render(<CreateTaskModal {...defaultProps} />)
      expect(screen.getByRole('button', { name: /취소/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /태스크 만들기/i })).toBeInTheDocument()
    })
  })

  describe('tabs navigation', () => {
    it('shows file upload content by default', () => {
      render(<CreateTaskModal {...defaultProps} />)
      expect(screen.getByTestId('file-drop-zone')).toBeInTheDocument()
    })

    it('switches to folder upload when folder tab clicked', async () => {
      const user = userEvent.setup()
      render(<CreateTaskModal {...defaultProps} />)

      await user.click(screen.getByRole('tab', { name: /폴더/i }))

      expect(screen.getByTestId('folder-drop-zone')).toBeInTheDocument()
    })

    it('switches to paste code when paste tab clicked', async () => {
      const user = userEvent.setup()
      render(<CreateTaskModal {...defaultProps} />)

      await user.click(screen.getByRole('tab', { name: /붙여넣기/i }))

      // Should show the code textarea (identifiable by placeholder)
      expect(screen.getByPlaceholderText(/코드를 붙여넣기/i)).toBeInTheDocument()
    })
  })

  describe('title input', () => {
    it('allows typing title', async () => {
      const user = userEvent.setup()
      render(<CreateTaskModal {...defaultProps} />)

      const titleInput = screen.getByLabelText(/태스크 제목/i)
      await user.type(titleInput, 'My Task Title')

      expect(titleInput).toHaveValue('My Task Title')
    })

    it('shows error when title is empty on submit', async () => {
      const user = userEvent.setup()
      render(<CreateTaskModal {...defaultProps} />)

      // Add a file to enable submit
      const dropZone = screen.getByTestId('file-drop-zone')
      const file = new File(['test'], 'test.js', { type: 'text/javascript' })
      fireEvent.drop(dropZone, {
        dataTransfer: {
          files: [file],
          types: ['Files'],
        },
      })

      await waitFor(() => {
        expect(screen.getByText(/1개 파일/i)).toBeInTheDocument()
      })

      // Button is still disabled because title is empty
      const submitButton = screen.getByRole('button', { name: /태스크 만들기/i })
      expect(submitButton).toBeDisabled()
    })
  })

  describe('file upload', () => {
    it('disables submit button when no files selected', () => {
      render(<CreateTaskModal {...defaultProps} />)
      const submitButton = screen.getByRole('button', { name: /태스크 만들기/i })
      expect(submitButton).toBeDisabled()
    })

    it('shows selected file count after file drop', async () => {
      render(<CreateTaskModal {...defaultProps} />)

      const dropZone = screen.getByTestId('file-drop-zone')
      const files = [
        new File(['test1'], 'file1.js', { type: 'text/javascript' }),
        new File(['test2'], 'file2.js', { type: 'text/javascript' }),
      ]

      fireEvent.drop(dropZone, {
        dataTransfer: {
          files,
          types: ['Files'],
        },
      })

      await waitFor(() => {
        expect(screen.getByText(/2개 파일/i)).toBeInTheDocument()
      })
    })

    it('enables submit button when files are selected and title provided', async () => {
      const user = userEvent.setup()
      render(<CreateTaskModal {...defaultProps} />)

      const titleInput = screen.getByLabelText(/태스크 제목/i)
      await user.type(titleInput, 'My Task')

      const dropZone = screen.getByTestId('file-drop-zone')
      const file = new File(['test'], 'test.js', { type: 'text/javascript' })
      fireEvent.drop(dropZone, {
        dataTransfer: {
          files: [file],
          types: ['Files'],
        },
      })

      await waitFor(() => {
        const submitButton = screen.getByRole('button', { name: /태스크 만들기/i })
        expect(submitButton).not.toBeDisabled()
      })
    })
  })

  describe('folder upload', () => {
    it('shows folder drop zone when folder tab is selected', async () => {
      const user = userEvent.setup()
      render(<CreateTaskModal {...defaultProps} />)

      await user.click(screen.getByRole('tab', { name: /폴더/i }))

      expect(screen.getByTestId('folder-drop-zone')).toBeInTheDocument()
    })
  })

  describe('paste code', () => {
    it('shows code textarea and language selector when paste tab selected', async () => {
      const user = userEvent.setup()
      render(<CreateTaskModal {...defaultProps} />)

      await user.click(screen.getByRole('tab', { name: /붙여넣기/i }))

      expect(screen.getByPlaceholderText(/코드를 붙여넣기/i)).toBeInTheDocument()
      expect(screen.getByRole('combobox')).toBeInTheDocument()
    })

    it('enables submit when title and code are provided', async () => {
      const user = userEvent.setup()
      render(<CreateTaskModal {...defaultProps} />)

      await user.click(screen.getByRole('tab', { name: /붙여넣기/i }))

      const titleInput = screen.getByLabelText(/태스크 제목/i)
      await user.type(titleInput, 'My Task')

      const codeInput = screen.getByPlaceholderText(/코드를 붙여넣기/i)
      await user.type(codeInput, 'console.log("hello")')

      // Click the "코드 추가" button to confirm the pasted code
      const addCodeButton = screen.getByRole('button', { name: /코드 추가/i })
      await user.click(addCodeButton)

      await waitFor(() => {
        const submitButton = screen.getByRole('button', { name: /태스크 만들기/i })
        expect(submitButton).not.toBeDisabled()
      })
    })
  })

  describe('form submission', () => {
    it('calls onSubmit with file upload data', async () => {
      const mockOnSubmit = vi.fn().mockResolvedValue(undefined)
      const user = userEvent.setup()
      render(<CreateTaskModal {...defaultProps} onSubmit={mockOnSubmit} />)

      const titleInput = screen.getByLabelText(/태스크 제목/i)
      await user.type(titleInput, 'My Task')

      const dropZone = screen.getByTestId('file-drop-zone')
      const file = new File(['test'], 'test.js', { type: 'text/javascript' })
      fireEvent.drop(dropZone, {
        dataTransfer: {
          files: [file],
          types: ['Files'],
        },
      })

      await waitFor(() => {
        expect(screen.getByText(/1개 파일/i)).toBeInTheDocument()
      })

      const submitButton = screen.getByRole('button', { name: /태스크 만들기/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith({
          title: 'My Task',
          uploadType: 'file',
          files: expect.arrayContaining([expect.any(File)]),
        })
      })
    })

    it('calls onSubmit with paste code data', async () => {
      const mockOnSubmit = vi.fn().mockResolvedValue(undefined)
      const user = userEvent.setup()
      render(<CreateTaskModal {...defaultProps} onSubmit={mockOnSubmit} />)

      const titleInput = screen.getByLabelText(/태스크 제목/i)
      await user.type(titleInput, 'Paste Task')

      await user.click(screen.getByRole('tab', { name: /붙여넣기/i }))

      const codeInput = screen.getByPlaceholderText(/코드를 붙여넣기/i)
      await user.type(codeInput, 'const x = 1;')

      // Click "코드 추가" to confirm the paste
      const addCodeButton = screen.getByRole('button', { name: /코드 추가/i })
      await user.click(addCodeButton)

      const submitButton = screen.getByRole('button', { name: /태스크 만들기/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith({
          title: 'Paste Task',
          uploadType: 'paste',
          code: 'const x = 1;',
          language: 'javascript',
        })
      })
    })

    it('closes modal after successful submission', async () => {
      const mockOnSubmit = vi.fn().mockResolvedValue(undefined)
      const mockOnOpenChange = vi.fn()
      const user = userEvent.setup()

      render(
        <CreateTaskModal
          {...defaultProps}
          onSubmit={mockOnSubmit}
          onOpenChange={mockOnOpenChange}
        />
      )

      const titleInput = screen.getByLabelText(/태스크 제목/i)
      await user.type(titleInput, 'My Task')

      await user.click(screen.getByRole('tab', { name: /붙여넣기/i }))

      const codeInput = screen.getByPlaceholderText(/코드를 붙여넣기/i)
      await user.type(codeInput, 'test code')

      // Click "코드 추가" to confirm the paste
      const addCodeButton = screen.getByRole('button', { name: /코드 추가/i })
      await user.click(addCodeButton)

      const submitButton = screen.getByRole('button', { name: /태스크 만들기/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(mockOnOpenChange).toHaveBeenCalledWith(false)
      })
    })

    it('shows error message on submission failure', async () => {
      const mockOnSubmit = vi.fn().mockRejectedValue(new Error('Failed'))
      const user = userEvent.setup()

      render(<CreateTaskModal {...defaultProps} onSubmit={mockOnSubmit} />)

      const titleInput = screen.getByLabelText(/태스크 제목/i)
      await user.type(titleInput, 'My Task')

      await user.click(screen.getByRole('tab', { name: /붙여넣기/i }))

      const codeInput = screen.getByPlaceholderText(/코드를 붙여넣기/i)
      await user.type(codeInput, 'test code')

      // Click "코드 추가" to confirm the paste
      const addCodeButton = screen.getByRole('button', { name: /코드 추가/i })
      await user.click(addCodeButton)

      const submitButton = screen.getByRole('button', { name: /태스크 만들기/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/실패/i)).toBeInTheDocument()
      })
    })
  })

  describe('cancel behavior', () => {
    it('calls onOpenChange with false when cancel clicked', async () => {
      const mockOnOpenChange = vi.fn()
      const user = userEvent.setup()

      render(<CreateTaskModal {...defaultProps} onOpenChange={mockOnOpenChange} />)

      const cancelButton = screen.getByRole('button', { name: /취소/i })
      await user.click(cancelButton)

      expect(mockOnOpenChange).toHaveBeenCalledWith(false)
    })

    it('resets form state when closed', async () => {
      const mockOnOpenChange = vi.fn()
      const user = userEvent.setup()

      const { rerender } = render(
        <CreateTaskModal {...defaultProps} onOpenChange={mockOnOpenChange} />
      )

      const titleInput = screen.getByLabelText(/태스크 제목/i)
      await user.type(titleInput, 'Some Title')

      const cancelButton = screen.getByRole('button', { name: /취소/i })
      await user.click(cancelButton)

      // Reopen modal
      rerender(<CreateTaskModal {...defaultProps} open={true} onOpenChange={mockOnOpenChange} />)

      // Title should be reset
      const newTitleInput = screen.getByLabelText(/태스크 제목/i)
      expect(newTitleInput).toHaveValue('')
    })
  })

  describe('loading state', () => {
    it('disables submit button while submitting', async () => {
      const mockOnSubmit = vi.fn(() => new Promise(() => {})) // Never resolves
      const user = userEvent.setup()

      render(<CreateTaskModal {...defaultProps} onSubmit={mockOnSubmit} />)

      const titleInput = screen.getByLabelText(/태스크 제목/i)
      await user.type(titleInput, 'My Task')

      await user.click(screen.getByRole('tab', { name: /붙여넣기/i }))

      const codeInput = screen.getByPlaceholderText(/코드를 붙여넣기/i)
      await user.type(codeInput, 'test code')

      // Click "코드 추가" to confirm the paste
      const addCodeButton = screen.getByRole('button', { name: /코드 추가/i })
      await user.click(addCodeButton)

      const submitButton = screen.getByRole('button', { name: /태스크 만들기/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /생성 중/i })).toBeDisabled()
      })
    })
  })
})
