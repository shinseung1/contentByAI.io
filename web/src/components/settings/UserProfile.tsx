import React from 'react'
import { Card, Form, Input, Button, Avatar, Upload, Typography, Space, message, Switch, Select } from 'antd'
import { UserOutlined, UploadOutlined, SaveOutlined, KeyOutlined } from '@ant-design/icons'
import { useAuth } from '../../contexts/AuthContext'

const { Title, Text } = Typography

const UserProfile: React.FC = () => {
  const { user } = useAuth()
  const [form] = Form.useForm()

  const handleSave = async (values: any) => {
    try {
      console.log('Saving profile:', values)
      message.success('프로필이 저장되었습니다')
    } catch (error) {
      message.error('저장 중 오류가 발생했습니다')
    }
  }

  const handlePasswordChange = async (values: any) => {
    try {
      console.log('Changing password:', values)
      message.success('비밀번호가 변경되었습니다')
    } catch (error) {
      message.error('비밀번호 변경 중 오류가 발생했습니다')
    }
  }

  return (
    <div>
      <Title level={3}>내 프로필</Title>
      <Text type="secondary">개인 정보와 계정 설정을 관리합니다</Text>

      <Card title="기본 정보" style={{ marginTop: 24, marginBottom: 24 }}>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSave}
          initialValues={{
            name: user?.username,
            email: user?.email,
            language: 'ko',
            timezone: 'Asia/Seoul'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: 24 }}>
            <Avatar size={80} icon={<UserOutlined />} style={{ marginRight: 16 }} />
            <div>
              <Upload>
                <Button icon={<UploadOutlined />}>프로필 이미지 변경</Button>
              </Upload>
              <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
                JPG, PNG 파일만 지원 (최대 2MB)
              </Text>
            </div>
          </div>

          <Form.Item name="name" label="이름" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="email" label="이메일" rules={[{ required: true, type: 'email' }]}>
            <Input disabled />
          </Form.Item>
          <Form.Item name="language" label="언어">
            <Select>
              <Select.Option value="ko">한국어</Select.Option>
              <Select.Option value="en">English</Select.Option>
              <Select.Option value="ja">日本語</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="timezone" label="시간대">
            <Select>
              <Select.Option value="Asia/Seoul">Asia/Seoul</Select.Option>
              <Select.Option value="UTC">UTC</Select.Option>
              <Select.Option value="America/New_York">America/New_York</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" icon={<SaveOutlined />}>
              프로필 저장
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Card title="보안 설정">
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <Title level={4}>비밀번호 변경</Title>
            <Form layout="vertical" onFinish={handlePasswordChange}>
              <Form.Item name="current_password" label="현재 비밀번호" rules={[{ required: true }]}>
                <Input.Password />
              </Form.Item>
              <Form.Item name="new_password" label="새 비밀번호" rules={[{ required: true, min: 8 }]}>
                <Input.Password />
              </Form.Item>
              <Form.Item name="confirm_password" label="비밀번호 확인" rules={[{ required: true }]}>
                <Input.Password />
              </Form.Item>
              <Form.Item>
                <Button type="primary" htmlType="submit" icon={<KeyOutlined />}>
                  비밀번호 변경
                </Button>
              </Form.Item>
            </Form>
          </div>

          <div>
            <Title level={4}>2단계 인증</Title>
            <Space>
              <Switch defaultChecked={false} />
              <Text>2단계 인증 활성화</Text>
            </Space>
            <div style={{ marginTop: 8 }}>
              <Text type="secondary">
                보안을 강화하기 위해 2단계 인증을 활성화하는 것을 권장합니다.
              </Text>
            </div>
          </div>
        </Space>
      </Card>
    </div>
  )
}

export default UserProfile