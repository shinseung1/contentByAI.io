export const API_BASE_URL = 'http://127.0.0.1:3005/api/v1'

export interface GenerationRequest {
  topic: string
  provider?: string
  tone: string
  word_count: number
  include_images: boolean
  target_language: string
}

export interface GenerationJobResponse {
  jobId: string
  status: string
  message: string
}

export interface ImageInfo {
  url: string
  alt: string
  caption: string
}

export interface GenerationResponse {
  job_id: string
  status: string
  message: string
  progress: number
  content?: {
    title: string
    content: string
    markdown_content?: string
    summary?: string
    tags: string[]
    images: ImageInfo[]
  }
  error?: string
  created_at: string
  completed_at?: string
  tone?: string
  word_count?: number
}

export const api = {
  // Content Generation
  generateContent: async (request: GenerationRequest): Promise<GenerationJobResponse> => {
    const token = localStorage.getItem('authToken')
    const response = await fetch(`${API_BASE_URL}/generation/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      throw new Error(`Generation failed: ${response.statusText}`)
    }

    const result = await response.json()
    // Convert backend job_id to frontend jobId
    return {
      jobId: result.job_id,
      status: result.status,
      message: result.message
    }
  },

  getGenerationJob: async (jobId: string): Promise<GenerationResponse> => {
    const token = localStorage.getItem('authToken')
    const response = await fetch(`${API_BASE_URL}/generation/jobs/${jobId}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })
    
    if (!response.ok) {
      throw new Error(`Failed to get job: ${response.statusText}`)
    }

    return response.json()
  },

  listGenerationJobs: async (provider?: string): Promise<GenerationResponse[]> => {
    const token = localStorage.getItem('authToken')
    const url = `${API_BASE_URL}/generation/jobs`
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })
    
    if (!response.ok) {
      throw new Error(`Failed to list jobs: ${response.statusText}`)
    }

    const jobs: GenerationResponse[] = await response.json()
    console.log('API response for listGenerationJobs:', jobs)
    console.log('First job tone:', jobs[0]?.tone, 'word_count:', jobs[0]?.word_count)
    jobs.forEach((job, index) => {
      if (index < 3) {
        console.log(`Job ${index}: tone=${job.tone}, word_count=${job.word_count}, job_id=${job.job_id}`)
      }
    })
    
    // Filter by provider if specified
    if (provider) {
      return jobs.filter(job => 
        job.message?.includes(provider) || true // Return all for now
      )
    }
    
    return jobs
  }
}