import { Link } from "react-router-dom";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { Project } from "@/services/project-service";

interface ProjectCardProps {
  project: Project;
}

/**
 * Format date to Korean locale string
 */
function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

/**
 * ProjectCard - displays a project summary card
 *
 * Shows project title, description, and metadata.
 * Links to the project detail page.
 */
export function ProjectCard({ project }: ProjectCardProps) {
  const isActive = project.deletionStatus === "active";

  return (
    <Link to={`/projects/${project.id}`} className="block">
      <Card className="transition-shadow hover:shadow-md cursor-pointer">
        <CardHeader>
          <div className="flex items-start justify-between">
            <CardTitle className="text-lg">{project.title}</CardTitle>
            {!isActive && (
              <Badge variant="secondary" className="ml-2">
                휴지통
              </Badge>
            )}
          </div>
          {project.description && (
            <CardDescription className="line-clamp-2">
              {project.description}
            </CardDescription>
          )}
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span>생성: {formatDate(project.createdAt)}</span>
            {project.lastActivityAt && (
              <span>마지막 활동: {formatDate(project.lastActivityAt)}</span>
            )}
          </div>
        </CardContent>
        <CardFooter className="text-xs text-muted-foreground">
          {/* Task count will be added in Phase 5 */}
        </CardFooter>
      </Card>
    </Link>
  );
}

export default ProjectCard;
