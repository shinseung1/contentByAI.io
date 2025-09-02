import React from 'react'
import { Card, Row, Col, Statistic, List, Typography, Badge } from 'antd'
import { 
  FileTextOutlined, 
  SendOutlined, 
  ClockCircleOutlined, 
  CheckCircleOutlined 
} from '@ant-design/icons'

const { Title } = Typography

const Dashboard: React.FC = () => {
  const stats = [
    {
      title: '총 생성된 번들',
      value: 42,
      icon: <FileTextOutlined />,
      color: '#1890ff',
    },
    {
      title: '발행된 포스트',
      value: 28,
      icon: <SendOutlined />,
      color: '#52c41a',
    },
    {
      title: '예약된 발행',
      value: 8,
      icon: <ClockCircleOutlined />,
      color: '#faad14',
    },
    {
      title: '성공률',
      value: '94%',
      icon: <CheckCircleOutlined />,
      color: '#52c41a',
    },
  ]

  const recentActivities = [
    {
      title: 'WordPress 포스트 발행 완료',
      description: 'AI와 머신러닝의 미래',
      time: '2시간 전',
      status: 'success',
    },
    {
      title: 'Blogger 포스트 예약 등록',
      description: '블록체인 기술의 현재와 전망',
      time: '4시간 전',
      status: 'processing',
    },
    {
      title: '새로운 번들 생성 완료',
      description: '디지털 마케팅 전략',
      time: '6시간 전',
      status: 'success',
    },
    {
      title: '품질 검사 실패',
      description: '클라우드 컴퓨팅 개요',
      time: '8시간 전',
      status: 'error',
    },
  ]

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'success':
        return <Badge status="success" />
      case 'processing':
        return <Badge status="processing" />
      case 'error':
        return <Badge status="error" />
      default:
        return <Badge status="default" />
    }
  }

  return (
    <div>
      <div className="page-header">
        <Title level={1}>대시보드</Title>
      </div>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {stats.map((stat, index) => (
          <Col span={6} key={index}>
            <Card>
              <Statistic
                title={stat.title}
                value={stat.value}
                prefix={stat.icon}
                valueStyle={{ color: stat.color }}
              />
            </Card>
          </Col>
        ))}
      </Row>

      <Row gutter={[16, 16]}>
        <Col span={12}>
          <Card title="최근 활동" extra={<a href="/publishing">전체 보기</a>}>
            <List
              itemLayout="horizontal"
              dataSource={recentActivities}
              renderItem={(item) => (
                <List.Item>
                  <List.Item.Meta
                    avatar={getStatusBadge(item.status)}
                    title={item.title}
                    description={
                      <div>
                        <div>{item.description}</div>
                        <div style={{ color: '#999', fontSize: '12px' }}>
                          {item.time}
                        </div>
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
        
        <Col span={12}>
          <Card title="시스템 상태">
            <List>
              <List.Item>
                <List.Item.Meta
                  avatar={<Badge status="success" />}
                  title="WordPress 연결"
                  description="정상 연결됨"
                />
              </List.Item>
              <List.Item>
                <List.Item.Meta
                  avatar={<Badge status="success" />}
                  title="Google Blogger 연결"
                  description="정상 연결됨"
                />
              </List.Item>
              <List.Item>
                <List.Item.Meta
                  avatar={<Badge status="processing" />}
                  title="AI 서비스"
                  description="응답 시간: 1.2초"
                />
              </List.Item>
            </List>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard