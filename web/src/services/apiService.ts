import axios from 'axios';

// API 기본 설정
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 응답 인터셉터
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// API 서비스 타입 정의
export interface TestResult {
  success: boolean;
  provider: string;
  message: string;
  response?: string;
  tokenUsage?: {
    promptTokenCount: number;
    candidatesTokenCount: number;
    totalTokenCount: number;
  };
  timestamp: string;
}

export interface GenerationRequest {
  topic: string;
  tone?: string;
  wordCount?: number;
  includeImages?: boolean;
  targetLanguage?: string;
}

export interface GenerationResponse {
  jobId: string;
  status: string;
  message: string;
}

export interface JobStatus {
  jobId: string;
  status: string;
  progress?: number;
  message?: string;
  result?: {
    bundleId: string;
    title: string;
    contentPreview: string;
    wordCount: number;
    imagesCount: number;
    seoScore: number;
  };
  errorMessage?: string;
  errorCode?: string;
}

// API 서비스 클래스
export class ApiService {
  // 헬스체크
  static async healthCheck(): Promise<any> {
    const response = await apiClient.get('/health/');
    return response.data;
  }

  // AI API 테스트
  static async testAiApi(provider: string, prompt?: string): Promise<TestResult> {
    try {
      const response = await apiClient.post('/test/ai', {
        provider,
        prompt: prompt || '안녕하세요! 간단한 인사말로 답해주세요.'
      });
      return {
        success: true,
        provider,
        message: 'API 테스트 성공',
        response: response.data.content,
        tokenUsage: response.data.tokenUsage,
        timestamp: new Date().toISOString()
      };
    } catch (error: any) {
      return {
        success: false,
        provider,
        message: error.response?.data?.message || error.message,
        timestamp: new Date().toISOString()
      };
    }
  }

  // 테스트 결과 조회
  static async getTestResults(provider: string, limit: number = 50): Promise<any[]> {
    const response = await apiClient.get(`/test-results/${provider}?limit=${limit}`);
    return response.data;
  }

  // 제공자별 통계 조회
  static async getProviderStats(provider: string): Promise<any> {
    const response = await apiClient.get(`/provider-stats/${provider}`);
    return response.data;
  }

  // 콘텐츠 생성 작업 목록 조회
  static async getGenerationJobs(provider: string, limit: number = 50): Promise<any[]> {
    const response = await apiClient.get(`/generation/jobs?provider=${provider}&limit=${limit}`);
    return response.data;
  }

  // 콘텐츠 생성
  static async generateContent(request: GenerationRequest): Promise<GenerationResponse> {
    const response = await apiClient.post('/generation/generate', request);
    return response.data;
  }

  // 작업 상태 확인
  static async getJobStatus(jobId: string): Promise<JobStatus> {
    const response = await apiClient.get(`/generation/jobs/${jobId}`);
    return response.data;
  }

  // 번들 목록 조회
  static async getBundles(limit?: number, offset?: number) {
    const params = new URLSearchParams();
    if (limit) params.append('limit', limit.toString());
    if (offset) params.append('offset', offset.toString());
    
    const response = await apiClient.get(`/bundles/?${params}`);
    return response.data;
  }

  // 번들 상세 조회
  static async getBundleDetail(bundleId: string) {
    const response = await apiClient.get(`/bundles/${bundleId}`);
    return response.data;
  }

  // 발행 작업
  static async publishContent(bundleId: string, platform: string, mode: string, scheduledDateTime?: string) {
    const response = await apiClient.post('/publishing/publish', {
      bundleId,
      platform,
      mode,
      scheduledDateTime
    });
    return response.data;
  }

  // 플랫폼 연결 테스트
  static async testPlatformConnection(platform: string) {
    const response = await apiClient.post(`/publishing/test-connection/${platform}`);
    return response.data;
  }
}

export default ApiService;