import React from 'react'
import { Typography } from 'antd'

const { Title } = Typography

const Settings: React.FC = () => {
  return (
    <div>
      <div className="page-header">
        <Title level={1}>설정</Title>
      </div>
      <div>설정 페이지 (개발 예정)</div>
    </div>
  )
}

export default Settings