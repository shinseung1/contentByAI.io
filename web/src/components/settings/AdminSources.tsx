import React from 'react'
import { Card, Typography, Form, Input, InputNumber, Switch, Button, Space, message, Select } from 'antd'
import { LinkOutlined, SaveOutlined } from '@ant-design/icons'

const { Title, Text } = Typography

const AdminSources: React.FC = () => {
  const [form] = Form.useForm()

  const handleSave = async (values: any) => {
    try {
      console.log('Saving source settings:', values)
      message.success('소스 연결 설정이 저장되었습니다')
    } catch (error) {
      message.error('저장 중 오류가 발생했습니다')
    }
  }

  return (
    <div>
      <Title level={3}>소스 연결</Title>
      <Text type="secondary">외부 데이터 소스와 연동을 관리합니다</Text>

      <Form form={form} layout="vertical" onFinish={handleSave} style={{ marginTop: 24 }}>
        <Card title="RSS/URL 크롤러" style={{ marginBottom: 24 }}>
          <Form.Item name="crawler_interval" label="크롤링 주기 (시간)">
            <InputNumber min={1} max={168} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="whitelist_domains" label="화이트리스트 도메인">
            <Input.TextArea placeholder="허용할 도메인을 줄바꿈으로 구분하여 입력" rows={4} />
          </Form.Item>
        </Card>

        <Card title="사내 도구 연동" style={{ marginBottom: 24 }}>
          <Form.Item name="notion_enabled" label="Notion 연동" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="google_docs_enabled" label="Google Docs 연동" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="slack_enabled" label="Slack 연동" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Card>

        <Card title="미디어 자산" style={{ marginBottom: 24 }}>
          <Form.Item name="image_policy" label="이미지 정책">
            <Select>
              <Select.Option value="suggest">제안만</Select.Option>
              <Select.Option value="upload">업로드 허용</Select.Option>
              <Select.Option value="stock">스톡 라이선스</Select.Option>
            </Select>
          </Form.Item>
        </Card>

        <Form.Item>
          <Button type="primary" htmlType="submit" icon={<SaveOutlined />} size="large">
            설정 저장
          </Button>
        </Form.Item>
      </Form>
    </div>
  )
}

export default AdminSources