import React, { useState, useEffect } from 'react'
import { Table, Card, Button, Tag, Space, Drawer, Form, Input, Select, DatePicker, Switch, message, Badge, Avatar, Dropdown, Spin } from 'antd'
import { UserOutlined, EditOutlined, DeleteOutlined, PlusOutlined, MoreOutlined, KeyOutlined } from '@ant-design/icons'
import { Typography } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { API_BASE_URL } from '../../services/api'

const { Title, Text } = Typography

interface User {
  id: number
  username: string
  email: string
  role: string
  is_active: boolean
  expires_at: string
  last_seen_at: string
  monthly_token_limit: number
  monthly_cost_cap: number
  mfa_enabled: boolean
  created_at: string
  last_login?: string
}

const AdminUsers: React.FC = () => {
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [drawerVisible, setDrawerVisible] = useState(false)
  const [form] = Form.useForm()
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    fetchUsers()
  }, [])

  const fetchUsers = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_BASE_URL}/users/`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      setUsers(data)
    } catch (error) {
      console.error('Failed to fetch users:', error)
      message.error('사용자 목록을 불러오는데 실패했습니다')
    } finally {
      setLoading(false)
    }
  }

  const columns: ColumnsType<User> = [
    {
      title: '사용자',
      dataIndex: 'username',
      key: 'username',
      render: (username, record) => (
        <Space>
          <Avatar icon={<UserOutlined />} />
          <div>
            <div style={{ fontWeight: 500 }}>{username}</div>
            <Text type="secondary" style={{ fontSize: '12px' }}>{record.email}</Text>
          </div>
        </Space>
      ),
    },
    {
      title: '롤',
      dataIndex: 'role',
      key: 'role',
      render: (role) => {
        const colors = {
          owner: 'purple',
          admin: 'blue',
          editor: 'green',
          viewer: 'orange',
          service: 'gray'
        }
        return <Tag color={colors[role as keyof typeof colors]}>{role}</Tag>
      },
    },
    {
      title: '상태',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (is_active) => (
        <Badge 
          status={is_active ? 'success' : 'error'} 
          text={is_active ? '활성' : '비활성'} 
        />
      ),
    },
    {
      title: '만료일',
      dataIndex: 'expires_at',
      key: 'expires_at',
      render: (date) => <Text>{date}</Text>,
    },
    {
      title: '마지막 접속',
      dataIndex: 'last_seen_at',
      key: 'last_seen_at',
      render: (time) => <Text type="secondary">{time}</Text>,
    },
    {
      title: '작업',
      key: 'actions',
      render: (_, record) => (
        <Dropdown
          menu={{
            items: [
              {
                key: 'edit',
                icon: <EditOutlined />,
                label: '편집',
                onClick: () => handleEditUser(record)
              },
              {
                key: 'reset-password',
                icon: <KeyOutlined />,
                label: '비밀번호 재설정',
                onClick: () => handleResetPassword(record.id)
              },
              {
                type: 'divider'
              },
              {
                key: 'delete',
                icon: <DeleteOutlined />,
                label: '삭제',
                danger: true,
                onClick: () => handleDeleteUser(record.id)
              }
            ]
          }}
          trigger={['click']}
        >
          <Button icon={<MoreOutlined />} />
        </Dropdown>
      ),
    },
  ]

  const handleEditUser = (user: User) => {
    setSelectedUser(user)
    form.setFieldsValue(user)
    setDrawerVisible(true)
  }

  const handleSaveUser = async (values: any) => {
    try {
      setSubmitting(true)
      
      const userData = {
        username: values.username || values.name,
        email: values.email,
        role: values.role,
        expires_at: values.expires_at ? values.expires_at.format('YYYY-MM-DD') : null,
        monthly_token_limit: values.monthly_token_limit || 100000,
        monthly_cost_cap: values.monthly_cost_cap || 50.0,
        ...(selectedUser ? {} : { password: values.password || 'temp123!' })
      }
      
      let response
      if (selectedUser) {
        // Update existing user
        response = await fetch(`${API_BASE_URL}/users/${selectedUser.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(userData)
        })
      } else {
        // Create new user
        response = await fetch(`${API_BASE_URL}/users/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(userData)
        })
      }
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to save user')
      }
      
      message.success(`사용자가 ${selectedUser ? '수정' : '생성'}되었습니다`)
      setDrawerVisible(false)
      form.resetFields()
      fetchUsers() // Refresh the list
    } catch (error) {
      console.error('Save user error:', error)
      message.error(`저장 중 오류가 발생했습니다: ${error.message}`)
    } finally {
      setSubmitting(false)
    }
  }

  const handleResetPassword = async (userId: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/users/${userId}/reset-password`, {
        method: 'POST'
      })
      
      if (!response.ok) {
        throw new Error('Failed to reset password')
      }
      
      const result = await response.json()
      message.success(`비밀번호가 재설정되었습니다. 임시 비밀번호: ${result.temporary_password}`)
    } catch (error) {
      console.error('Reset password error:', error)
      message.error('비밀번호 재설정에 실패했습니다')
    }
  }

  const handleDeleteUser = async (userId: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/users/${userId}`, {
        method: 'DELETE'
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to delete user')
      }
      
      message.success('사용자가 삭제되었습니다')
      fetchUsers() // Refresh the list
    } catch (error) {
      console.error('Delete user error:', error)
      message.error(`삭제 중 오류가 발생했습니다: ${error.message}`)
    }
  }

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <Title level={3}>사용자 관리</Title>
          <Text type="secondary">시스템 사용자 계정을 관리합니다</Text>
        </div>
        <Button 
          type="primary" 
          icon={<PlusOutlined />}
          onClick={() => {
            setSelectedUser(null)
            form.resetFields()
            setDrawerVisible(true)
          }}
        >
          사용자 추가
        </Button>
      </div>

      <Card>
        <Spin spinning={loading}>
          <Table
            columns={columns}
            dataSource={users}
            rowKey="id"
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total) => `총 ${total}명의 사용자`
            }}
          />
        </Spin>
      </Card>

      <Drawer
        title={selectedUser ? '사용자 편집' : '새 사용자 추가'}
        width={600}
        open={drawerVisible}
        onClose={() => setDrawerVisible(false)}
        extra={
          <Space>
            <Button onClick={() => setDrawerVisible(false)}>취소</Button>
            <Button type="primary" loading={submitting} onClick={() => form.submit()}>
              저장
            </Button>
          </Space>
        }
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSaveUser}
        >
          <div style={{ marginBottom: 24 }}>
            <Title level={4}>기본정보</Title>
            <Form.Item name="username" label="사용자명" rules={[{ required: true }]}>
              <Input />
            </Form.Item>
            {!selectedUser && (
              <Form.Item name="password" label="비밀번호" rules={[{ required: true, min: 6 }]}>
                <Input.Password />
              </Form.Item>
            )}
            <Form.Item name="email" label="이메일" rules={[{ required: true, type: 'email' }]}>
              <Input />
            </Form.Item>
            <Form.Item name="role" label="역할" rules={[{ required: true }]}>
              <Select>
                <Select.Option value="owner">Owner</Select.Option>
                <Select.Option value="admin">Admin</Select.Option>
                <Select.Option value="editor">Editor</Select.Option>
                <Select.Option value="viewer">Viewer</Select.Option>
                <Select.Option value="service">Service</Select.Option>
              </Select>
            </Form.Item>
          </div>

          <div style={{ marginBottom: 24 }}>
            <Title level={4}>유효기간</Title>
            <Form.Item name="expires_at" label="만료일">
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="auto_renew" label="자동연장" valuePropName="checked">
              <Switch />
            </Form.Item>
          </div>

          <div style={{ marginBottom: 24 }}>
            <Title level={4}>크레딧/한도</Title>
            <Form.Item name="monthly_token_limit" label="월 토큰 한도">
              <Input type="number" suffix="토큰" />
            </Form.Item>
            <Form.Item name="monthly_cost_cap" label="월 비용 상한">
              <Input type="number" suffix="USD" />
            </Form.Item>
          </div>

          <div>
            <Title level={4}>보안</Title>
            <Form.Item name="mfa_enabled" label="2단계 인증" valuePropName="checked">
              <Switch />
            </Form.Item>
            <Space>
              <Button icon={<KeyOutlined />}>비밀번호 재설정 링크 발급</Button>
            </Space>
          </div>
        </Form>
      </Drawer>
    </div>
  )
}

export default AdminUsers