import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { FolderUpload } from './FolderUpload'

// Mock file with webkitRelativePath
const createMockFile = (name: string, path: string, content: string = 'test') => {
  const file = new File([content], name, { type: 'text/plain' })
  Object.defineProperty(file, 'webkitRelativePath', {
    value: path,
    writable: false,
  })
  return file
}

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

  // Add numeric index access
  files.forEach((file, index) => {
    Object.defineProperty(fileList, index, {
      value: file,
      enumerable: true,
    })
  })

  return fileList
}

describe('FolderUpload', () => {
  const mockOnFolderSelect = vi.fn()

  beforeEach(() => {
    mockOnFolderSelect.mockClear()
  })

  describe('rendering', () => {
    it('renders folder upload area', () => {
      render(<FolderUpload onFolderSelect={mockOnFolderSelect} />)
      expect(screen.getByText(/폴더를 드래그/i)).toBeInTheDocument()
    })

    it('renders folder picker button', () => {
      render(<FolderUpload onFolderSelect={mockOnFolderSelect} />)
      expect(screen.getByRole('button', { name: /폴더 선택/i })).toBeInTheDocument()
    })

    it('renders hidden folder input with webkitdirectory attribute', () => {
      render(<FolderUpload onFolderSelect={mockOnFolderSelect} />)
      const folderInput = document.querySelector('input[type="file"]') as HTMLInputElement
      expect(folderInput).toBeInTheDocument()
      expect(folderInput).toHaveAttribute('webkitdirectory')
    })
  })

  describe('folder picker', () => {
    it('opens folder picker when button is clicked', async () => {
      const user = userEvent.setup()
      render(<FolderUpload onFolderSelect={mockOnFolderSelect} />)
      const folderInput = document.querySelector('input[type="file"]') as HTMLInputElement
      const clickSpy = vi.spyOn(folderInput, 'click')
      const button = screen.getByRole('button', { name: /폴더 선택/i })
      await user.click(button)
      expect(clickSpy).toHaveBeenCalled()
    })

    it('calls onFolderSelect with files preserving directory structure', async () => {
      render(<FolderUpload onFolderSelect={mockOnFolderSelect} />)

      const files = [
        createMockFile('index.ts', 'src/index.ts'),
        createMockFile('App.tsx', 'src/App.tsx'),
        createMockFile('utils.ts', 'src/utils/utils.ts'),
      ]

      const folderInput = document.querySelector('input[type="file"]') as HTMLInputElement
      const mockFileList = createMockFileList(files)

      Object.defineProperty(folderInput, 'files', {
        value: mockFileList,
        configurable: true,
      })

      fireEvent.change(folderInput)

      await waitFor(() => {
        expect(mockOnFolderSelect).toHaveBeenCalledWith(
          expect.arrayContaining([
            expect.objectContaining({ name: 'index.ts' }),
            expect.objectContaining({ name: 'App.tsx' }),
            expect.objectContaining({ name: 'utils.ts' }),
          ])
        )
      })
    })
  })

  describe('drag and drop', () => {
    it('shows drag-over state when folder is dragged over', () => {
      render(<FolderUpload onFolderSelect={mockOnFolderSelect} />)
      const dropZone = screen.getByTestId('folder-drop-zone')
      fireEvent.dragEnter(dropZone, { dataTransfer: { types: ['Files'] } })
      expect(dropZone).toHaveClass('border-primary')
    })

    it('removes drag-over state when folder leaves', () => {
      render(<FolderUpload onFolderSelect={mockOnFolderSelect} />)
      const dropZone = screen.getByTestId('folder-drop-zone')
      fireEvent.dragEnter(dropZone, { dataTransfer: { types: ['Files'] } })
      fireEvent.dragLeave(dropZone)
      expect(dropZone).not.toHaveClass('border-primary')
    })

    it('calls onFolderSelect when files are dropped', async () => {
      render(<FolderUpload onFolderSelect={mockOnFolderSelect} />)

      const file = createMockFile('test.ts', 'folder/test.ts')
      const dropZone = screen.getByTestId('folder-drop-zone')

      fireEvent.drop(dropZone, {
        dataTransfer: {
          files: [file],
          types: ['Files'],
        },
      })

      await waitFor(() => {
        expect(mockOnFolderSelect).toHaveBeenCalledWith([file])
      })
    })
  })

  describe('file count validation', () => {
    it('rejects folders exceeding maxFiles', async () => {
      const onError = vi.fn()
      render(
        <FolderUpload
          onFolderSelect={mockOnFolderSelect}
          maxFiles={2}
          onError={onError}
        />
      )

      const files = [
        createMockFile('file1.ts', 'folder/file1.ts'),
        createMockFile('file2.ts', 'folder/file2.ts'),
        createMockFile('file3.ts', 'folder/file3.ts'),
      ]

      const folderInput = document.querySelector('input[type="file"]') as HTMLInputElement
      const mockFileList = createMockFileList(files)

      Object.defineProperty(folderInput, 'files', {
        value: mockFileList,
        configurable: true,
      })

      fireEvent.change(folderInput)

      await waitFor(() => {
        expect(onError).toHaveBeenCalledWith(expect.stringContaining('파일'))
        expect(mockOnFolderSelect).not.toHaveBeenCalled()
      })
    })

    it('accepts folders within maxFiles limit', async () => {
      render(
        <FolderUpload
          onFolderSelect={mockOnFolderSelect}
          maxFiles={5}
        />
      )

      const files = [
        createMockFile('file1.ts', 'folder/file1.ts'),
        createMockFile('file2.ts', 'folder/file2.ts'),
      ]

      const folderInput = document.querySelector('input[type="file"]') as HTMLInputElement
      const mockFileList = createMockFileList(files)

      Object.defineProperty(folderInput, 'files', {
        value: mockFileList,
        configurable: true,
      })

      fireEvent.change(folderInput)

      await waitFor(() => {
        expect(mockOnFolderSelect).toHaveBeenCalled()
      })
    })
  })

  describe('disabled state', () => {
    it('disables folder selection when disabled prop is true', () => {
      render(<FolderUpload onFolderSelect={mockOnFolderSelect} disabled />)
      const button = screen.getByRole('button', { name: /폴더 선택/i })
      expect(button).toBeDisabled()
    })

    it('ignores drag and drop when disabled', async () => {
      render(<FolderUpload onFolderSelect={mockOnFolderSelect} disabled />)

      const file = createMockFile('test.ts', 'folder/test.ts')
      const dropZone = screen.getByTestId('folder-drop-zone')

      fireEvent.drop(dropZone, {
        dataTransfer: {
          files: [file],
          types: ['Files'],
        },
      })

      await waitFor(() => {
        expect(mockOnFolderSelect).not.toHaveBeenCalled()
      })
    })
  })
})
