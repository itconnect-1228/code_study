import { useParams } from 'react-router-dom'

export default function TaskDetail() {
  const { id } = useParams<{ id: string }>()

  return (
    <div>
      <h1>태스크 상세</h1>
      <p>태스크 ID: {id}</p>
      <p>Phase 5에서 구현될 예정입니다.</p>
    </div>
  )
}
