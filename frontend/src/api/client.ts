import type {
  ComplianceScanResponse,
  EvidencePayload,
  HealthResponse,
  PolicyIngestionResponse,
  PolicyListItem,
  ExtractedRuleBase,
} from "./types"

const BASE_URL =
  import.meta.env.VITE_API_URL ||
  "https://policy-to-evidence-compliance-evaluation.onrender.com"

class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.name = "ApiError"
    this.status = status
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = `HTTP ${res.status} ${res.statusText}`
    try {
      const errJson = await res.json()
      if (errJson.detail) {
        errorDetail =
          typeof errJson.detail === "string"
            ? errJson.detail
            : JSON.stringify(errJson.detail)
      }
    } catch {
      // Ignored if not JSON
    }
    throw new ApiError(errorDetail, res.status)
  }
  return res.json() as Promise<T>
}

export const api = {
  getHealth: async (): Promise<HealthResponse> => {
    const res = await fetch(`${BASE_URL}/health`)
    return handleResponse<HealthResponse>(res)
  },

  getPolicies: async (): Promise<PolicyListItem[]> => {
    const res = await fetch(`${BASE_URL}/api/v1/policies`)
    return handleResponse<PolicyListItem[]>(res)
  },

  getPolicyRules: async (policyId: string): Promise<ExtractedRuleBase[]> => {
    const res = await fetch(`${BASE_URL}/api/v1/policies/${policyId}/rules`)
    return handleResponse<ExtractedRuleBase[]>(res)
  },

  uploadPolicyPdf: async (file: File): Promise<PolicyIngestionResponse> => {
    const formData = new FormData()
    formData.append("file", file)
    const res = await fetch(`${BASE_URL}/api/v1/policies/upload-pdf`, {
      method: "POST",
      body: formData,
    })
    return handleResponse<PolicyIngestionResponse>(res)
  },

  extractPolicyText: async (payload: {
    policy_name: string
    raw_text: string
  }): Promise<PolicyIngestionResponse> => {
    const res = await fetch(`${BASE_URL}/api/v1/policies/extract-text`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    return handleResponse<PolicyIngestionResponse>(res)
  },

  runComplianceScan: async (
    evidence: EvidencePayload,
    policyId?: string
  ): Promise<ComplianceScanResponse> => {
    const url = new URL(`${BASE_URL}/api/v1/compliance/scan`)
    if (policyId) {
      url.searchParams.set("policy_id", policyId)
    }
    const res = await fetch(url.toString(), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(evidence),
    })
    return handleResponse<ComplianceScanResponse>(res)
  },
}
