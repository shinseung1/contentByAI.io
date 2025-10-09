import React, { useState, useEffect } from 'react'
import { Row, Col, Card, Statistic, List, Badge, Typography, Space, Alert, Spin } from 'antd'
import { TrophyOutlined, ClockCircleOutlined, DollarOutlined, ScheduleOutlined, ExclamationCircleOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons'
import { API_BASE_URL } from '../../services/api'

const { Title, Text } = Typography

interface DashboardStats {
  today_count: number;
  failed_count: number;
  total_cost: number;
  pending_count: number;
  recent_activities: Array<{
    id: string;
    action: string;
    user: string;
    model: string;
    status: string;
    timestamp: string;
  }>;
  alerts: Array<{
    type: string;
    message: string;
    action: string;
  }>;
}

const AdminDashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchDashboardStats()
  }, [])

  const fetchDashboardStats = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await fetch(`${API_BASE_URL}/generation/dashboard/stats`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      if (data.error) {
        throw new Error(data.error)
      }
      setStats(data)
    } catch (err) {
      console.error('Failed to fetch dashboard stats:', err)
      setError(err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다')
      // Set default values on error
      setStats({
        today_count: 0,
        failed_count: 0,
        total_cost: 0,
        pending_count: 0,
        recent_activities: [],
        alerts: []
      })
    } finally {
      setLoading(false)
    }
  }

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
        <div style={{ marginTop: 16 }}>대시보드 데이터를 불러오는 중...</div>
      </div>
    )
  }

  return (
    <div>
      <Title level={3}>시스템 대시보드</Title>
      <Text type="secondary">전체 시스템 상태와 활동을 모니터링합니다</Text>
      
      {error && (
        <Alert
          style={{ marginTop: 16 }}
          message="데이터 로드 오류"
          description={error}
          type="warning"
          showIcon
          action={
            <a onClick={fetchDashboardStats} style={{ fontSize: '12px' }}>
              다시 시도
            </a>
          }
        />
      )}

      <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="오늘 생성 건수"
              value={stats?.today_count || 0}
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
              value={stats?.failed_count || 0}
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
              value={stats?.total_cost || 0}
              prefix={<DollarOutlined />}
              valueStyle={{ color: '#722ed1' }}
              suffix="USD"
              precision={2}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="예약 발행 대기"
              value={stats?.pending_count || 0}
              prefix={<ScheduleOutlined />}
              valueStyle={{ color: '#1890ff' }}
              suffix="건"
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
        <Col span={16}>
          <Card title="최근 활동" extra={<a href="#" onClick={fetchDashboardStats}>새로고침</a>}>
            <List
              itemLayout="horizontal"
              dataSource={stats?.recent_activities || []}
              locale={{
                emptyText: stats?.recent_activities?.length === 0 ? '최근 활동이 없습니다' : '데이터를 불러오는 중...'
              }}
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
                        <Text type="secondary">모델: {item.model}</Text>
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
              {stats?.alerts && stats.alerts.length > 0 ? (
                stats.alerts.map((alert, index) => (
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
                ))
              ) : (
                <Alert
                  message="현재 알림이 없습니다"
                  type="success"
                  showIcon
                  style={{ textAlign: 'center' }}
                />
              )}
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default AdminDashboard