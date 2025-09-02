import React, { useState } from 'react'
import { Tabs, Card, Typography, Alert } from 'antd'
import { useAuth } from '../contexts/AuthContext'
import { SettingOutlined, UserOutlined, ApiOutlined, FileTextOutlined, GlobalOutlined, LinkOutlined, SafetyOutlined, CreditCardOutlined, AuditOutlined, RocketOutlined } from '@ant-design/icons'
import AdminDashboard from '../components/settings/AdminDashboard'
import AdminUsers from '../components/settings/AdminUsers'
import AdminModels from '../components/settings/AdminModels'
import AdminWorkflows from '../components/settings/AdminWorkflows'
import AdminSEO from '../components/settings/AdminSEO'
import AdminSources from '../components/settings/AdminSources'
import AdminPolicies from '../components/settings/AdminPolicies'
import AdminBilling from '../components/settings/AdminBilling'
import AdminLogging from '../components/settings/AdminLogging'
import AdminIntegrations from '../components/settings/AdminIntegrations'
import UserProfile from '../components/settings/UserProfile'
import UserDefaults from '../components/settings/UserDefaults'
import UserSources from '../components/settings/UserSources'
import UserSEO from '../components/settings/UserSEO'
import UserSafety from '../components/settings/UserSafety'
import UserLimits from '../components/settings/UserLimits'
import UserTasks from '../components/settings/UserTasks'

const { Title, Text } = Typography

const Settings: React.FC = () => {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState('1')

  const isAdmin = user?.role === 'owner' || user?.role === 'admin'
  const isOwner = user?.role === 'owner'

  const adminTabs = [
    {
      key: '1',
      label: (
        <span>
          <SettingOutlined />
          대시보드
        </span>
      ),
      children: <AdminDashboard />,
    },
    {
      key: '2',
      label: (
        <span>
          <UserOutlined />
          사용자 관리
        </span>
      ),
      children: <AdminUsers />,
    },
    {
      key: '3',
      label: (
        <span>
          <ApiOutlined />
          모델/프로바이더
        </span>
      ),
      children: <AdminModels />,
    },
    {
      key: '4',
      label: (
        <span>
          <FileTextOutlined />
          워크플로우 템플릿
        </span>
      ),
      children: <AdminWorkflows />,
    },
    {
      key: '5',
      label: (
        <span>
          <GlobalOutlined />
          SEO/배포
        </span>
      ),
      children: <AdminSEO />,
    },
    {
      key: '6',
      label: (
        <span>
          <LinkOutlined />
          소스 연결
        </span>
      ),
      children: <AdminSources />,
    },
    {
      key: '7',
      label: (
        <span>
          <SafetyOutlined />
          정책/컴플라이언스
        </span>
      ),
      children: <AdminPolicies />,
    },
    ...(isOwner ? [{
      key: '8',
      label: (
        <span>
          <CreditCardOutlined />
          과금/한도
        </span>
      ),
      children: <AdminBilling />,
    }] : []),
    {
      key: '9',
      label: (
        <span>
          <AuditOutlined />
          로깅/감사
        </span>
      ),
      children: <AdminLogging />,
    },
    {
      key: '10',
      label: (
        <span>
          <RocketOutlined />
          통합 & API
        </span>
      ),
      children: <AdminIntegrations />,
    },
  ]

  const userTabs = [
    {
      key: '1',
      label: (
        <span>
          <UserOutlined />
          내 프로필
        </span>
      ),
      children: <UserProfile />,
    },
    {
      key: '2',
      label: (
        <span>
          <SettingOutlined />
          생성 기본값
        </span>
      ),
      children: <UserDefaults />,
    },
    {
      key: '3',
      label: (
        <span>
          <LinkOutlined />
          인풋 소스
        </span>
      ),
      children: <UserSources />,
    },
    {
      key: '4',
      label: (
        <span>
          <GlobalOutlined />
          SEO/배포 기본값
        </span>
      ),
      children: <UserSEO />,
    },
    {
      key: '5',
      label: (
        <span>
          <SafetyOutlined />
          안전/컴플라이언스
        </span>
      ),
      children: <UserSafety />,
    },
    {
      key: '6',
      label: (
        <span>
          <CreditCardOutlined />
          한도 & 알림
        </span>
      ),
      children: <UserLimits />,
    },
    {
      key: '7',
      label: (
        <span>
          <FileTextOutlined />
          내 작업
        </span>
      ),
      children: <UserTasks />,
    },
  ]

  return (
    <div>
      <div className="page-header">
        <Title level={1}>
          <SettingOutlined /> 설정
        </Title>
        <Text type="secondary">
          {isAdmin ? '시스템 관리 및 사용자 설정' : '개인 설정 및 계정 관리'}
        </Text>
      </div>

      {isAdmin && (
        <Alert
          message={`관리자 권한으로 접속됨 (${user?.role})`}
          description="모든 시스템 설정과 사용자 관리 기능에 접근할 수 있습니다."
          type="info"
          showIcon
          style={{ marginBottom: 24 }}
        />
      )}

      <Card>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={isAdmin ? adminTabs : userTabs}
          tabPosition="left"
          size="large"
          style={{ minHeight: '600px' }}
        />
      </Card>
    </div>
  )
}

export default Settings