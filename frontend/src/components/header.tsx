import { ShieldCheck, Activity, FileText, Cpu } from "lucide-react"
import { ThemeToggle } from "@/components/theme-toggle"
import { Button } from "@/components/ui/button"
import type { NavTab } from "@/components/sidebar"
import { cn } from "@/lib/utils"

interface HeaderProps {
  currentTab: NavTab
  onSelectTab: (tab: NavTab) => void
}

export function Header({ currentTab, onSelectTab }: HeaderProps) {
  return (
    <header className="sticky top-0 z-20 w-full border-b border-border/60 bg-background/85 backdrop-blur-md transition-colors">
      <div className="flex h-16 items-center justify-between px-4 sm:px-8">
        {/* Brand / Logo (Mobile only or Subtitle) */}
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3 lg:hidden">
            <div className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <ShieldCheck className="size-4" />
            </div>
            <span className="font-heading text-sm font-bold tracking-tight text-foreground">
              Policy-to-Evidence
            </span>
          </div>

          {/* Top Navigation Tabs */}
          <nav className="flex items-center gap-1 sm:gap-2">
            <button
              type="button"
              onClick={() => onSelectTab("policies")}
              className={cn(
                "flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-semibold transition-all",
                currentTab === "policies"
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <FileText className="size-3.5" />
              <span>Policies</span>
            </button>

            <button
              type="button"
              onClick={() => onSelectTab("scans")}
              className={cn(
                "flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-semibold transition-all",
                currentTab === "scans"
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <Cpu className="size-3.5" />
              <span>Scans & Audits</span>
            </button>
          </nav>
        </div>

        {/* Right Section: Status Badge, Docs Link, Theme Toggle */}
        <div className="flex items-center gap-3 sm:gap-4">
          {/* Backend Status Pill */}
          <div
            className="flex items-center gap-2 rounded-full border border-border/80 bg-muted/40 px-3 py-1 text-xs font-medium text-foreground transition-colors"
            title="Backend API: https://policy-to-evidence-compliance-evaluation.onrender.com"
          >
            <span className="relative flex size-2">
              <span className="absolute inline-flex size-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex size-2 rounded-full bg-emerald-500"></span>
            </span>
            <span className="hidden sm:inline text-muted-foreground">API:</span>
            <span className="font-semibold text-emerald-600 dark:text-emerald-400">Live</span>
          </div>

          {/* API Docs Button */}
          <Button
            variant="outline"
            size="sm"
            asChild
            className="hidden sm:inline-flex rounded-full text-xs font-medium"
          >
            <a
              href="https://policy-to-evidence-compliance-evaluation.onrender.com/docs"
              target="_blank"
              rel="noreferrer"
            >
              <Activity className="size-3.5" />
              API Docs
            </a>
          </Button>

          <div className="h-4 w-px bg-border"></div>

          {/* Theme Toggle */}
          <ThemeToggle />
        </div>
      </div>
    </header>
  )
}
