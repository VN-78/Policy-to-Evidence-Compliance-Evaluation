import * as React from "react"
import {
  UploadCloud,
  FileText,
  Sparkles,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  Quote,
  Loader2,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { useUploadPolicyPdf, useExtractPolicyText, usePolicies } from "@/api/hooks"
import type { ExtractedRuleBase, PolicyIngestionResponse } from "@/api/types"

const SAMPLE_POLICY_NAME = "ACME Cloud Infrastructure Security & Governance Policy"
const SAMPLE_POLICY_TEXT = `ACME Corporation - Cloud Infrastructure Security & Governance Policy (v3.4)

1.0 Storage Security
All Amazon S3 buckets storing customer records and regulated data must enforce server_side_encryption set to true. Furthermore, all public access must be blocked by ensuring block_public_access is set to true. S3 buckets containing regulated data must have versioning_status set to "Enabled".

2.0 Relational Database Governance
All production RDS database instances must have storage_encrypted enabled (equal to true). Production databases must maintain a backup_retention_days threshold of at least 7 days (backup_retention_days >= 7). Production relational databases must be deployed in high-availability configuration with multi_az enabled (multi_az == true).

3.0 Compute Performance and Utilization Limits
Under baseline operations, Amazon EC2 instances must maintain average cpu_utilization below 85 percent (cpu_utilization < 85). Instances processing cardholder or authentication traffic must enforce IMDSv2 metadata protection with http_tokens set to "required".`

interface PolicyIngestionViewProps {
  onProceedToScan: (policyId: string, policyName: string) => void
}

export function PolicyIngestionView({ onProceedToScan }: PolicyIngestionViewProps) {
  const [activeTab, setActiveTab] = React.useState<"pdf" | "text">("pdf")
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null)
  const [policyName, setPolicyName] = React.useState(SAMPLE_POLICY_NAME)
  const [rawText, setRawText] = React.useState(SAMPLE_POLICY_TEXT)
  const [ingestionResult, setIngestionResult] = React.useState<PolicyIngestionResponse | null>(null)
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null)

  const uploadPdfMutation = useUploadPolicyPdf()
  const extractTextMutation = useExtractPolicyText()
  const { refetch: refetchPolicies } = usePolicies()

  const isExtracting = uploadPdfMutation.isPending || extractTextMutation.isPending

  const handleFileDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0]
      if (file.type === "application/pdf" || file.name.endsWith(".pdf")) {
        setSelectedFile(file)
        setErrorMessage(null)
      } else {
        setErrorMessage("Please upload a valid PDF document.")
      }
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0])
      setErrorMessage(null)
    }
  }

  const handleExtractPdf = async () => {
    if (!selectedFile) return
    setErrorMessage(null)
    try {
      const result = await uploadPdfMutation.mutateAsync(selectedFile)
      setIngestionResult(result)
      refetchPolicies()
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to extract rules from PDF")
    }
  }

  const handleExtractText = async () => {
    if (!rawText.trim()) return
    setErrorMessage(null)
    try {
      const result = await extractTextMutation.mutateAsync({
        policy_name: policyName.trim() || "Custom Policy",
        raw_text: rawText,
      })
      setIngestionResult(result)
      refetchPolicies()
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to extract rules from text")
    }
  }

  const loadSampleText = () => {
    setPolicyName(SAMPLE_POLICY_NAME)
    setRawText(SAMPLE_POLICY_TEXT)
    setActiveTab("text")
    setErrorMessage(null)
  }

  return (
    <div className="space-y-6">
      {/* View Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="font-heading text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
            Policy Ingestion & Rule Extraction
          </h2>
          <p className="text-sm text-muted-foreground sm:text-base">
            Upload an enterprise security policy PDF or paste unstructured prose to extract atomic,
            machine-evaluatable rules with GenAI.
          </p>
        </div>

        {/* Quick Sample Button */}
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadSampleText}
            className="rounded-lg text-xs"
            disabled={isExtracting}
          >
            <Sparkles className="size-3.5 text-primary" />
            Load Sample Policy
          </Button>
        </div>
      </div>

      {/* Error Alert */}
      {errorMessage && (
        <div className="flex items-center gap-3 rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
          <AlertCircle className="size-5 shrink-0" />
          <p className="font-medium">{errorMessage}</p>
        </div>
      )}

      {/* Main Two-Column Extraction Workspace */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Left Column: Upload / Input Panel (5 Cols) */}
        <div className="space-y-6 lg:col-span-5">
          <Card className="h-full">
            <CardHeader className="pb-4">
              <CardTitle className="text-lg">Input Policy Document</CardTitle>
              <CardDescription>Select a PDF document or paste raw text</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Tabs
                value={activeTab}
                onValueChange={(val) => setActiveTab(val as "pdf" | "text")}
                className="w-full"
              >
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="pdf">Upload PDF</TabsTrigger>
                  <TabsTrigger value="text">Paste Text</TabsTrigger>
                </TabsList>

                {/* PDF Upload Tab */}
                <TabsContent value="pdf" className="mt-4 space-y-4">
                  <div
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={handleFileDrop}
                    className="group relative flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-border/80 bg-muted/20 p-8 text-center transition-all hover:border-primary hover:bg-muted/40 cursor-pointer"
                    onClick={() => document.getElementById("pdf-file-input")?.click()}
                  >
                    <input
                      id="pdf-file-input"
                      type="file"
                      accept=".pdf,application/pdf"
                      onChange={handleFileChange}
                      className="hidden"
                    />
                    <div className="flex size-12 items-center justify-center rounded-full bg-primary/10 text-primary transition-transform group-hover:scale-110 mb-3">
                      <UploadCloud className="size-6" />
                    </div>
                    <h4 className="font-heading text-sm font-semibold text-foreground">
                      {selectedFile ? selectedFile.name : "Choose a PDF file or drag & drop"}
                    </h4>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {selectedFile
                        ? `${(selectedFile.size / 1024).toFixed(1)} KB ready for extraction`
                        : "SOC 2, ISO 27001, AWS Security Standards (PDF)"}
                    </p>
                  </div>

                  <Button
                    onClick={handleExtractPdf}
                    disabled={!selectedFile || isExtracting}
                    className="w-full gap-2 rounded-lg font-semibold"
                  >
                    {isExtracting ? (
                      <>
                        <Loader2 className="size-4 animate-spin" />
                        Extracting Rules with Gemini...
                      </>
                    ) : (
                      <>
                        <Sparkles className="size-4" />
                        Extract Rules from PDF
                      </>
                    )}
                  </Button>
                </TabsContent>

                {/* Plain Text Tab */}
                <TabsContent value="text" className="mt-4 space-y-4">
                  <div className="space-y-2">
                    <label className="text-xs font-medium text-muted-foreground">Policy Name</label>
                    <Input
                      value={policyName}
                      onChange={(e) => setPolicyName(e.target.value)}
                      placeholder="e.g. ACME Cloud Security Policy"
                      className="rounded-lg text-sm"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-xs font-medium text-muted-foreground">Policy Text</label>
                    <Textarea
                      value={rawText}
                      onChange={(e) => setRawText(e.target.value)}
                      placeholder="Paste your compliance clauses here..."
                      className="min-h-[220px] font-mono text-xs leading-relaxed"
                    />
                  </div>

                  <Button
                    onClick={handleExtractText}
                    disabled={!rawText.trim() || isExtracting}
                    className="w-full gap-2 rounded-lg font-semibold"
                  >
                    {isExtracting ? (
                      <>
                        <Loader2 className="size-4 animate-spin" />
                        Extracting Rules with Gemini...
                      </>
                    ) : (
                      <>
                        <Sparkles className="size-4" />
                        Extract Rules from Text
                      </>
                    )}
                  </Button>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Extracted Rules Preview (7 Cols) */}
        <div className="space-y-6 lg:col-span-7">
          <Card className="flex h-full flex-col">
            <CardHeader className="flex flex-row items-center justify-between border-b border-border/60 pb-4">
              <div>
                <CardTitle className="text-lg">Extracted Compliance Rules</CardTitle>
                <CardDescription>
                  {ingestionResult
                    ? `Policy: "${ingestionResult.policy_name}"`
                    : "Machine-readable rules extracted by GenAI"}
                </CardDescription>
              </div>

              {ingestionResult && (
                <Badge variant="success" className="gap-1 font-mono text-xs">
                  <CheckCircle2 className="size-3.5" />
                  {ingestionResult.rules.length} Rules Extracted
                </Badge>
              )}
            </CardHeader>

            <CardContent className="flex-1 space-y-4 p-6 overflow-y-auto max-h-[560px]">
              {ingestionResult ? (
                <div className="space-y-4">
                  {ingestionResult.rules.map((rule: ExtractedRuleBase, idx: number) => (
                    <div
                      key={rule.control_id || idx}
                      className="relative overflow-hidden rounded-xl border border-border/80 bg-card p-4 shadow-sm transition-all hover:border-primary/50"
                    >
                      <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary" />

                      {/* Card Header */}
                      <div className="mb-2 flex items-start justify-between">
                        <div className="flex items-center gap-2">
                          <Badge variant="secondary" className="font-mono text-[11px] font-bold">
                            {rule.control_id}
                          </Badge>
                          <h4 className="font-heading text-sm font-semibold text-foreground">
                            {rule.title || rule.target_metric}
                          </h4>
                        </div>
                        <Badge variant="outline" className="text-[10px]">
                          {rule.target_asset_type}
                        </Badge>
                      </div>

                      {/* Condition formula */}
                      <div className="mb-3 flex items-center gap-2 text-xs">
                        <span className="font-medium text-muted-foreground">Condition:</span>
                        <div className="rounded border border-primary/20 bg-primary/10 px-2 py-0.5 font-mono text-xs font-semibold text-primary">
                          {rule.target_metric} {rule.operator}{" "}
                          {typeof rule.threshold_value === "object"
                            ? JSON.stringify(rule.threshold_value)
                            : String(rule.threshold_value)}
                        </div>
                        {rule.pre_condition && (
                          <span className="text-[11px] text-muted-foreground">
                            (When {rule.pre_condition.target_metric} {rule.pre_condition.operator}{" "}
                            {String(rule.pre_condition.threshold_value)})
                          </span>
                        )}
                      </div>

                      {/* Verbatim Quote */}
                      <div className="relative rounded-lg border border-border/50 bg-muted/40 p-3 text-xs italic text-muted-foreground">
                        <Quote className="absolute top-2 left-2 size-3 text-muted-foreground/40" />
                        <p className="pl-4 leading-relaxed">"{rule.source_clause}"</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex h-64 flex-col items-center justify-center rounded-xl border-2 border-dashed border-border/60 bg-muted/10 p-6 text-center text-muted-foreground">
                  <FileText className="size-10 text-muted-foreground/40 mb-3" />
                  <p className="text-sm font-medium text-foreground">No rules extracted yet</p>
                  <p className="mt-1 text-xs text-muted-foreground max-w-sm">
                    Upload a PDF policy document or paste unstructured compliance clauses on the left to
                    extract structured rules.
                  </p>
                </div>
              )}
            </CardContent>

            {/* Bottom Action Footer */}
            {ingestionResult && (
              <div className="flex items-center justify-between border-t border-border/60 p-4 bg-muted/20">
                <div className="text-xs text-muted-foreground">
                  Policy ID: <span className="font-mono">{ingestionResult.policy_id.slice(0, 8)}...</span>
                </div>
                <Button
                  onClick={() =>
                    onProceedToScan(ingestionResult.policy_id, ingestionResult.policy_name)
                  }
                  className="gap-2 rounded-lg font-semibold shadow-sm"
                >
                  Proceed to Evidence Evaluation
                  <ArrowRight className="size-4" />
                </Button>
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  )
}
