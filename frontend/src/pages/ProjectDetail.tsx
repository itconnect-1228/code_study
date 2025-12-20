import { useParams } from 'react-router-dom'

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>()

  return (
    <div>
      <h1>프로젝트 상세</h1>
      <p>프로젝트 ID: {id}</p>
      <p>Phase 4에서 구현될 예정입니다.</p>
    </div>
  )
}
