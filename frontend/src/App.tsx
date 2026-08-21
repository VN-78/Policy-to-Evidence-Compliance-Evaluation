import * as React from "react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { ThemeProvider } from "@/components/theme-provider"
import { Header } from "@/components/header"
import { Sidebar, type NavTab } from "@/components/sidebar"
import { PolicyIngestionView } from "@/components/features/policy-ingestion-view"
import { ComplianceScanView } from "@/components/features/compliance-scan-view"

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
})

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
      />

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col lg:ml-64">
        {/* Sticky Top Header */}
        <Header currentTab={currentTab} onSelectTab={setCurrentTab} />

        {/* Dynamic Screen View */}
        <main className="container mx-auto max-w-7xl flex-1 px-4 py-8 sm:px-8">
          {currentTab === "policies" ? (
            <PolicyIngestionView onProceedToScan={handleProceedToScan} />
          ) : (
            <ComplianceScanView
              selectedPolicyId={selectedPolicyId}
              onSelectPolicy={setSelectedPolicyId}
            />
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
