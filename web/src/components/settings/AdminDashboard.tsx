import React from 'react'
import { Row, Col, Card, Statistic, List, Badge, Typography, Space, Alert } from 'antd'
import { TrophyOutlined, ClockCircleOutlined, DollarOutlined, ScheduleOutlined, ExclamationCircleOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons'

const { Title, Text } = Typography

const AdminDashboard: React.FC = () => {
  const recentActivities = [
    { id: 1, action: '콘텐츠 생성 완료', user: 'user1', model: 'GPT-4', status: 'success', timestamp: '2분 전' },
    { id: 2, action: '사용자 계정 생성', user: 'admin', target: 'newuser@company.com', status: 'success', timestamp: '15분 전' },
    { id: 3, action: 'API 키 갱신', user: 'admin', provider: 'OpenAI', status: 'warning', timestamp: '1시간 전' },
    { id: 4, action: '워크플로우 배포', user: 'editor1', workflow: 'SEO 최적화', status: 'success', timestamp: '2시간 전' },
    { id: 5, action: '토큰 한도 초과', user: 'user2', model: 'Claude', status: 'error', timestamp: '3시간 전' },
  ]

  const alerts = [
    { type: 'warning', message: 'OpenAI API 키가 7일 후 만료됩니다', action: '키 갱신' },
    { type: 'info', message: '3명의 사용자가 토큰 한도 80%에 도달했습니다', action: '한도 조정' },
    { type: 'error', message: 'WordPress 연동에서 2건의 발행 실패가 발생했습니다', action: '연동 확인' },
  ]

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success': return <CheckCircleOutlined style={{ color: '#52c41a' }} />
      case 'warning': return <ExclamationCircleOutlined style={{ color: '#faad14' }} />
      case 'error': return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
      default: return <ClockCircleOutlined style={{ color: '#1890ff' }} />
    }
  }

  return (
    <div>
      <Title level={3}>시스템 대시보드</Title>
      <Text type="secondary">전체 시스템 상태와 활동을 모니터링합니다</Text>

      <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="오늘 생성 건수"
              value={127}
              prefix={<TrophyOutlined />}
              valueStyle={{ color: '#3f8600' }}
              suffix="건"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="실패/재시도"
              value={8}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#cf1322' }}
              suffix="건"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="토큰/비용"
              value={2847.50}
              prefix={<DollarOutlined />}
              valueStyle={{ color: '#722ed1' }}
              suffix="USD"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="예약 발행 대기"
              value={15}
              prefix={<ScheduleOutlined />}
              valueStyle={{ color: '#1890ff' }}
              suffix="건"
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
        <Col span={16}>
          <Card title="최근 활동" extra={<a href="#">전체 로그 보기</a>}>
            <List
              itemLayout="horizontal"
              dataSource={recentActivities}
              renderItem={(item) => (
                <List.Item>
                  <List.Item.Meta
                    avatar={getStatusIcon(item.status)}
                    title={
                      <Space>
                        <span>{item.action}</span>
                        <Badge 
                          status={item.status === 'success' ? 'success' : item.status === 'warning' ? 'processing' : 'error'} 
                        />
                      </Space>
                    }
                    description={
                      <Space>
                        <Text type="secondary">사용자: {item.user}</Text>
                        {item.model && <Text type="secondary">모델: {item.model}</Text>}
                        {item.target && <Text type="secondary">대상: {item.target}</Text>}
                        {item.provider && <Text type="secondary">제공업체: {item.provider}</Text>}
                        {item.workflow && <Text type="secondary">워크플로우: {item.workflow}</Text>}
                        <Text type="secondary">{item.timestamp}</Text>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card title="알림 센터">
            <Space direction="vertical" style={{ width: '100%' }}>
              {alerts.map((alert, index) => (
                <Alert
                  key={index}
                  message={alert.message}
                  type={alert.type as any}
                  action={
                    <a href="#" style={{ fontSize: '12px' }}>
                      {alert.action}
                    </a>
                  }
                  closable
                  showIcon
                />
              ))}
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default AdminDashboard