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
  ExperimentOutlined,
  RobotOutlined,
  BulbOutlined,
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
    token: { colorBgContainer, colorText, colorBorder },
  } = theme.useToken()
  
  const darkTheme = {
    colorBgContainer: '#1f1f1f',
    colorBgElevated: '#262626',
    colorText: '#ffffff',
    colorTextSecondary: '#a6a6a6',
    colorBorder: '#434343',
    colorPrimary: '#722ed1',
  }

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
      children: [
        {
          key: '/generation/gemini',
          icon: <ExperimentOutlined />,
          label: 'Gemini',
        },
        {
          key: '/generation/claude',
          icon: <RobotOutlined />,
          label: 'Claude',
        },
        {
          key: '/generation/openai',
          icon: <BulbOutlined />,
          label: 'OpenAI',
        },
      ],
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
    <Layout style={{ minHeight: '100vh', background: darkTheme.colorBgContainer }}>
      <Sider 
        trigger={null} 
        collapsible 
        collapsed={collapsed}
        style={{
          background: '#0a0a0a',
          borderRight: `1px solid ${darkTheme.colorBorder}`,
          boxShadow: '2px 0 8px rgba(0, 0, 0, 0.3)',
        }}
      >
        <div 
          className="demo-logo-vertical" 
          style={{ 
            height: 64, 
            margin: '16px', 
            background: 'linear-gradient(135deg, #722ed1, #1890ff)', 
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontWeight: 'bold',
            fontSize: collapsed ? '16px' : '18px'
          }}
        >
          {collapsed ? 'AI' : 'AI Writer'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => handleMenuClick(key)}
          style={{
            background: 'transparent',
            border: 'none',
          }}
        />
      </Sider>
      <Layout style={{ background: darkTheme.colorBgContainer }}>
        <Header style={{ 
          padding: 0, 
          background: darkTheme.colorBgElevated,
          borderBottom: `1px solid ${darkTheme.colorBorder}`,
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)'
        }}>
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
                style: { 
                  fontSize: '18px', 
                  cursor: 'pointer',
                  color: darkTheme.colorText,
                  padding: '8px',
                  borderRadius: '6px',
                  transition: 'all 0.3s'
                }
              })}
              <h2 style={{ 
                margin: '0 0 0 16px', 
                color: darkTheme.colorText,
                background: 'linear-gradient(135deg, #722ed1, #1890ff)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text'
              }}>
                AI Writer
              </h2>
            </div>
            
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <span style={{ 
                color: darkTheme.colorTextSecondary, 
                fontSize: '14px' 
              }}>
                환영합니다, {user?.username}님
              </span>
              <Dropdown 
                menu={{ items: userMenuItems }} 
                placement="bottomRight"
                arrow
              >
                <Avatar
                  style={{ 
                    backgroundColor: darkTheme.colorPrimary, 
                    cursor: 'pointer',
                    border: `2px solid ${darkTheme.colorBorder}`
                  }}
                  icon={<UserOutlined />}
                />
              </Dropdown>
            </div>
          </div>
        </Header>
        <Content style={{ 
          margin: '24px', 
          padding: '24px', 
          background: darkTheme.colorBgContainer,
          borderRadius: '12px',
          minHeight: '280px'
        }}>
          {children}
        </Content>
      </Layout>
    </Layout>
  )
}

export default MainLayout