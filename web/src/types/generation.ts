export interface GenerateContentRequest {
  topic: string;
  tone?: string;
  word_count?: number;
  include_images?: boolean;
  target_language?: string;
  scheduled_at?: string;
}

export interface GenerationJobResponse {
  job_id: string;
  status: string;
  message: string;
}

export interface GeneratedContent {
  title: string;
  content: string;
  summary?: string;
  tags: string[];
  images: string[];
}

export interface GenerationResponse {
  job_id: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  message: string;
  progress?: number;
  content?: GeneratedContent;
  error?: string;
  created_at?: string;
  completed_at?: string;
}

export interface Job {
  id: string;
  topic: string;
  tone?: string;
  word_count?: number;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  created_at: string;
  completed_at?: string;
  error?: string;
}