import * as React from "react"
import {
  Play,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ChevronRight,
  ChevronDown,
  Gavel,
  ShieldCheck,
  Loader2,
  Sparkles,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Textarea } from "@/components/ui/textarea"
import { usePolicies, useRunComplianceScan } from "@/api/hooks"
import type {
  AssetEvaluationResult,
  ComplianceScanResponse,
  EvidencePayload,
  RuleEvaluationResult,
} from "@/api/types"

const SAMPLE_EVIDENCE_JSON: EvidencePayload = {
  scan_id: "audit-scan-2026-08-prod-01",
  environment: "production",
  assets: [
    {
      asset_id: "arn:aws:s3:::acme-customer-records-prod",
      asset_type: "s3_bucket",
      region: "ap-south-1",
      metrics: {
        classification: "regulated_data",
        server_side_encryption: true,
        block_public_access: true,
        versioning_status: "Enabled",
      },
    },
    {
      asset_id: "arn:aws:s3:::acme-public-assets-static",
      asset_type: "s3_bucket",
      region: "ap-south-1",
      metrics: {
        classification: "public_static",
        server_side_encryption: true,
        block_public_access: false,
        versioning_status: "Suspended",
      },
    },
    {
      asset_id: "arn:aws:rds:ap-south-1:123456789012:db:acme-core-postgres-prod",
      asset_type: "rds_instance",
      region: "ap-south-1",
      metrics: {
        environment: "production",
        storage_encrypted: true,
        multi_az: true,
        backup_retention_days: 14,
      },
    },
    {
      asset_id: "i-0a1b2c3d4e5f67890",
      asset_type: "ec2_instance",
      region: "ap-south-1",
      metrics: {
        instance_name: "payment-api-worker-01",
        cpu_utilization: 64.2,
        http_tokens: "required",
      },
    },
    {
      asset_id: "i-098765fedcba43210",
      asset_type: "ec2_instance",
      region: "ap-south-1",
      metrics: {
        instance_name: "legacy-report-generator",
        cpu_utilization: 91.8,
      },
    },
  ],
}

interface ComplianceScanViewProps {
  selectedPolicyId: string | null
  onSelectPolicy: (policyId: string) => void
}

export function ComplianceScanView({
  selectedPolicyId,
  onSelectPolicy,
}: ComplianceScanViewProps) {
  const [evidenceText, setEvidenceText] = React.useState(
    JSON.stringify(SAMPLE_EVIDENCE_JSON, null, 2)
  )
  const [expandedAssets, setExpandedAssets] = React.useState<Record<string, boolean>>({})
  const [scanResult, setScanResult] = React.useState<ComplianceScanResponse | null>(null)
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null)

  const { data: policies, isLoading: isLoadingPolicies } = usePolicies()
  const scanMutation = useRunComplianceScan()

  // Auto-select latest policy if none selected
  React.useEffect(() => {
    if (!selectedPolicyId && policies && policies.length > 0) {
      onSelectPolicy(policies[0].id)
    }
  }, [selectedPolicyId, policies, onSelectPolicy])

  const toggleAssetExpand = (assetId: string) => {
    setExpandedAssets((prev) => ({
      ...prev,
      [assetId]: !prev[assetId],
    }))
  }

  const handleRunScan = async () => {
    setErrorMessage(null)
    try {
      const parsedEvidence: EvidencePayload = JSON.parse(evidenceText)
      if (!parsedEvidence.assets || !Array.isArray(parsedEvidence.assets)) {
        throw new Error("Evidence payload must contain an 'assets' array.")
      }

      const result = await scanMutation.mutateAsync({
        evidence: parsedEvidence,
        policyId: selectedPolicyId || undefined,
      })
      setScanResult(result)
      // Auto-expand all assets with non-compliant status
      const initialExpanded: Record<string, boolean> = {}
      result.asset_results.forEach((asset) => {
        initialExpanded[asset.asset_id] = true
      })
      setExpandedAssets(initialExpanded)
    } catch (err: unknown) {
      setErrorMessage(
        err instanceof Error ? err.message : "Failed to run compliance scan."
      )
    }
  }

  const loadSampleEvidence = () => {
    setEvidenceText(JSON.stringify(SAMPLE_EVIDENCE_JSON, null, 2))
    setErrorMessage(null)
  }

  const formatJson = () => {
    try {
      const parsed = JSON.parse(evidenceText)
      setEvidenceText(JSON.stringify(parsed, null, 2))
      setErrorMessage(null)
    } catch {
      setErrorMessage("Cannot format invalid JSON.")
    }
  }

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="font-heading text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
            Compliance Scan Workspace
          </h2>
          <p className="text-sm text-muted-foreground sm:text-base">
            Ingest live infrastructure telemetry JSON and deterministically evaluate compliance
            against active policy rules.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadSampleEvidence}
            className="rounded-lg text-xs"
            disabled={scanMutation.isPending}
          >
            <Sparkles className="size-3.5 text-primary" />
            Load Sample Evidence
          </Button>
        </div>
      </div>

      {/* Error Message */}
      {errorMessage && (
        <div className="flex items-center gap-3 rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
          <AlertTriangle className="size-5 shrink-0" />
          <p className="font-medium">{errorMessage}</p>
        </div>
      )}

      {/* Input Section: Evidence Payload + Policy Selector */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Evidence JSON Editor (8 Cols) */}
        <div className="lg:col-span-8">
          <Card className="h-full">
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <div>
                <CardTitle className="text-lg">Infrastructure Evidence Payload</CardTitle>
                <CardDescription>Raw telemetry JSON emitted from cloud monitoring</CardDescription>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="xs"
                  onClick={formatJson}
                  className="rounded text-xs"
                >
                  Format JSON
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <Textarea
                value={evidenceText}
                onChange={(e) => setEvidenceText(e.target.value)}
                placeholder="Paste raw telemetry evidence JSON..."
                className="h-[280px] font-mono text-xs leading-relaxed bg-muted/20"
              />
            </CardContent>
          </Card>
        </div>

        {/* Scan Action & Policy Selector Panel (4 Cols) */}
        <div className="lg:col-span-4">
          <Card className="flex h-full flex-col justify-between p-6">
            <div className="space-y-4">
              <div>
                <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Target Compliance Policy
                </label>
                <select
                  value={selectedPolicyId || ""}
                  onChange={(e) => onSelectPolicy(e.target.value)}
                  disabled={isLoadingPolicies}
                  className="mt-2 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm shadow-sm transition-colors focus:border-ring focus:outline-none"
                >
                  {isLoadingPolicies ? (
                    <option>Loading policies...</option>
                  ) : policies && policies.length > 0 ? (
                    policies.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name} ({p.rule_count} rules)
                      </option>
                    ))
                  ) : (
                    <option value="">No policies available (upload one first)</option>
                  )}
                </select>
              </div>

              <div className="rounded-lg border border-border/80 bg-muted/20 p-4 text-xs text-muted-foreground space-y-2">
                <div className="flex items-center gap-2 font-semibold text-foreground">
                  <ShieldCheck className="size-4 text-primary" />
                  Deterministic Audit Engine
                </div>
                <p>
                  Evaluates arithmetic thresholds, string matching, and conditional requirements
                  with zero LLM hallucinations during scan time.
                </p>
              </div>
            </div>

            <Button
              onClick={handleRunScan}
              disabled={scanMutation.isPending || !selectedPolicyId}
              className="mt-6 w-full gap-2 rounded-lg py-5 text-sm font-semibold shadow-md"
            >
              {scanMutation.isPending ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  Evaluating Evidence...
                </>
              ) : (
                <>
                  <Play className="size-4" />
                  Run Compliance Scan
                </>
              )}
            </Button>
          </Card>
        </div>
      </div>

      {/* Results Dashboard Section */}
      {scanResult && (
        <div className="space-y-6 pt-4 border-t border-border/60">
          {/* Header */}
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h3 className="font-heading text-xl font-bold tracking-tight text-foreground sm:text-2xl">
                Scan Audit Results
              </h3>
              <p className="text-xs text-muted-foreground sm:text-sm font-mono">
                Scan ID: {scanResult.scan_id} • Environment: {scanResult.environment}
              </p>
            </div>
          </div>

          {/* Global KPI Summary Cards */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {/* Overall Status Card */}
            <Card
              className={
                scanResult.overall_status === "Compliant"
                  ? "border-emerald-500/30 bg-emerald-500/10"
                  : "border-destructive/30 bg-destructive/10"
              }
            >
              <CardContent className="flex items-center gap-4 p-5">
                <div
                  className={`flex size-12 items-center justify-center rounded-xl font-bold ${
                    scanResult.overall_status === "Compliant"
                      ? "bg-emerald-500 text-white"
                      : "bg-destructive text-white"
                  }`}
                >
                  {scanResult.overall_status === "Compliant" ? (
                    <CheckCircle2 className="size-6" />
                  ) : (
                    <XCircle className="size-6" />
                  )}
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Overall Posture
                  </p>
                  <p
                    className={`font-heading text-lg font-bold ${
                      scanResult.overall_status === "Compliant"
                        ? "text-emerald-600 dark:text-emerald-400"
                        : "text-destructive"
                    }`}
                  >
                    {scanResult.overall_status}
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Total Assets Scanned */}
            <Card>
              <CardContent className="p-5">
                <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Total Assets Scanned
                </p>
                <p className="mt-1 font-heading text-2xl font-bold text-foreground">
                  {scanResult.total_assets}
                </p>
              </CardContent>
            </Card>

            {/* Compliant Assets */}
            <Card className="relative overflow-hidden">
              <div className="absolute right-0 top-0 bottom-0 w-1.5 bg-emerald-500" />
              <CardContent className="p-5">
                <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Compliant Assets
                </p>
                <p className="mt-1 font-heading text-2xl font-bold text-emerald-600 dark:text-emerald-400">
                  {scanResult.compliant_assets_count}
                </p>
              </CardContent>
            </Card>

            {/* Non-Compliant Assets */}
            <Card className="relative overflow-hidden">
              <div className="absolute right-0 top-0 bottom-0 w-1.5 bg-destructive" />
              <CardContent className="p-5">
                <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Non-Compliant Assets
                </p>
                <p className="mt-1 font-heading text-2xl font-bold text-destructive">
                  {scanResult.non_compliant_assets_count}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Detailed Asset Table */}
          <Card className="overflow-hidden">
            <CardHeader className="border-b border-border/60 bg-muted/30 py-4 px-6">
              <CardTitle className="text-base">Asset Compliance Details & Evaluation Breakdown</CardTitle>
            </CardHeader>

            <CardContent className="p-0 divide-y divide-border/60">
              {scanResult.asset_results.map((asset: AssetEvaluationResult) => {
                const isExpanded = expandedAssets[asset.asset_id]
                const isAssetCompliant = asset.overall_status === "Compliant"

                return (
                  <div key={asset.asset_id} className="transition-colors">
                    {/* Asset Header Row */}
                    <div
                      onClick={() => toggleAssetExpand(asset.asset_id)}
                      className="flex items-center justify-between p-4 px-6 hover:bg-muted/30 cursor-pointer select-none transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-muted-foreground">
                          {isExpanded ? (
                            <ChevronDown className="size-4" />
                          ) : (
                            <ChevronRight className="size-4" />
                          )}
                        </span>
                        <div className="flex flex-col">
                          <span className="font-mono text-xs font-semibold text-foreground sm:text-sm">
                            {asset.asset_id}
                          </span>
                          <span className="text-[11px] text-muted-foreground">
                            Category: {asset.asset_type}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        <Badge
                          variant={isAssetCompliant ? "success" : "destructive"}
                          className="font-mono text-[11px] font-bold"
                        >
                          {asset.overall_status}
                        </Badge>
                      </div>
                    </div>

                    {/* Expandable Checks Details */}
                    {isExpanded && (
                      <div className="bg-muted/15 p-6 space-y-4 border-t border-border/40">
                        <h4 className="font-heading text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                          Evaluated Policy Checks ({asset.checks.length})
                        </h4>

                        <div className="space-y-3">
                          {asset.checks.map((check: RuleEvaluationResult, idx: number) => {
                            const isCheckPassed = check.status === "Compliant"
                            return (
                              <div
                                key={check.control_id || idx}
                                className={`rounded-xl border p-4 shadow-sm relative overflow-hidden bg-card ${
                                  isCheckPassed
                                    ? "border-emerald-500/20"
                                    : "border-destructive/30"
                                }`}
                              >
                                <div
                                  className={`absolute left-0 top-0 bottom-0 w-1 ${
                                    isCheckPassed ? "bg-emerald-500" : "bg-destructive"
                                  }`}
                                />

                                <div className="ml-2 space-y-3">
                                  {/* Check Title & Status */}
                                  <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                      {isCheckPassed ? (
                                        <CheckCircle2 className="size-4 text-emerald-500" />
                                      ) : (
                                        <XCircle className="size-4 text-destructive" />
                                      )}
                                      <span className="font-mono text-xs font-bold text-foreground">
                                        {check.control_id}
                                      </span>
                                      <span className="text-xs text-muted-foreground">
                                        ({check.target_metric})
                                      </span>
                                    </div>

                                    <Badge
                                      variant={isCheckPassed ? "success" : "destructive"}
                                      className="text-[10px]"
                                    >
                                      {check.status}
                                    </Badge>
                                  </div>

                                  {/* Metrics Comparison Grid */}
                                  <div className="grid grid-cols-2 gap-3 text-xs">
                                    <div className="rounded-lg border border-border/50 bg-muted/30 p-2.5">
                                      <span className="block text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                                        Actual Metric Value
                                      </span>
                                      <span
                                        className={`font-mono font-bold ${
                                          isCheckPassed
                                            ? "text-emerald-600 dark:text-emerald-400"
                                            : "text-destructive"
                                        }`}
                                      >
                                        {check.actual_value !== undefined && check.actual_value !== null
                                          ? String(check.actual_value)
                                          : "null / missing"}
                                      </span>
                                    </div>

                                    <div className="rounded-lg border border-border/50 bg-muted/30 p-2.5">
                                      <span className="block text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                                        Required Policy Threshold
                                      </span>
                                      <span className="font-mono font-semibold text-foreground">
                                        {check.operator} {String(check.threshold_value)}
                                      </span>
                                    </div>
                                  </div>

                                  {/* Audit Reasoning Box */}
                                  <div className="rounded-lg border border-border/60 bg-muted/40 p-3 text-xs leading-relaxed">
                                    <div className="flex items-center gap-1.5 font-semibold text-foreground mb-1">
                                      <Gavel className="size-3.5 text-primary" />
                                      Audit Reasoning:
                                    </div>
                                    <p className="text-muted-foreground italic">
                                      "{check.audit_reasoning}"
                                    </p>
                                  </div>
                                </div>
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
