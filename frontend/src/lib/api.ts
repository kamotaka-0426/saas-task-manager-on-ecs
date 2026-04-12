type ApiError = { response?: { data?: { detail?: string } } }

export function getApiErrorDetail(err: unknown, fallback: string): string {
  return (err as ApiError).response?.data?.detail ?? fallback
}
