import React from 'react'
import { Typography } from 'antd'

const { Title } = Typography

const Bundles: React.FC = () => {
  return (
    <div>
      <div className="page-header">
        <Title level={1}>번들 관리</Title>
      </div>
      <div>번들 관리 페이지 (개발 예정)</div>
    </div>
  )
}

export default Bundles