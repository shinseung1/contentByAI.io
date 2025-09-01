import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Table,
  Card,
  Typography,
  Button,
  Tag,
  Space,
  Modal,
  Form,
  Input,
  Select,
  Tooltip,
  Popconfirm,
  message,
  Badge,
  Dropdown,
  MenuProps
} from 'antd';
import {
  FileTextOutlined,
  EditOutlined,
  DeleteOutlined,
  SendOutlined,
  EyeOutlined,
  MoreOutlined,
  FileImageOutlined,
  GoogleOutlined,
  ExportOutlined
} from '@ant-design/icons';
import { generationAPI } from '../services/api';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Option } = Select;

interface Post {
  id: string;
  title: string;
  content: string;
  summary?: string;
  tags?: string[];
  status: 'draft' | 'published' | 'scheduled';
  platform?: 'wordpress' | 'blogger' | 'medium';
  created_at: string;
  published_at?: string;
  views?: number;
  likes?: number;
}

const Posts: React.FC = () => {
  const [selectedPosts, setSelectedPosts] = useState<string[]>([]);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingPost, setEditingPost] = useState<Post | null>(null);
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  const { data: posts, isLoading } = useQuery({
    queryKey: ['posts'],
    queryFn: () => generationAPI.listJobs(),
    select: (data) => data.data.filter((job: any) => job.status === 'completed' && job.content)
  });

  const publishMutation = useMutation({
    mutationFn: ({ postId, platform }: { postId: string; platform: string }) => 
      generationAPI.publishPost(postId, platform),
    onSuccess: () => {
      message.success('포스트가 성공적으로 발행되었습니다.');
      queryClient.invalidateQueries({ queryKey: ['posts'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '포스트 발행에 실패했습니다.');
    }
  });

  const deleteMutation = useMutation({
    mutationFn: (postId: string) => generationAPI.deleteJob(postId),
    onSuccess: () => {
      message.success('포스트가 삭제되었습니다.');
      queryClient.invalidateQueries({ queryKey: ['posts'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '포스트 삭제에 실패했습니다.');
    }
  });

  const getStatusTag = (status: string) => {
    const statusConfig = {
      draft: { color: 'default', text: '초안' },
      published: { color: 'success', text: '발행됨' },
      scheduled: { color: 'processing', text: '예약됨' }
    };

    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.draft;
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  const getPlatformIcon = (platform?: string) => {
    switch (platform) {
      case 'wordpress':
        return <FileImageOutlined style={{ color: '#21759b' }} />;
      case 'blogger':
        return <GoogleOutlined style={{ color: '#ea4335' }} />;
      case 'medium':
        return <FileTextOutlined style={{ color: '#00ab6c' }} />;
      default:
        return <FileTextOutlined />;
    }
  };

  const handlePublish = (post: Post, platform: string) => {
    publishMutation.mutate({ postId: post.id, platform });
  };

  const handleEdit = (post: Post) => {
    setEditingPost(post);
    form.setFieldsValue({
      title: post.title,
      content: post.content,
      summary: post.summary,
      tags: post.tags?.join(', ')
    });
    setIsModalVisible(true);
  };

  const handleDelete = (postId: string) => {
    deleteMutation.mutate(postId);
  };

  const onFinish = (values: any) => {
    // This would typically update the post
    message.info('포스트 수정 기능은 준비 중입니다.');
    setIsModalVisible(false);
  };

  const getActionMenu = (post: Post): MenuProps => ({
    items: [
      {
        key: 'wordpress',
        label: 'WordPress에 발행',
        icon: <FileImageOutlined />,
        onClick: () => handlePublish(post, 'wordpress')
      },
      {
        key: 'blogger',
        label: 'Blogger에 발행',
        icon: <GoogleOutlined />,
        onClick: () => handlePublish(post, 'blogger')
      },
      {
        key: 'export',
        label: 'Markdown 내보내기',
        icon: <ExportOutlined />,
        onClick: () => {
          const element = document.createElement('a');
          const file = new Blob([post.content], { type: 'text/markdown' });
          element.href = URL.createObjectURL(file);
          element.download = `${post.title}.md`;
          document.body.appendChild(element);
          element.click();
          document.body.removeChild(element);
        }
      }
    ]
  });

  const columns = [
    {
      title: '제목',
      dataIndex: 'title',
      key: 'title',
      width: 300,
      render: (title: string, record: Post) => (
        <div>
          <Text strong className="block mb-1">{title || record.content?.title || '제목 없음'}</Text>
          <div className="flex items-center space-x-2">
            {record.platform && getPlatformIcon(record.platform)}
            <Text type="secondary" className="text-xs">
              {record.summary || record.content?.summary || ''}
            </Text>
          </div>
        </div>
      )
    },
    {
      title: '상태',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: string) => getStatusTag(status || 'draft'),
      filters: [
        { text: '초안', value: 'draft' },
        { text: '발행됨', value: 'published' },
        { text: '예약됨', value: 'scheduled' }
      ],
      onFilter: (value: any, record: Post) => (record.status || 'draft') === value
    },
    {
      title: '태그',
      dataIndex: 'tags',
      key: 'tags',
      width: 200,
      render: (tags: string[], record: Post) => {
        const postTags = tags || record.content?.tags || [];
        return (
          <Space wrap>
            {postTags.slice(0, 3).map((tag: string, index: number) => (
              <Tag key={index} color="blue" className="text-xs">
                {tag}
              </Tag>
            ))}
            {postTags.length > 3 && (
              <Tag className="text-xs">+{postTags.length - 3}</Tag>
            )}
          </Space>
        );
      }
    },
    {
      title: '생성일',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (created_at: string) => dayjs(created_at).format('MM-DD HH:mm'),
      sorter: (a: Post, b: Post) => dayjs(a.created_at).unix() - dayjs(b.created_at).unix(),
      defaultSortOrder: 'descend' as const
    },
    {
      title: '통계',
      key: 'stats',
      width: 100,
      render: (_, record: Post) => (
        <div className="text-center">
          <div className="text-xs text-gray-500">
            {record.views !== undefined && (
              <div>조회: {record.views}</div>
            )}
            {record.likes !== undefined && (
              <div>좋아요: {record.likes}</div>
            )}
            {!record.views && !record.likes && (
              <Text type="secondary">-</Text>
            )}
          </div>
        </div>
      )
    },
    {
      title: '작업',
      key: 'actions',
      width: 120,
      render: (_, record: Post) => (
        <Space size="small">
          <Tooltip title="보기">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => window.open(`/jobs/${record.id}`, '_blank')}
            />
          </Tooltip>
          
          <Tooltip title="수정">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>

          <Dropdown menu={getActionMenu(record)} trigger={['click']}>
            <Button type="text" icon={<MoreOutlined />} />
          </Dropdown>

          <Popconfirm
            title="이 포스트를 삭제하시겠습니까?"
            onConfirm={() => handleDelete(record.id)}
            okText="삭제"
            cancelText="취소"
          >
            <Tooltip title="삭제">
              <Button
                type="text"
                icon={<DeleteOutlined />}
                danger
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      )
    }
  ];

  const rowSelection = {
    selectedRowKeys: selectedPosts,
    onChange: (selectedRowKeys: React.Key[]) => {
      setSelectedPosts(selectedRowKeys as string[]);
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <div className="flex justify-between items-start">
          <div>
            <Title level={2}>
              <FileTextOutlined className="mr-2" />
              포스트 관리
            </Title>
            <Text type="secondary">
              생성된 콘텐츠를 관리하고 다양한 플랫폼에 발행하세요.
            </Text>
          </div>

          <Space>
            {selectedPosts.length > 0 && (
              <Button
                icon={<SendOutlined />}
                onClick={() => {
                  // Batch publish functionality
                  message.info('일괄 발행 기능은 준비 중입니다.');
                }}
              >
                선택 항목 발행
              </Button>
            )}
          </Space>
        </div>
      </div>

      <Card>
        <div className="mb-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <Text strong>총 {posts?.length || 0}개의 포스트</Text>
              {selectedPosts.length > 0 && (
                <Text type="secondary">
                  {selectedPosts.length}개 선택됨
                </Text>
              )}
            </div>
            
            <Space>
              <Select
                placeholder="플랫폼 필터"
                allowClear
                style={{ width: 120 }}
              >
                <Option value="wordpress">WordPress</Option>
                <Option value="blogger">Blogger</Option>
                <Option value="medium">Medium</Option>
              </Select>
              
              <Select
                placeholder="상태 필터"
                allowClear
                style={{ width: 120 }}
              >
                <Option value="draft">초안</Option>
                <Option value="published">발행됨</Option>
                <Option value="scheduled">예약됨</Option>
              </Select>
            </Space>
          </div>
        </div>

        <Table<Post>
          columns={columns}
          dataSource={posts || []}
          loading={isLoading}
          rowKey="id"
          rowSelection={rowSelection}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `${range[0]}-${range[1]} / 총 ${total}개`,
          }}
          scroll={{ x: 800 }}
          locale={{
            emptyText: '생성된 포스트가 없습니다'
          }}
        />
      </Card>

      <Modal
        title={editingPost ? "포스트 수정" : "새 포스트"}
        open={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        footer={null}
        width={800}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          className="space-y-4"
        >
          <Form.Item
            label="제목"
            name="title"
            rules={[{ required: true, message: '제목을 입력해주세요!' }]}
          >
            <Input placeholder="포스트 제목" maxLength={200} />
          </Form.Item>

          <Form.Item
            label="요약"
            name="summary"
          >
            <Input.TextArea
              placeholder="포스트 요약 (선택사항)"
              rows={3}
              maxLength={500}
              showCount
            />
          </Form.Item>

          <Form.Item
            label="태그"
            name="tags"
          >
            <Input
              placeholder="태그를 쉼표로 구분하여 입력 (예: AI, 기술, 블로그)"
              maxLength={200}
            />
          </Form.Item>

          <Form.Item
            label="내용"
            name="content"
            rules={[{ required: true, message: '내용을 입력해주세요!' }]}
          >
            <Input.TextArea
              placeholder="포스트 내용 (Markdown 지원)"
              rows={12}
              showCount
            />
          </Form.Item>

          <div className="flex justify-end space-x-2 pt-4">
            <Button onClick={() => setIsModalVisible(false)}>
              취소
            </Button>
            <Button type="primary" htmlType="submit">
              {editingPost ? '수정' : '저장'}
            </Button>
          </div>
        </Form>
      </Modal>
    </div>
  );
};

export default Posts;