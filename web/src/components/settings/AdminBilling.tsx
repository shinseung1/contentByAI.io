import React from 'react'
import { Card, Table, Typography, Tag, Space, Statistic, Row, Col } from 'antd'
import { CreditCardOutlined, DollarOutlined, TrophyOutlined } from '@ant-design/icons'

const { Title, Text } = Typography

const AdminBilling: React.FC = () => {
  const billingData = [
    { month: '2024-01', usage: 450.30, limit: 1000, users: 12 },
    { month: '2023-12', usage: 380.50, limit: 1000, users: 10 },
    { month: '2023-11', usage: 520.80, limit: 1000, users: 11 }
  ]

  const columns = [
    { title: '기간', dataIndex: 'month', key: 'month' },
    { title: '사용량 (USD)', dataIndex: 'usage', key: 'usage', render: (value: number) => `$${value}` },
    { title: '한도 (USD)', dataIndex: 'limit', key: 'limit', render: (value: number) => `$${value}` },
    { title: '활성 사용자', dataIndex: 'users', key: 'users', render: (value: number) => `${value}명` }
  ]

  return (
    <div>
      <Title level={3}>과금/한도 관리</Title>
      <Text type="secondary">결제 정보와 사용량 한도를 관리합니다</Text>

      <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="이번 달 사용량"
              value={450.30}
              prefix={<DollarOutlined />}
              suffix="USD"
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="월 한도"
              value={1000}
              prefix={<TrophyOutlined />}
              suffix="USD"
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="한도 사용률"
              value={45.03}
              suffix="%"
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
      </Row>

      <Card title="과금 이력" style={{ marginTop: 24 }}>
        <Table
          columns={columns}
          dataSource={billingData}
          rowKey="month"
          size="middle"
        />
      </Card>
    </div>
  )
}

export default AdminBilling