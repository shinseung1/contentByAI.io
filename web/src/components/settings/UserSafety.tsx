import React from 'react'
import { Card, Switch, Typography, Button, message, Space, Alert } from 'antd'
import { SafetyOutlined, SaveOutlined } from '@ant-design/icons'

const { Title, Text } = Typography

const UserSafety: React.FC = () => {
  const handleSave = async () => {
    try {
      message.success('안전 설정이 저장되었습니다')
    } catch (error) {
      message.error('저장 중 오류가 발생했습니다')
    }
  }

  return (
    <div>
      <Title level={3}>안전/컴플라이언스</Title>
      <Text type="secondary">개인정보 보호와 콘텐츠 안전성 설정을 관리합니다</Text>

      <Card title="개인정보 보호" style={{ marginTop: 24, marginBottom: 24 }}>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <Text strong>PII 자동 제거</Text>
              <div><Text type="secondary">생성된 콘텐츠에서 개인정보를 자동으로 감지하고 제거합니다</Text></div>
            </div>
            <Switch defaultChecked />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <Text strong>제한 주제 알림</Text>
              <div><Text type="secondary">의료, 투자 등 민감한 주제 사용 시 알림을 받습니다</Text></div>
            </div>
            <Switch defaultChecked />
          </div>
        </Space>
      </Card>

      <Card title="콘텐츠 정책" style={{ marginBottom: 24 }}>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <Text strong>저작권 확인</Text>
              <div><Text type="secondary">콘텐츠 생성 시 저작권 관련 안내를 표시합니다</Text></div>
            </div>
            <Switch defaultChecked />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <Text strong>인용 표기</Text>
              <div><Text type="secondary">참조한 자료의 출처를 자동으로 표기합니다</Text></div>
            </div>
            <Switch defaultChecked />
          </div>
        </Space>
      </Card>

      <Alert
        message="컴플라이언스 정보"
        description="이 설정들은 법적 요구사항과 회사 정책을 준수하기 위한 것입니다. 변경 시 관리자의 승인이 필요할 수 있습니다."
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      <Button type="primary" onClick={handleSave} icon={<SaveOutlined />} size="large">
        안전 설정 저장
      </Button>
    </div>
  )
}

export default UserSafety