import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ProjectCard } from "@/components/project/ProjectCard";
import { CreateProjectModal } from "@/components/project/CreateProjectModal";
import { projectService } from "@/services/project-service";
import { useAuthStore } from "@/stores/auth-store";

/**
 * Dashboard - main page showing user's projects
 *
 * Features:
 * - List of all user projects
 * - Create new project button
 * - Empty state when no projects exist
 */
export default function Dashboard() {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const queryClient = useQueryClient();
  const { user } = useAuthStore();

  // Fetch projects
  const { data, isLoading, error } = useQuery({
    queryKey: ["projects"],
    queryFn: () => projectService.getProjects(),
  });

  // Create project mutation
  const createMutation = useMutation({
    mutationFn: ({
      title,
      description,
    }: {
      title: string;
      description?: string;
    }) => projectService.createProject(title, description),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });

  const handleCreateProject = async (title: string, description?: string) => {
    await createMutation.mutateAsync({ title, description });
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-8">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-10 w-40" />
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <Skeleton key={i} className="h-48 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center py-12">
          <h2 className="text-xl font-semibold text-destructive mb-2">
            프로젝트를 불러오는 데 실패했습니다
          </h2>
          <p className="text-muted-foreground mb-4">
            잠시 후 다시 시도해주세요.
          </p>
          <Button
            onClick={() =>
              queryClient.invalidateQueries({ queryKey: ["projects"] })
            }
          >
            다시 시도
          </Button>
        </div>
      </div>
    );
  }

  const projects = data?.projects ?? [];

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold">내 프로젝트</h1>
          {user && (
            <p className="text-muted-foreground mt-1">
              안녕하세요, {user.email}님
            </p>
          )}
        </div>
        <Button onClick={() => setIsCreateModalOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />새 프로젝트
        </Button>
      </div>

      {/* Project List */}
      {projects.length === 0 ? (
        // Empty state
        <div className="text-center py-12 border rounded-lg bg-muted/20">
          <h2 className="text-xl font-semibold mb-2">
            아직 프로젝트가 없습니다
          </h2>
          <p className="text-muted-foreground mb-4">
            첫 번째 프로젝트를 만들어 코드 학습을 시작해보세요!
          </p>
          <Button onClick={() => setIsCreateModalOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />첫 프로젝트 만들기
          </Button>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </div>
      )}

      {/* Stats */}
      {projects.length > 0 && (
        <div className="mt-8 text-center text-muted-foreground">
          총 {data?.total ?? 0}개의 프로젝트
        </div>
      )}

      {/* Create Project Modal */}
      <CreateProjectModal
        open={isCreateModalOpen}
        onOpenChange={setIsCreateModalOpen}
        onSubmit={handleCreateProject}
      />
    </div>
  );
}
