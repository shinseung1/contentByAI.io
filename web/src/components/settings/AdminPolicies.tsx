import React from 'react'
import { Card, Form, Input, Switch, Typography, Button, message, Space } from 'antd'
import { SafetyOutlined, SaveOutlined } from '@ant-design/icons'

const { Title, Text } = Typography

const AdminPolicies: React.FC = () => {
  const [form] = Form.useForm()

  const handleSave = async (values: any) => {
    try {
      message.success('정책 설정이 저장되었습니다')
    } catch (error) {
      message.error('저장 중 오류가 발생했습니다')
    }
  }

  return (
    <div>
      <Title level={3}>정책/컴플라이언스</Title>
      <Text type="secondary">브랜드 가이드와 안전성 정책을 관리합니다</Text>

      <Form form={form} layout="vertical" onFinish={handleSave} style={{ marginTop: 24 }}>
        <Card title="브랜드 가이드" style={{ marginBottom: 24 }}>
          <Form.Item name="required_terms" label="필수 포함 용어">
            <Input.TextArea placeholder="반드시 포함되어야 할 용어들을 쉼표로 구분" rows={3} />
          </Form.Item>
          <Form.Item name="forbidden_terms" label="금지 용어">
            <Input.TextArea placeholder="사용하면 안 되는 용어들을 쉼표로 구분" rows={3} />
          </Form.Item>
        </Card>

        <Card title="안전성 정책" style={{ marginBottom: 24 }}>
          <Form.Item name="pii_removal" label="개인정보 자동 제거" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="sensitive_topics" label="민감 주제 차단" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="fact_check_required" label="사실 검증 필수" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Card>

        <Form.Item>
          <Button type="primary" htmlType="submit" icon={<SaveOutlined />} size="large">
            정책 저장
          </Button>
        </Form.Item>
      </Form>
    </div>
  )
}

export default AdminPolicies