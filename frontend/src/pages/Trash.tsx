import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Trash2,
  AlertCircle,
  Loader2,
  Calendar,
  RotateCcw,
  X,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { projectService, type Project } from "@/services/project-service";
import { toast } from "sonner";

/**
 * 삭제된 프로젝트 카드 컴포넌트
 */
function TrashedProjectCard({
  project,
  onRestore,
  onPermanentDelete,
  isRestoring,
  isDeleting,
}: {
  project: Project;
  onRestore: (id: string) => void;
  onPermanentDelete: (id: string) => void;
  isRestoring: boolean;
  isDeleting: boolean;
}) {
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const trashedDate = project.trashedAt
    ? new Date(project.trashedAt).toLocaleDateString("ko-KR", {
        year: "numeric",
        month: "long",
        day: "numeric",
      })
    : "알 수 없음";

  const handlePermanentDelete = () => {
    onPermanentDelete(project.id);
    setIsDialogOpen(false);
  };

  return (
    <Card className="opacity-75 hover:opacity-100 transition-opacity">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-lg line-through text-muted-foreground flex-1 min-w-0">
            {project.title}
          </CardTitle>
          <div className="flex gap-1 shrink-0">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onRestore(project.id)}
              disabled={isRestoring || isDeleting}
            >
              {isRestoring ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <>
                  <RotateCcw className="h-4 w-4 mr-1" />
                  복구
                </>
              )}
            </Button>
            <AlertDialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
              <AlertDialogTrigger asChild>
                <Button
                  variant="destructive"
                  size="sm"
                  disabled={isRestoring || isDeleting}
                >
                  {isDeleting ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <X className="h-4 w-4" />
                  )}
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>프로젝트 영구 삭제</AlertDialogTitle>
                  <AlertDialogDescription>
                    "{project.title}" 프로젝트를 영구적으로 삭제하시겠습니까?
                    <br />
                    <strong className="text-destructive">
                      이 작업은 되돌릴 수 없습니다.
                    </strong>
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>취소</AlertDialogCancel>
                  <AlertDialogAction
                    onClick={handlePermanentDelete}
                    className="bg-destructive text-white hover:bg-destructive/90"
                  >
                    영구 삭제
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {project.description && (
          <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
            {project.description}
          </p>
        )}
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Calendar className="h-3 w-3" />
          <span>삭제일: {trashedDate}</span>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Trash - 휴지통 페이지
 *
 * 삭제된 프로젝트 목록을 표시합니다.
 * 삭제된 프로젝트는 30일 후 영구 삭제됩니다.
 */
export default function Trash() {
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ["projects", "trashed"],
    queryFn: () => projectService.getProjects(true),
  });

  const restoreMutation = useMutation({
    mutationFn: (projectId: string) => projectService.restoreProject(projectId),
    onSuccess: (restoredProject) => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      toast.success(`"${restoredProject.title}" 프로젝트가 복구되었습니다.`);
    },
    onError: () => {
      toast.error("프로젝트 복구에 실패했습니다.");
    },
  });

  const permanentDeleteMutation = useMutation({
    mutationFn: (projectId: string) =>
      projectService.permanentDeleteProject(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      toast.success("프로젝트가 영구적으로 삭제되었습니다.");
    },
    onError: () => {
      toast.error("프로젝트 삭제에 실패했습니다.");
    },
  });

  // 삭제된 프로젝트만 필터링
  const trashedProjects = data?.projects.filter(
    (project: Project) => project.deletionStatus === "trashed",
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          휴지통을 불러오는 중 오류가 발생했습니다.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Trash2 className="h-6 w-6" />
          휴지통
        </h1>
        <p className="text-muted-foreground mt-1">
          삭제된 프로젝트는 30일 후 영구 삭제됩니다.
        </p>
      </div>

      {/* 프로젝트 목록 */}
      {!trashedProjects || trashedProjects.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Trash2 className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground text-center">
              휴지통이 비어 있습니다.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {trashedProjects.map((project) => (
            <TrashedProjectCard
              key={project.id}
              project={project}
              onRestore={(id) => restoreMutation.mutate(id)}
              onPermanentDelete={(id) => permanentDeleteMutation.mutate(id)}
              isRestoring={
                restoreMutation.isPending &&
                restoreMutation.variables === project.id
              }
              isDeleting={
                permanentDeleteMutation.isPending &&
                permanentDeleteMutation.variables === project.id
              }
            />
          ))}
        </div>
      )}
    </div>
  );
}
