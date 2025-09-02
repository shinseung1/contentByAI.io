const API_BASE_URL = 'http://127.0.0.1:3000/api/v1'

export interface GenerationRequest {
  topic: string
  provider?: string
  tone: string
  word_count: number
  include_images: boolean
  target_language: string
}

export interface GenerationJobResponse {
  job_id: string
  status: string
  message: string
}

export interface GenerationResponse {
  job_id: string
  status: string
  message: string
  progress: number
  content?: {
    title: string
    content: string
    summary?: string
    tags: string[]
    images: string[]
  }
  error?: string
  created_at: string
  completed_at?: string
}

export const api = {
  // Content Generation
  generateContent: async (request: GenerationRequest): Promise<GenerationJobResponse> => {
    const response = await fetch(`${API_BASE_URL}/generation/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      throw new Error(`Generation failed: ${response.statusText}`)
    }

    return response.json()
  },

  getGenerationJob: async (jobId: string): Promise<GenerationResponse> => {
    const response = await fetch(`${API_BASE_URL}/generation/jobs/${jobId}`)
    
    if (!response.ok) {
      throw new Error(`Failed to get job: ${response.statusText}`)
    }

    return response.json()
  },

  listGenerationJobs: async (): Promise<string[]> => {
    const response = await fetch(`${API_BASE_URL}/generation/jobs`)
    
    if (!response.ok) {
      throw new Error(`Failed to list jobs: ${response.statusText}`)
    }

    return response.json()
  }
}