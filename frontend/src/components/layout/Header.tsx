import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  LogOut,
  Trash2,
  LayoutDashboard,
  User,
  ChevronDown,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@/hooks/useAuth";

/**
 * Header - Main navigation header with user menu
 *
 * Features:
 * - Logo/title linking to dashboard
 * - Navigation links (Dashboard, Trash)
 * - User dropdown with email and logout
 */
export default function Header() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  const isActive = (path: string) => location.pathname === path;

  return (
    <header className="border-b bg-background">
      <div className="container mx-auto flex h-14 items-center justify-between px-4">
        {/* Logo */}
        <Link to="/dashboard" className="flex items-center gap-2">
          <span className="text-lg font-bold">AI 코드 학습</span>
        </Link>

        {/* Navigation */}
        <nav className="flex items-center gap-1">
          <Button
            variant={
              isActive("/dashboard") || isActive("/") ? "secondary" : "ghost"
            }
            size="sm"
            asChild
          >
            <Link to="/dashboard">
              <LayoutDashboard className="mr-2 h-4 w-4" />
              대시보드
            </Link>
          </Button>
          <Button
            variant={isActive("/trash") ? "secondary" : "ghost"}
            size="sm"
            asChild
          >
            <Link to="/trash">
              <Trash2 className="mr-2 h-4 w-4" />
              휴지통
            </Link>
          </Button>
        </nav>

        {/* User Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm" className="gap-2">
              <User className="h-4 w-4" />
              <span className="hidden sm:inline">{user?.email}</span>
              <ChevronDown className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel>
              <div className="flex flex-col gap-1">
                <span className="text-sm font-medium">내 계정</span>
                <span className="text-xs text-muted-foreground">
                  {user?.email}
                </span>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleLogout} variant="destructive">
              <LogOut className="mr-2 h-4 w-4" />
              로그아웃
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
