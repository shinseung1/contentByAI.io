import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Card,
  Typography,
  Spin,
  Alert,
  Descriptions,
  Tag,
  Button,
  Space,
  Divider,
  Progress,
  Empty
} from 'antd';
import {
  ArrowLeftOutlined,
  ReloadOutlined,
  FileTextOutlined,
  CalendarOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ClockCircleOutlined,
  LoadingOutlined,
  CopyOutlined
} from '@ant-design/icons';
import { generationAPI } from '../services/api';
import ReactMarkdown from 'react-markdown';
import dayjs from 'dayjs';

const { Title, Text, Paragraph } = Typography;

const JobDetail: React.FC = () => {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();

  const { data: job, isLoading, error, refetch } = useQuery({
    queryKey: ['job', jobId],
    queryFn: () => generationAPI.getJob(jobId!),
    enabled: !!jobId,
    refetchInterval: (data) => {
      if (data?.data?.status === 'completed' || data?.data?.status === 'failed') {
        return false;
      }
      return 3000;
    },
  });

  const getStatusInfo = (status: string) => {
    const statusConfig = {
      pending: { 
        color: 'default', 
        text: '대기 중', 
        icon: <ClockCircleOutlined />,
        description: '작업이 큐에서 대기 중입니다.' 
      },
      in_progress: { 
        color: 'processing', 
        text: '진행 중', 
        icon: <LoadingOutlined spin />,
        description: 'AI가 콘텐츠를 생성하고 있습니다.' 
      },
      completed: { 
        color: 'success', 
        text: '완료', 
        icon: <CheckCircleOutlined />,
        description: '콘텐츠 생성이 성공적으로 완료되었습니다.' 
      },
      failed: { 
        color: 'error', 
        text: '실패', 
        icon: <ExclamationCircleOutlined />,
        description: '콘텐츠 생성 중 오류가 발생했습니다.' 
      }
    };
    
    return statusConfig[status as keyof typeof statusConfig] || statusConfig.pending;
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spin size="large" />
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="p-6">
        <Alert
          message="작업을 찾을 수 없습니다"
          description="요청한 작업이 존재하지 않거나 접근 권한이 없습니다."
          type="error"
          showIcon
          action={
            <Button onClick={() => navigate('/jobs')}>작업 목록으로</Button>
          }
        />
      </div>
    );
  }

  const jobData = job.data;
  const statusInfo = getStatusInfo(jobData.status);
  const progress = jobData.progress ? Math.round(jobData.progress * 100) : 0;

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-6">
        <Button
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/jobs')}
          className="mb-4"
        >
          작업 목록으로
        </Button>
        
        <div className="flex justify-between items-start">
          <div>
            <Title level={2}>
              <FileTextOutlined className="mr-2" />
              작업 상세
            </Title>
            <Text type="secondary">작업 ID: {jobId}</Text>
          </div>
          
          <Space>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => refetch()}
              loading={isLoading}
            >
              새로고림
            </Button>
          </Space>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <Card title="작업 상태" className="h-fit">
            <div className="text-center mb-4">
              <div className="text-4xl mb-2">{statusInfo.icon}</div>
              <Tag color={statusInfo.color} className="text-lg px-4 py-1">
                {statusInfo.text}
              </Tag>
              <div className="mt-2 text-sm text-gray-500">
                {statusInfo.description}
              </div>
            </div>
            
            {jobData.status === 'in_progress' && progress > 0 && (
              <div className="mt-4">
                <Text strong>진행률</Text>
                <Progress percent={progress} className="mt-2" />
              </div>
            )}
            
            <Divider />
            
            <Descriptions column={1} size="small">
              <Descriptions.Item label="생성 시간">
                <div className="flex items-center space-x-1">
                  <CalendarOutlined className="text-gray-400" />
                  {dayjs(jobData.created_at).format('YYYY-MM-DD HH:mm:ss')}
                </div>
              </Descriptions.Item>
              
              {jobData.completed_at && (
                <Descriptions.Item label="완료 시간">
                  <div className="flex items-center space-x-1">
                    <CheckCircleOutlined className="text-green-500" />
                    {dayjs(jobData.completed_at).format('YYYY-MM-DD HH:mm:ss')}
                  </div>
                </Descriptions.Item>
              )}
            </Descriptions>
            
            {jobData.error && (
              <Alert
                message="오류 발생"
                description={jobData.error}
                type="error"
                size="small"
                className="mt-4"
              />
            )}
          </Card>
        </div>

        <div className="lg:col-span-2">
          <Card title="작업 정보">
            <Descriptions column={2} bordered>
              <Descriptions.Item label="주제" span={2}>
                <Text strong>{jobData.topic || jobData.job_id}</Text>
              </Descriptions.Item>
              
              <Descriptions.Item label="작성 톤">
                {jobData.tone ? (
                  <Tag color="blue">{jobData.tone}</Tag>
                ) : (
                  <Text type="secondary">-</Text>
                )}
              </Descriptions.Item>
              
              <Descriptions.Item label="목표 단어 수">
                {jobData.word_count ? `${jobData.word_count}단어` : '-'}
              </Descriptions.Item>
              
              <Descriptions.Item label="언어">
                {jobData.target_language ? (
                  <Tag>{jobData.target_language.toUpperCase()}</Tag>
                ) : (
                  <Text type="secondary">-</Text>
                )}
              </Descriptions.Item>
              
              <Descriptions.Item label="이미지 포함">
                {jobData.include_images !== undefined ? (
                  <Tag color={jobData.include_images ? 'green' : 'default'}>
                    {jobData.include_images ? '포함' : '미포함'}
                  </Tag>
                ) : (
                  <Text type="secondary">-</Text>
                )}
              </Descriptions.Item>
            </Descriptions>
          </Card>
        </div>
      </div>

      {jobData.status === 'completed' && jobData.content && (
        <div className="mt-6">
          <Card 
            title="생성된 콘텐츠"
            extra={
              <Button
                icon={<CopyOutlined />}
                onClick={() => copyToClipboard(jobData.content.content)}
              >
                복사
              </Button>
            }
          >
            <div className="space-y-4">
              {jobData.content.title && (
                <div>
                  <Text strong className="text-lg block mb-2">제목</Text>
                  <Title level={3} copyable>{jobData.content.title}</Title>
                </div>
              )}
              
              {jobData.content.summary && (
                <div>
                  <Text strong className="block mb-2">요약</Text>
                  <Paragraph className="bg-gray-50 p-4 rounded">
                    {jobData.content.summary}
                  </Paragraph>
                </div>
              )}
              
              {jobData.content.tags && jobData.content.tags.length > 0 && (
                <div>
                  <Text strong className="block mb-2">태그</Text>
                  <Space wrap>
                    {jobData.content.tags.map((tag: string, index: number) => (
                      <Tag key={index} color="blue">{tag}</Tag>
                    ))}
                  </Space>
                </div>
              )}
              
              <Divider />
              
              <div>
                <Text strong className="block mb-2">본문</Text>
                <div className="prose max-w-none bg-white p-6 rounded border">
                  <ReactMarkdown>{jobData.content.content}</ReactMarkdown>
                </div>
              </div>
              
              {jobData.content.images && jobData.content.images.length > 0 && (
                <div>
                  <Text strong className="block mb-2">이미지</Text>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    {jobData.content.images.map((image: string, index: number) => (
                      <img
                        key={index}
                        src={image}
                        alt={`Generated ${index + 1}`}
                        className="w-full h-32 object-cover rounded border"
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>
          </Card>
        </div>
      )}

      {(jobData.status === 'pending' || jobData.status === 'in_progress') && (
        <div className="mt-6">
          <Card>
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description={
                <div className="text-center">
                  <Text type="secondary">
                    {jobData.status === 'pending' 
                      ? '작업이 시작되면 생성된 콘텐츠가 여기에 표시됩니다.'
                      : '콘텐츠를 생성하고 있습니다. 잠시만 기다려주세요...'
                    }
                  </Text>
                </div>
              }
            />
          </Card>
        </div>
      )}
    </div>
  );
};

export default JobDetail;