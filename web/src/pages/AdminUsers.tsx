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
  Avatar,
  Badge
} from 'antd';
import {
  UserOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CrownOutlined,
  MailOutlined,
  LockOutlined,
  EyeOutlined
} from '@ant-design/icons';
import { generationAPI } from '../services/api';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Option } = Select;

interface User {
  id: string;
  email: string;
  username?: string;
  role: 'admin' | 'user';
  is_active: boolean;
  created_at: string;
  last_login?: string;
  posts_count?: number;
  jobs_count?: number;
}

const AdminUsers: React.FC = () => {
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  const { data: users, isLoading } = useQuery({
    queryKey: ['admin-users'],
    queryFn: () => generationAPI.getUsers(),
    select: (data) => data.data
  });

  const createUserMutation = useMutation({
    mutationFn: (data: any) => generationAPI.createUser(data),
    onSuccess: () => {
      message.success('사용자가 성공적으로 생성되었습니다.');
      setIsModalVisible(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '사용자 생성에 실패했습니다.');
    }
  });

  const updateUserMutation = useMutation({
    mutationFn: ({ userId, data }: { userId: string; data: any }) => 
      generationAPI.updateUser(userId, data),
    onSuccess: () => {
      message.success('사용자 정보가 수정되었습니다.');
      setIsModalVisible(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '사용자 수정에 실패했습니다.');
    }
  });

  const deleteUserMutation = useMutation({
    mutationFn: (userId: string) => generationAPI.deleteUser(userId),
    onSuccess: () => {
      message.success('사용자가 삭제되었습니다.');
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '사용자 삭제에 실패했습니다.');
    }
  });

  const toggleUserStatusMutation = useMutation({
    mutationFn: ({ userId, isActive }: { userId: string; isActive: boolean }) => 
      generationAPI.updateUser(userId, { is_active: isActive }),
    onSuccess: () => {
      message.success('사용자 상태가 변경되었습니다.');
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '상태 변경에 실패했습니다.');
    }
  });

  const handleAddUser = () => {
    setEditingUser(null);
    form.resetFields();
    form.setFieldsValue({
      role: 'user',
      is_active: true
    });
    setIsModalVisible(true);
  };

  const handleEditUser = (user: User) => {
    setEditingUser(user);
    form.setFieldsValue(user);
    setIsModalVisible(true);
  };

  const handleDeleteUser = (userId: string) => {
    deleteUserMutation.mutate(userId);
  };

  const handleToggleStatus = (user: User) => {
    toggleUserStatusMutation.mutate({
      userId: user.id,
      isActive: !user.is_active
    });
  };

  const onFinish = (values: any) => {
    if (editingUser) {
      updateUserMutation.mutate({
        userId: editingUser.id,
        data: values
      });
    } else {
      createUserMutation.mutate(values);
    }
  };

  const getRoleTag = (role: string) => {
    return role === 'admin' ? (
      <Tag color="red" icon={<CrownOutlined />}>관리자</Tag>
    ) : (
      <Tag color="blue">사용자</Tag>
    );
  };

  const getStatusBadge = (isActive: boolean) => {
    return isActive ? (
      <Badge status="success" text="활성" />
    ) : (
      <Badge status="default" text="비활성" />
    );
  };

  const columns = [
    {
      title: '사용자',
      key: 'user',
      width: 250,
      render: (_, record: User) => (
        <div className="flex items-center space-x-3">
          <Avatar size="large" icon={<UserOutlined />} />
          <div>
            <Text strong className="block">
              {record.username || record.email.split('@')[0]}
            </Text>
            <Text type="secondary" className="text-sm">
              {record.email}
            </Text>
          </div>
        </div>
      )
    },
    {
      title: '권한',
      dataIndex: 'role',
      key: 'role',
      width: 120,
      render: (role: string) => getRoleTag(role),
      filters: [
        { text: '관리자', value: 'admin' },
        { text: '사용자', value: 'user' }
      ],
      onFilter: (value: any, record: User) => record.role === value
    },
    {
      title: '상태',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 120,
      render: (isActive: boolean) => getStatusBadge(isActive),
      filters: [
        { text: '활성', value: true },
        { text: '비활성', value: false }
      ],
      onFilter: (value: any, record: User) => record.is_active === value
    },
    {
      title: '통계',
      key: 'stats',
      width: 150,
      render: (_, record: User) => (
        <div className="text-center">
          <div className="text-sm">
            <div>포스트: {record.posts_count || 0}</div>
            <div>작업: {record.jobs_count || 0}</div>
          </div>
        </div>
      )
    },
    {
      title: '가입일',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (created_at: string) => (
        <Tooltip title={dayjs(created_at).format('YYYY-MM-DD HH:mm:ss')}>
          {dayjs(created_at).format('YYYY-MM-DD')}
        </Tooltip>
      ),
      sorter: (a: User, b: User) => dayjs(a.created_at).unix() - dayjs(b.created_at).unix()
    },
    {
      title: '최종 로그인',
      dataIndex: 'last_login',
      key: 'last_login',
      width: 120,
      render: (lastLogin: string) => lastLogin ? (
        <Tooltip title={dayjs(lastLogin).format('YYYY-MM-DD HH:mm:ss')}>
          {dayjs(lastLogin).fromNow()}
        </Tooltip>
      ) : (
        <Text type="secondary">-</Text>
      )
    },
    {
      title: '작업',
      key: 'actions',
      width: 150,
      render: (_, record: User) => (
        <Space size="small">
          <Tooltip title="상세 보기">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => {
                // View user details functionality
                message.info('사용자 상세 보기 기능은 준비 중입니다.');
              }}
            />
          </Tooltip>
          
          <Tooltip title="수정">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => handleEditUser(record)}
            />
          </Tooltip>

          <Tooltip title={record.is_active ? "비활성화" : "활성화"}>
            <Button
              type="text"
              onClick={() => handleToggleStatus(record)}
              style={{ 
                color: record.is_active ? '#faad14' : '#52c41a' 
              }}
            >
              {record.is_active ? '비활성' : '활성'}
            </Button>
          </Tooltip>

          <Popconfirm
            title="이 사용자를 삭제하시겠습니까?"
            description="삭제된 사용자는 복구할 수 없습니다."
            onConfirm={() => handleDeleteUser(record.id)}
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

  const activeUsersCount = users?.filter((user: User) => user.is_active).length || 0;
  const adminUsersCount = users?.filter((user: User) => user.role === 'admin').length || 0;

  return (
    <div className="p-6">
      <div className="mb-6">
        <div className="flex justify-between items-start">
          <div>
            <Title level={2}>
              <UserOutlined className="mr-2" />
              사용자 관리
            </Title>
            <Text type="secondary">
              시스템 사용자를 관리하고 권한을 설정하세요.
            </Text>
          </div>

          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleAddUser}
          >
            사용자 추가
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card size="small" className="text-center">
          <div className="text-2xl font-bold text-blue-600">{users?.length || 0}</div>
          <div className="text-gray-500">전체 사용자</div>
        </Card>
        <Card size="small" className="text-center">
          <div className="text-2xl font-bold text-green-600">{activeUsersCount}</div>
          <div className="text-gray-500">활성 사용자</div>
        </Card>
        <Card size="small" className="text-center">
          <div className="text-2xl font-bold text-red-600">{adminUsersCount}</div>
          <div className="text-gray-500">관리자</div>
        </Card>
        <Card size="small" className="text-center">
          <div className="text-2xl font-bold text-yellow-600">
            {(users?.length || 0) - activeUsersCount}
          </div>
          <div className="text-gray-500">비활성 사용자</div>
        </Card>
      </div>

      <Card>
        <Table<User>
          columns={columns}
          dataSource={users || []}
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
            emptyText: '등록된 사용자가 없습니다'
          }}
        />
      </Card>

      <Modal
        title={editingUser ? "사용자 수정" : "새 사용자 추가"}
        open={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        footer={null}
        width={500}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          className="space-y-4"
        >
          <Form.Item
            label="이메일"
            name="email"
            rules={[
              { required: true, message: '이메일을 입력해주세요!' },
              { type: 'email', message: '올바른 이메일 형식을 입력해주세요!' }
            ]}
          >
            <Input
              prefix={<MailOutlined />}
              placeholder="user@example.com"
              disabled={!!editingUser}
            />
          </Form.Item>

          <Form.Item
            label="사용자명"
            name="username"
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="사용자명 (선택사항)"
              maxLength={50}
            />
          </Form.Item>

          {!editingUser && (
            <Form.Item
              label="비밀번호"
              name="password"
              rules={[
                { required: true, message: '비밀번호를 입력해주세요!' },
                { min: 6, message: '비밀번호는 최소 6자 이상이어야 합니다!' }
              ]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="비밀번호"
              />
            </Form.Item>
          )}

          <div className="grid grid-cols-2 gap-4">
            <Form.Item
              label="권한"
              name="role"
              rules={[{ required: true, message: '권한을 선택해주세요!' }]}
            >
              <Select placeholder="권한 선택">
                <Option value="user">
                  <Space>
                    <UserOutlined />
                    일반 사용자
                  </Space>
                </Option>
                <Option value="admin">
                  <Space>
                    <CrownOutlined />
                    관리자
                  </Space>
                </Option>
              </Select>
            </Form.Item>

            <Form.Item
              label="상태"
              name="is_active"
              rules={[{ required: true, message: '상태를 선택해주세요!' }]}
            >
              <Select placeholder="상태 선택">
                <Option value={true}>활성</Option>
                <Option value={false}>비활성</Option>
              </Select>
            </Form.Item>
          </div>

          <div className="flex justify-end space-x-2 pt-4">
            <Button onClick={() => setIsModalVisible(false)}>
              취소
            </Button>
            <Button
              type="primary"
              htmlType="submit"
              loading={createUserMutation.isPending || updateUserMutation.isPending}
            >
              {editingUser ? '수정' : '생성'}
            </Button>
          </div>
        </Form>
      </Modal>
    </div>
  );
};

export default AdminUsers;