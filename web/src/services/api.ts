export const API_BASE_URL = 'http://127.0.0.1:3000/api/v1'

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

export interface ScheduledPost {
  schedule_id: string
  title: string
  topic?: string
  topic_source: 'user' | 'trend'
  schedule_time: string
  status: 'pending' | 'completed' | 'failed' | 'paused'
  provider: string
  workflow_template_id?: number
  repeat_config?: string
  generated_job_id?: string
  error_message?: string
  created_at: string
  updated_at: string
  last_executed_at?: string
}

export interface CreateScheduledPostRequest {
  title: string
  topic?: string
  topic_source: 'user' | 'trend'
  schedule_time: string
  provider: string
  workflow_template_id?: number
  repeat_config?: string
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
  },

  // Scheduled Posts API
  listScheduledPosts: async (): Promise<ScheduledPost[]> => {
    const token = localStorage.getItem('authToken')
    const response = await fetch(`${API_BASE_URL}/scheduled-posts/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })
    
    if (!response.ok) {
      throw new Error(`Failed to list scheduled posts: ${response.statusText}`)
    }

    return response.json()
  },

  createScheduledPost: async (scheduledPost: CreateScheduledPostRequest): Promise<ScheduledPost> => {
    const token = localStorage.getItem('authToken')
    const response = await fetch(`${API_BASE_URL}/scheduled-posts/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(scheduledPost),
    })

    if (!response.ok) {
      throw new Error(`Failed to create scheduled post: ${response.statusText}`)
    }

    return response.json()
  },

  updateScheduledPost: async (scheduleId: string, scheduledPost: CreateScheduledPostRequest): Promise<ScheduledPost> => {
    const token = localStorage.getItem('authToken')
    const response = await fetch(`${API_BASE_URL}/scheduled-posts/${scheduleId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(scheduledPost),
    })

    if (!response.ok) {
      throw new Error(`Failed to update scheduled post: ${response.statusText}`)
    }

    return response.json()
  },

  deleteScheduledPost: async (scheduleId: string): Promise<void> => {
    const token = localStorage.getItem('authToken')
    const response = await fetch(`${API_BASE_URL}/scheduled-posts/${scheduleId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })

    if (!response.ok) {
      throw new Error(`Failed to delete scheduled post: ${response.statusText}`)
    }
  },

  toggleScheduledPostStatus: async (scheduleId: string): Promise<ScheduledPost> => {
    const token = localStorage.getItem('authToken')
    const response = await fetch(`${API_BASE_URL}/scheduled-posts/${scheduleId}/toggle`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })

    if (!response.ok) {
      throw new Error(`Failed to toggle scheduled post status: ${response.statusText}`)
    }

    return response.json()
  }
}