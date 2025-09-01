import React, { useState } from 'react'
import { Layout, Menu, theme, Button, Avatar, Dropdown } from 'antd'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import {
  DashboardOutlined,
  EditOutlined,
  FolderOutlined,
  SendOutlined,
  SettingOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  UserOutlined,
  LogoutOutlined,
} from '@ant-design/icons'

const { Header, Sider, Content } = Layout

interface MainLayoutProps {
  children: React.ReactNode
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const {
    token: { colorBgContainer },
  } = theme.useToken()

  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: '대시보드',
    },
    {
      key: '/generation',
      icon: <EditOutlined />,
      label: '콘텐츠 생성',
    },
    {
      key: '/bundles',
      icon: <FolderOutlined />,
      label: '번들 관리',
    },
    {
      key: '/publishing',
      icon: <SendOutlined />,
      label: '발행 관리',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: '설정',
    },
  ]

  const handleMenuClick = (key: string) => {
    navigate(key)
  }

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: `${user?.username} (${user?.role})`,
      disabled: true,
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '로그아웃',
      onClick: logout,
    },
  ]

  return (
    <Layout>
      <Sider trigger={null} collapsible collapsed={collapsed}>
        <div className="demo-logo-vertical" />
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => handleMenuClick(key)}
        />
      </Sider>
      <Layout>
        <Header style={{ padding: 0, background: colorBgContainer }}>
          <div style={{ 
            padding: '0 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              {React.createElement(collapsed ? MenuUnfoldOutlined : MenuFoldOutlined, {
                className: 'trigger',
                onClick: () => setCollapsed(!collapsed),
                style: { fontSize: '18px', cursor: 'pointer' }
              })}
              <h2 style={{ margin: '0 0 0 16px' }}>AI Writer</h2>
            </div>
            
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <span style={{ color: '#666', fontSize: '14px' }}>
                환영합니다, {user?.username}님
              </span>
              <Dropdown 
                menu={{ items: userMenuItems }} 
                placement="bottomRight"
                arrow
              >
                <Avatar
                  style={{ 
                    backgroundColor: '#1890ff', 
                    cursor: 'pointer'
                  }}
                  icon={<UserOutlined />}
                />
              </Dropdown>
            </div>
          </div>
        </Header>
        <Content style={{ margin: '24px 16px', padding: 24, background: colorBgContainer }}>
          {children}
        </Content>
      </Layout>
    </Layout>
  )
}

export default MainLayout