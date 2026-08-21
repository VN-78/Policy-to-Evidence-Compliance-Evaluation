import * as React from "react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { ThemeProvider } from "@/components/theme-provider"
import { Header } from "@/components/header"
import { Sidebar, type NavTab } from "@/components/sidebar"
import { PolicyIngestionView } from "@/components/features/policy-ingestion-view"
import { ComplianceScanView } from "@/components/features/compliance-scan-view"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { usePolicies } from "@/api/hooks"
import { ShieldCheck, FileText, Cpu, ArrowRight } from "lucide-react"

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
})

function DashboardOverview({ onNavigate }: { onNavigate: (tab: NavTab) => void }) {
  const { data: policies } = usePolicies()

  return (
    <div className="space-y-8">
      {/* Banner */}
      <div className="rounded-2xl border border-border/70 bg-card p-6 shadow-sm sm:p-8">
        <div className="flex flex-col gap-3">
          <div className="inline-flex w-fit items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
            <ShieldCheck className="size-3.5" />
            Automated Policy-as-Code Platform
          </div>
          <h2 className="font-heading text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
            Policy-to-Evidence Compliance Evaluation
          </h2>
          <p className="max-w-3xl text-sm leading-relaxed text-muted-foreground sm:text-base">
            Extract machine-evaluatable compliance rules from PDF documents with GenAI, persist
            canonical rules with SHA-256 deduplication, and deterministically audit live
            infrastructure telemetry evidence.
          </p>
        </div>
      </div>

      {/* Two-step quick flow cards */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {/* Step 1 Card */}
        <Card className="flex flex-col justify-between hover:border-primary/50 transition-all">
          <CardHeader>
            <div className="flex items-center justify-between mb-2">
              <div className="flex size-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
                <FileText className="size-5" />
              </div>
              <span className="rounded-md bg-muted px-2.5 py-1 font-mono text-xs font-semibold text-muted-foreground">
                Step 1
              </span>
            </div>
            <CardTitle className="text-lg">Policy Ingestion & Rule Extraction</CardTitle>
            <CardDescription>
              Upload multi-page compliance PDFs (SOC 2, ISO 27001) or paste raw text to parse atomic
              evaluatable rules with verbatim citations.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-2">
            <Button
              onClick={() => onNavigate("policies")}
              className="w-full gap-2 rounded-lg font-semibold"
            >
              Go to Policy Extraction
              <ArrowRight className="size-4" />
            </Button>
          </CardContent>
        </Card>

        {/* Step 2 Card */}
        <Card className="flex flex-col justify-between hover:border-primary/50 transition-all">
          <CardHeader>
            <div className="flex items-center justify-between mb-2">
              <div className="flex size-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
                <Cpu className="size-5" />
              </div>
              <span className="rounded-md bg-muted px-2.5 py-1 font-mono text-xs font-semibold text-muted-foreground">
                Step 2
              </span>
            </div>
            <CardTitle className="text-lg">Evidence Ingestion & Compliance Scan</CardTitle>
            <CardDescription>
              Feed raw AWS/Cloud telemetry JSON to execute deterministic mathematical evaluations and
              view plain-language audit verdicts.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-2">
            <Button
              variant="outline"
              onClick={() => onNavigate("scans")}
              className="w-full gap-2 rounded-lg font-semibold"
            >
              Open Scan Workspace
              <ArrowRight className="size-4" />
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Available Policies Overview */}
      {policies && policies.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Active Ingested Policies ({policies.length})</CardTitle>
            <CardDescription>Policies available for compliance scans in PostgreSQL</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="divide-y divide-border/60">
              {policies.map((p) => (
                <div
                  key={p.id}
                  className="flex items-center justify-between py-3 hover:bg-muted/30 px-2 rounded-lg transition-colors cursor-pointer"
                  onClick={() => onNavigate("scans")}
                >
                  <div className="flex items-center gap-3">
                    <FileText className="size-4 text-primary" />
                    <div>
                      <p className="text-sm font-semibold text-foreground">{p.name}</p>
                      <p className="text-xs text-muted-foreground font-mono">
                        ID: {p.id.slice(0, 8)}... • Ingested {new Date(p.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <span className="rounded-full bg-muted px-3 py-1 font-mono text-xs font-semibold text-foreground">
                    {p.rule_count} Rules
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

function MainApp() {
  const [currentTab, setCurrentTab] = React.useState<NavTab>("policies")
  const [selectedPolicyId, setSelectedPolicyId] = React.useState<string | null>(null)

  const handleProceedToScan = (policyId: string) => {
    setSelectedPolicyId(policyId)
    setCurrentTab("scans")
  }

  return (
    <div className="flex min-h-screen bg-background text-foreground transition-colors">
      {/* Sidebar for Desktop */}
      <Sidebar
        currentTab={currentTab}
        onSelectTab={setCurrentTab}
        onNewPolicyClick={() => setCurrentTab("policies")}
      />

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col lg:ml-64">
        {/* Sticky Header */}
        <Header currentTab={currentTab} onSelectTab={setCurrentTab} />

        {/* Dynamic Screen View */}
        <main className="container mx-auto max-w-7xl flex-1 px-4 py-8 sm:px-8">
          {currentTab === "policies" && (
            <PolicyIngestionView onProceedToScan={handleProceedToScan} />
          )}

          {currentTab === "scans" && (
            <ComplianceScanView
              selectedPolicyId={selectedPolicyId}
              onSelectPolicy={setSelectedPolicyId}
            />
          )}

          {currentTab === "dashboard" && (
            <DashboardOverview onNavigate={setCurrentTab} />
          )}

          {currentTab === "audit-log" && (
            <DashboardOverview onNavigate={setCurrentTab} />
          )}
        </main>
      </div>
    </div>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider defaultTheme="dark" storageKey="compliance-ui-theme">
        <MainApp />
      </ThemeProvider>
    </QueryClientProvider>
  )
}

export default App
