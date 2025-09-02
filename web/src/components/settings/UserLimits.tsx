import React from 'react'
import { Card, Typography, Statistic, Row, Col, Progress, Switch, Form, Select, Button, message } from 'antd'
import { CreditCardOutlined, TrophyOutlined, ClockCircleOutlined, BellOutlined, SaveOutlined } from '@ant-design/icons'

const { Title, Text } = Typography

const UserLimits: React.FC = () => {
  const [form] = Form.useForm()

  const handleSave = async (values: any) => {
    try {
      message.success('알림 설정이 저장되었습니다')
    } catch (error) {
      message.error('저장 중 오류가 발생했습니다')
    }
  }

  return (
    <div>
      <Title level={3}>한도 & 알림</Title>
      <Text type="secondary">내 사용량과 알림 설정을 확인합니다</Text>

      <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="잔여 크레딧"
              value={75000}
              prefix={<TrophyOutlined />}
              suffix="토큰"
              valueStyle={{ color: '#3f8600' }}
            />
            <Progress percent={75} strokeColor="#722ed1" style={{ marginTop: 16 }} />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="월 한도"
              value={100000}
              prefix={<CreditCardOutlined />}
              suffix="토큰"
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="이번 달 사용량"
              value={25000}
              prefix={<ClockCircleOutlined />}
              suffix="토큰"
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      <Card title={<><BellOutlined /> 알림 설정</>} style={{ marginTop: 24 }}>
        <Form form={form} layout="vertical" onFinish={handleSave}>
          <div style={{ marginBottom: 24 }}>
            <Text strong>이메일 알림</Text>
            <div style={{ marginTop: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <div>
                  <Text>작업 완료 알림</Text>
                  <div><Text type="secondary">콘텐츠 생성이 완료되면 이메일로 알림을 받습니다</Text></div>
                </div>
                <Switch defaultChecked />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <div>
                  <Text>작업 실패 알림</Text>
                  <div><Text type="secondary">콘텐츠 생성이 실패하면 이메일로 알림을 받습니다</Text></div>
                </div>
                <Switch defaultChecked />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <div>
                  <Text>한도 임박 알림</Text>
                  <div><Text type="secondary">월 한도의 80%에 도달하면 알림을 받습니다</Text></div>
                </div>
                <Switch defaultChecked />
              </div>
            </div>
          </div>

          <div style={{ marginBottom: 24 }}>
            <Text strong>Slack 알림</Text>
            <Form.Item name="slack_webhook" label="Slack Webhook URL" style={{ marginTop: 16 }}>
              <Input placeholder="https://hooks.slack.com/..." />
            </Form.Item>
            <Form.Item name="slack_channel" label="알림 채널">
              <Input placeholder="#notifications" />
            </Form.Item>
          </div>

          <Form.Item>
            <Button type="primary" htmlType="submit" icon={<SaveOutlined />} size="large">
              알림 설정 저장
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}

export default UserLimits