import React from 'react'
import { Card, Typography, Form, Input, Switch, Button, Space, message, List, Tag } from 'antd'
import { RocketOutlined, SaveOutlined, ApiOutlined, LinkOutlined } from '@ant-design/icons'

const { Title, Text } = Typography

const AdminIntegrations: React.FC = () => {
  const [form] = Form.useForm()

  const webhooks = [
    { name: 'Content Published', url: 'https://api.company.com/webhook/published', events: ['content.published'] },
    { name: 'User Created', url: 'https://api.company.com/webhook/user', events: ['user.created', 'user.updated'] }
  ]

  const apiTokens = [
    { name: 'Mobile App', scope: ['content.read', 'content.create'], expires: '2024-12-31' },
    { name: 'Analytics Service', scope: ['logs.read'], expires: '2024-06-30' }
  ]

  const handleSave = async (values: any) => {
    try {
      message.success('통합 설정이 저장되었습니다')
    } catch (error) {
      message.error('저장 중 오류가 발생했습니다')
    }
  }

  return (
    <div>
      <Title level={3}>통합 & API</Title>
      <Text type="secondary">외부 시스템과의 연동을 관리합니다</Text>

      <Card title={<Space><LinkOutlined />Webhook 설정</Space>} style={{ marginTop: 24, marginBottom: 24 }}>
        <List
          dataSource={webhooks}
          renderItem={(webhook) => (
            <List.Item
              actions={[<Button key="edit" type="link">편집</Button>]}
            >
              <List.Item.Meta
                title={webhook.name}
                description={
                  <div>
                    <div>{webhook.url}</div>
                    <Space style={{ marginTop: 8 }}>
                      {webhook.events.map(event => (
                        <Tag key={event} color="blue">{event}</Tag>
                      ))}
                    </Space>
                  </div>
                }
              />
            </List.Item>
          )}
        />
      </Card>

      <Card title={<Space><ApiOutlined />API 토큰</Space>} style={{ marginBottom: 24 }}>
        <List
          dataSource={apiTokens}
          renderItem={(token) => (
            <List.Item
              actions={[<Button key="regenerate" type="link">재생성</Button>]}
            >
              <List.Item.Meta
                title={token.name}
                description={
                  <div>
                    <div>만료: {token.expires}</div>
                    <Space style={{ marginTop: 8 }}>
                      {token.scope.map(scope => (
                        <Tag key={scope} color="green">{scope}</Tag>
                      ))}
                    </Space>
                  </div>
                }
              />
            </List.Item>
          )}
        />
      </Card>

      <Form form={form} layout="vertical" onFinish={handleSave}>
        <Card title="SSO/SAML" style={{ marginBottom: 24 }}>
          <Form.Item name="sso_enabled" label="SSO 활성화" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="saml_endpoint" label="SAML 엔드포인트">
            <Input placeholder="https://sso.company.com/saml" />
          </Form.Item>
          <Form.Item name="saml_certificate" label="SAML 인증서">
            <Input.TextArea rows={4} placeholder="-----BEGIN CERTIFICATE-----" />
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

export default AdminIntegrations