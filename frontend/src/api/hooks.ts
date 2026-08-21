import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { api } from "./client"
import type {
  ComplianceScanResponse,
  EvidencePayload,
  HealthResponse,
  PolicyIngestionResponse,
  PolicyListItem,
  ExtractedRuleBase,
} from "./types"

export const QUERY_KEYS = {
  health: ["health"] as const,
  policies: ["policies"] as const,
  policyRules: (policyId: string) => ["policies", policyId, "rules"] as const,
}

export function useHealth() {
  return useQuery<HealthResponse, Error>({
    queryKey: QUERY_KEYS.health,
    queryFn: api.getHealth,
    refetchInterval: 30000,
    retry: 1,
  })
}

export function usePolicies() {
  return useQuery<PolicyListItem[], Error>({
    queryKey: QUERY_KEYS.policies,
    queryFn: api.getPolicies,
  })
}

export function usePolicyRules(policyId: string | null | undefined) {
  return useQuery<ExtractedRuleBase[], Error>({
    queryKey: QUERY_KEYS.policyRules(policyId || ""),
    queryFn: () => {
      if (!policyId) return Promise.resolve([])
      return api.getPolicyRules(policyId)
    },
    enabled: Boolean(policyId),
  })
}

export function useUploadPolicyPdf() {
  const queryClient = useQueryClient()
  return useMutation<PolicyIngestionResponse, Error, File>({
    mutationFn: (file: File) => api.uploadPolicyPdf(file),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.policies })
      queryClient.setQueryData(QUERY_KEYS.policyRules(data.policy_id), data.rules)
    },
  })
}

export function useExtractPolicyText() {
  const queryClient = useQueryClient()
  return useMutation<
    PolicyIngestionResponse,
    Error,
    { policy_name: string; raw_text: string }
  >({
    mutationFn: (payload) => api.extractPolicyText(payload),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.policies })
      queryClient.setQueryData(QUERY_KEYS.policyRules(data.policy_id), data.rules)
    },
  })
}

export function useRunComplianceScan() {
  return useMutation<
    ComplianceScanResponse,
    Error,
    { evidence: EvidencePayload; policyId?: string }
  >({
    mutationFn: ({ evidence, policyId }) =>
      api.runComplianceScan(evidence, policyId),
  })
}
