import React, { useState, useEffect } from 'react'
import { Row, Col, Card, Statistic, List, Badge, Typography, Space, Alert, Spin } from 'antd'
import { TrophyOutlined, ClockCircleOutlined, DollarOutlined, ScheduleOutlined, ExclamationCircleOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons'
import { api, DashboardStats, DashboardActivity, DashboardAlert } from '../../services/api'

const { Title, Text } = Typography

const AdminDashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [activities, setActivities] = useState<DashboardActivity[]>([])
  const [alerts, setAlerts] = useState<DashboardAlert[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setLoading(true)
        const [statsData, activitiesData, alertsData] = await Promise.all([
          api.getDashboardStats(),
          api.getDashboardActivities(5),
          api.getDashboardAlerts()
        ])
        setStats(statsData)
        setActivities(activitiesData)
        setAlerts(alertsData)
        setError(null)
      } catch (err) {
        console.error('Failed to load dashboard data:', err)
        setError(err instanceof Error ? err.message : '데이터를 불러오는데 실패했습니다')
      } finally {
        setLoading(false)
      }
    }

    loadDashboardData()
  }, [])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success': return <CheckCircleOutlined style={{ color: '#52c41a' }} />
      case 'warning': return <ExclamationCircleOutlined style={{ color: '#faad14' }} />
      case 'error': return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
      default: return <ClockCircleOutlined style={{ color: '#1890ff' }} />
    }
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <p style={{ marginTop: 16 }}>대시보드 데이터를 불러오는 중...</p>
      </div>
    )
  }

  if (error) {
    return (
      <Alert
        message="데이터 로드 실패"
        description={error}
        type="error"
        showIcon
      />
    )
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
              value={stats?.today_jobs || 0}
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
              value={stats?.failed_jobs || 0}
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
              value={stats?.estimated_cost || 0}
              precision={2}
              prefix={<DollarOutlined />}
              valueStyle={{ color: '#722ed1' }}
              suffix="USD"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="진행 중 작업"
              value={stats?.in_progress_jobs || 0}
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
              dataSource={activities}
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
                  description={alert.details && alert.details.length > 0 ? (
                    <ul style={{ margin: 0, paddingLeft: '20px' }}>
                      {alert.details.map((detail, idx) => (
                        <li key={idx} style={{ fontSize: '12px' }}>{detail}</li>
                      ))}
                    </ul>
                  ) : undefined}
                  type={alert.type}
                  action={
                    <a href="#" style={{ fontSize: '12px' }}>
                      {alert.action}
                    </a>
                  }
                  closable
                  showIcon
                  style={{ marginBottom: '8px' }}
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