import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Table,
  Card,
  Typography,
  Badge,
  Button,
  Space,
  Tag,
  Select,
  Input,
  Row,
  Col,
  Tooltip,
  Progress
} from 'antd';
import {
  EyeOutlined,
  ReloadOutlined,
  SearchOutlined,
  FileTextOutlined,
  CalendarOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ClockCircleOutlined,
  LoadingOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { generationAPI } from '../services/api';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/ko';

dayjs.extend(relativeTime);
dayjs.locale('ko');

const { Title, Text } = Typography;
const { Option } = Select;

interface JobData {
  id: string;
  topic: string;
  tone?: string;
  word_count?: number;
  target_language?: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  progress?: number;
  created_at: string;
  completed_at?: string;
  error?: string;
}

const Jobs: React.FC = () => {
  const navigate = useNavigate();
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const { data: jobs, isLoading, error, refetch } = useQuery({
    queryKey: ['jobs', statusFilter],
    queryFn: () => generationAPI.listJobs(),
    refetchInterval: 5000,
  });

  const getStatusBadge = (status: string, progress?: number) => {
    const statusConfig = {
      pending: { color: 'default', text: '대기', icon: <ClockCircleOutlined /> },
      in_progress: { color: 'processing', text: '진행 중', icon: <LoadingOutlined /> },
      completed: { color: 'success', text: '완료', icon: <CheckCircleOutlined /> },
      failed: { color: 'error', text: '실패', icon: <ExclamationCircleOutlined /> }
    };
    
    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.pending;
    
    return (
      <div className="flex items-center space-x-2">
        <Badge color={config.color} />
        <span className="flex items-center space-x-1">
          {config.icon}
          <span>{config.text}</span>
        </span>
        {status === 'in_progress' && progress !== undefined && (
          <Progress percent={Math.round(progress * 100)} size="small" className="w-20" />
        )}
      </div>
    );
  };

  const getToneTag = (tone?: string) => {
    if (!tone) return null;
    
    const toneColors = {
      professional: 'blue',
      casual: 'green',
      friendly: 'orange',
      formal: 'purple',
      humorous: 'pink',
      informative: 'cyan'
    };
    
    return (
      <Tag color={toneColors[tone as keyof typeof toneColors] || 'default'}>
        {tone}
      </Tag>
    );
  };

  const columns = [
    {
      title: '주제',
      dataIndex: 'topic',
      key: 'topic',
      width: 300,
      render: (topic: string, record: JobData) => (
        <div>
          <Text strong className="block mb-1">{topic}</Text>
          <div className="flex items-center space-x-2 text-xs text-gray-500">
            {getToneTag(record.tone)}
            {record.word_count && (
              <span>{record.word_count}단어</span>
            )}
            {record.target_language && (
              <Tag size="small">{record.target_language.toUpperCase()}</Tag>
            )}
          </div>
        </div>
      )
    },
    {
      title: '상태',
      dataIndex: 'status',
      key: 'status',
      width: 150,
      render: (status: string, record: JobData) => getStatusBadge(status, record.progress),
      filters: [
        { text: '대기', value: 'pending' },
        { text: '진행 중', value: 'in_progress' },
        { text: '완료', value: 'completed' },
        { text: '실패', value: 'failed' }
      ],
      onFilter: (value: any, record: JobData) => record.status === value
    },
    {
      title: '생성 시간',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (created_at: string) => (
        <Tooltip title={dayjs(created_at).format('YYYY-MM-DD HH:mm:ss')}>
          <div className="flex items-center space-x-1">
            <CalendarOutlined className="text-gray-400" />
            <span>{dayjs(created_at).fromNow()}</span>
          </div>
        </Tooltip>
      ),
      sorter: (a: JobData, b: JobData) => dayjs(a.created_at).unix() - dayjs(b.created_at).unix(),
      defaultSortOrder: 'descend' as const
    },
    {
      title: '완료 시간',
      dataIndex: 'completed_at',
      key: 'completed_at',
      width: 120,
      render: (completed_at: string) => completed_at ? (
        <Tooltip title={dayjs(completed_at).format('YYYY-MM-DD HH:mm:ss')}>
          <span>{dayjs(completed_at).fromNow()}</span>
        </Tooltip>
      ) : (
        <Text type="secondary">-</Text>
      )
    },
    {
      title: '작업',
      key: 'actions',
      width: 100,
      render: (_, record: JobData) => (
        <Space size="small">
          <Tooltip title="상세 보기">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => navigate(`/jobs/${record.id}`)}
            />
          </Tooltip>
        </Space>
      )
    }
  ];

  const filteredData = React.useMemo(() => {
    if (!jobs?.data) return [];
    
    let filtered = jobs.data;
    
    if (statusFilter && statusFilter !== 'all') {
      filtered = filtered.filter((job: JobData) => job.status === statusFilter);
    }
    
    if (searchTerm) {
      filtered = filtered.filter((job: JobData) => 
        job.topic.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    
    return filtered;
  }, [jobs?.data, statusFilter, searchTerm]);

  const getStatusCounts = () => {
    if (!jobs?.data) return { all: 0, pending: 0, in_progress: 0, completed: 0, failed: 0 };
    
    const counts = jobs.data.reduce((acc: any, job: JobData) => {
      acc[job.status] = (acc[job.status] || 0) + 1;
      acc.all = (acc.all || 0) + 1;
      return acc;
    }, {});
    
    return counts;
  };

  const statusCounts = getStatusCounts();

  return (
    <div className="p-6">
      <div className="flex justify-between items-start mb-6">
        <div>
          <Title level={2}>
            <FileTextOutlined className="mr-2" />
            작업 목록
          </Title>
          <Text type="secondary">
            콘텐츠 생성 작업의 진행 상황을 확인하고 관리하세요.
          </Text>
        </div>
        
        <Button
          icon={<ReloadOutlined />}
          onClick={() => refetch()}
          loading={isLoading}
        >
          새로고침
        </Button>
      </div>

      <Row gutter={[16, 16]} className="mb-6">
        <Col xs={24} sm={8} lg={6}>
          <Card size="small" className="text-center">
            <div className="text-2xl font-bold text-blue-600">{statusCounts.all || 0}</div>
            <div className="text-gray-500">전체</div>
          </Card>
        </Col>
        <Col xs={24} sm={8} lg={6}>
          <Card size="small" className="text-center">
            <div className="text-2xl font-bold text-yellow-600">{statusCounts.pending || 0}</div>
            <div className="text-gray-500">대기</div>
          </Card>
        </Col>
        <Col xs={24} sm={8} lg={6}>
          <Card size="small" className="text-center">
            <div className="text-2xl font-bold text-blue-600">{statusCounts.in_progress || 0}</div>
            <div className="text-gray-500">진행 중</div>
          </Card>
        </Col>
        <Col xs={24} sm={8} lg={6}>
          <Card size="small" className="text-center">
            <div className="text-2xl font-bold text-green-600">{statusCounts.completed || 0}</div>
            <div className="text-gray-500">완료</div>
          </Card>
        </Col>
      </Row>

      <Card>
        <div className="mb-4">
          <Row gutter={[16, 16]} align="middle">
            <Col xs={24} sm={12} md={8}>
              <Input
                placeholder="주제로 검색..."
                prefix={<SearchOutlined />}
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                allowClear
              />
            </Col>
            
            <Col xs={24} sm={12} md={8}>
              <Select
                placeholder="상태 필터"
                value={statusFilter}
                onChange={setStatusFilter}
                className="w-full"
              >
                <Option value="all">모든 상태</Option>
                <Option value="pending">대기 중</Option>
                <Option value="in_progress">진행 중</Option>
                <Option value="completed">완료됨</Option>
                <Option value="failed">실패함</Option>
              </Select>
            </Col>
            
            <Col xs={24} md={8} className="text-right">
              <Text type="secondary">
                총 {filteredData.length}개의 작업
              </Text>
            </Col>
          </Row>
        </div>

        <Table<JobData>
          columns={columns}
          dataSource={filteredData}
          loading={isLoading}
          rowKey="id"
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `${range[0]}-${range[1]} / 총 ${total}개`,
          }}
          scroll={{ x: 800 }}
          locale={{
            emptyText: '작업이 없습니다'
          }}
        />
      </Card>
    </div>
  );
};

export default Jobs;