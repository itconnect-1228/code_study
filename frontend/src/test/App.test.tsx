import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import App from '../App'

const renderWithRouter = (initialRoute: string) => {
  return render(
    <MemoryRouter initialEntries={[initialRoute]}>
      <App />
    </MemoryRouter>
  )
}

describe('App Router', () => {
  it('renders Dashboard at /', () => {
    renderWithRouter('/')
    expect(screen.getByRole('heading', { name: /대시보드/i })).toBeInTheDocument()
  })

  it('renders Register page at /register', () => {
    renderWithRouter('/register')
    expect(screen.getByRole('heading', { name: /회원가입/i })).toBeInTheDocument()
  })

  it('renders Login page at /login', () => {
    renderWithRouter('/login')
    expect(screen.getByRole('heading', { name: /로그인/i })).toBeInTheDocument()
  })

  it('renders ProjectDetail page at /projects/:id', () => {
    renderWithRouter('/projects/123')
    expect(screen.getByRole('heading', { name: /프로젝트 상세/i })).toBeInTheDocument()
    expect(screen.getByText(/프로젝트 ID: 123/i)).toBeInTheDocument()
  })

  it('renders TaskDetail page at /tasks/:id', () => {
    renderWithRouter('/tasks/456')
    expect(screen.getByRole('heading', { name: /태스크 상세/i })).toBeInTheDocument()
    expect(screen.getByText(/태스크 ID: 456/i)).toBeInTheDocument()
  })

  it('renders Trash page at /trash', () => {
    renderWithRouter('/trash')
    expect(screen.getByRole('heading', { name: /휴지통/i })).toBeInTheDocument()
  })

  it('renders NotFound page for unknown routes', () => {
    renderWithRouter('/unknown-route')
    expect(screen.getByRole('heading', { name: /404/i })).toBeInTheDocument()
  })

  it('NotFound page has link to dashboard', () => {
    renderWithRouter('/unknown-route')
    expect(screen.getByRole('link', { name: /대시보드로 돌아가기/i })).toHaveAttribute('href', '/')
  })
})
