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
    html_content?: string
    content?: string
    markdown_content?: string
    summary?: string
    tags?: string[]
    images?: ImageInfo[]
  }
  error?: string
  created_at: string
  completed_at?: string
  tone?: string
  word_count?: number
}

export interface DashboardStats {
  today_jobs: number
  failed_jobs: number
  in_progress_jobs: number
  completed_jobs: number
  active_users: number
  provider_stats: Record<string, number>
  estimated_cost: number
}

export interface DashboardActivity {
  id: number
  action: string
  user: string
  status: string
  timestamp: string
  model?: string
  target?: string
  provider?: string
  workflow?: string
}

export interface DashboardAlert {
  type: 'success' | 'info' | 'warning' | 'error'
  message: string
  details?: string[]
  action: string
}

export const api = {
  // Dashboard APIs
  getDashboardStats: async (): Promise<DashboardStats> => {
    const token = localStorage.getItem('authToken')
    const response = await fetch(`${API_BASE_URL}/admin/dashboard/stats`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })
    
    if (!response.ok) {
      throw new Error(`Failed to get dashboard stats: ${response.statusText}`)
    }
    
    const result = await response.json()
    return result.data
  },

  getDashboardActivities: async (limit: number = 10): Promise<DashboardActivity[]> => {
    const token = localStorage.getItem('authToken')
    const response = await fetch(`${API_BASE_URL}/admin/dashboard/activities?limit=${limit}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })
    
    if (!response.ok) {
      throw new Error(`Failed to get dashboard activities: ${response.statusText}`)
    }
    
    const result = await response.json()
    return result.data
  },

  getDashboardAlerts: async (): Promise<DashboardAlert[]> => {
    const token = localStorage.getItem('authToken')
    const response = await fetch(`${API_BASE_URL}/admin/dashboard/alerts`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })
    
    if (!response.ok) {
      throw new Error(`Failed to get dashboard alerts: ${response.statusText}`)
    }
    
    const result = await response.json()
    return result.data
  },

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
    let url = `${API_BASE_URL}/generation/jobs`
    
    // Add provider query parameter if specified
    if (provider) {
      url += `?provider=${encodeURIComponent(provider)}`
    }
    
    const headers: Record<string, string> = {}
    
    // Add authorization header only if token exists
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    
    const response = await fetch(url, {
      headers,
    })
    
    if (!response.ok) {
      throw new Error(`Failed to list jobs: ${response.statusText}`)
    }

    const result = await response.json()
    console.log('API response for listGenerationJobs:', result)
    
    // Handle new API response format: {jobs: [...], count: n}
    const jobs: GenerationResponse[] = result.jobs || result
    console.log('Parsed jobs:', jobs)
    
    return jobs
  }
}