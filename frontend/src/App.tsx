import { Routes, Route } from 'react-router-dom'
import Register from './pages/Register'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import ProjectDetail from './pages/ProjectDetail'
import TaskDetail from './pages/TaskDetail'
import Trash from './pages/Trash'
import NotFound from './pages/NotFound'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/register" element={<Register />} />
      <Route path="/login" element={<Login />} />
      <Route path="/projects/:id" element={<ProjectDetail />} />
      <Route path="/tasks/:id" element={<TaskDetail />} />
      <Route path="/trash" element={<Trash />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}

export default App
