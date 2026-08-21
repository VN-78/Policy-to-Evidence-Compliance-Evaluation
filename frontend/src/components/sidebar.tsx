import {
  FileText,
  Cpu,
  LayoutDashboard,
  History,
  HelpCircle,
  Plus,
  ShieldCheck,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

export type NavTab = "policies" | "scans" | "dashboard" | "audit-log"

interface SidebarProps {
  currentTab: NavTab
  onSelectTab: (tab: NavTab) => void
  onNewPolicyClick: () => void
}

export function Sidebar({ currentTab, onSelectTab, onNewPolicyClick }: SidebarProps) {
  const navItems = [
    {
      id: "policies" as NavTab,
      label: "Policies & Ingestion",
      icon: FileText,
      badge: "Step 1",
    },
    {
      id: "scans" as NavTab,
      label: "Scans & Evaluation",
      icon: Cpu,
      badge: "Step 2",
    },
    {
      id: "dashboard" as NavTab,
      label: "Overview Dashboard",
      icon: LayoutDashboard,
    },
    {
      id: "audit-log" as NavTab,
      label: "Audit Logs",
      icon: History,
    },
  ]

  return (
    <aside className="fixed left-0 top-0 z-30 hidden h-screen w-64 flex-col border-r border-border/80 bg-card p-4 transition-colors lg:flex">
      {/* Brand Header */}
      <div className="mb-6 flex items-center gap-3 px-2">
        <div className="flex size-9 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm shadow-primary/20">
          <ShieldCheck className="size-5" />
        </div>
        <div className="flex flex-col">
          <span className="font-heading text-sm font-bold tracking-tight text-foreground">
            Policy-to-Evidence
          </span>
          <span className="font-mono text-[10px] text-muted-foreground">
            Enterprise Audit v2.4
          </span>
        </div>
      </div>

      {/* Quick Action CTA */}
      <Button
        onClick={onNewPolicyClick}
        className="mb-6 w-full gap-2 rounded-xl text-xs font-semibold shadow-sm"
      >
        <Plus className="size-4" />
        New Policy Ingestion
      </Button>

      {/* Main Navigation List */}
      <nav className="flex-1 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = currentTab === item.id

          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onSelectTab(item.id)}
              className={cn(
                "flex w-full items-center justify-between rounded-xl px-3 py-2.5 text-xs font-medium transition-all text-left select-none",
                isActive
                  ? "bg-primary text-primary-foreground font-semibold shadow-sm"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <div className="flex items-center gap-3">
                <Icon className="size-4 shrink-0" />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span
                  className={cn(
                    "rounded px-1.5 py-0.5 text-[10px] font-mono",
                    isActive
                      ? "bg-primary-foreground/20 text-primary-foreground"
                      : "bg-muted text-muted-foreground"
                  )}
                >
                  {item.badge}
                </span>
              )}
            </button>
          )
        })}
      </nav>

      {/* Footer Navigation */}
      <div className="border-t border-border/60 pt-4 space-y-1">
        <a
          href="https://policy-to-evidence-compliance-evaluation.onrender.com/docs"
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-3 rounded-xl px-3 py-2 text-xs font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
        >
          <HelpCircle className="size-4 shrink-0" />
          <span>API Swagger Docs</span>
        </a>
      </div>
    </aside>
  )
}
