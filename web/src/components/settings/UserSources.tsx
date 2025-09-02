import React from 'react'
import { Card, Form, Input, Button, Typography, Upload, message, Switch, InputNumber } from 'antd'
import { LinkOutlined, SaveOutlined, UploadOutlined } from '@ant-design/icons'

const { Title, Text } = Typography

const UserSources: React.FC = () => {
  const [form] = Form.useForm()

  const handleSave = async (values: any) => {
    try {
      message.success('인풋 소스 설정이 저장되었습니다')
    } catch (error) {
      message.error('저장 중 오류가 발생했습니다')
    }
  }

  return (
    <div>
      <Title level={3}>인풋 소스</Title>
      <Text type="secondary">콘텐츠 생성을 위한 입력 소스를 관리합니다</Text>

      <Form form={form} layout="vertical" onFinish={handleSave} style={{ marginTop: 24 }}>
        <Card title="RSS/URL 등록" style={{ marginBottom: 24 }}>
          <Form.Item name="rss_urls" label="RSS 피드 URL">
            <Input.TextArea placeholder="RSS URL들을 줄바꿈으로 구분하여 입력" rows={4} />
          </Form.Item>
          <Form.Item name="crawl_interval" label="크롤링 주기 (시간)">
            <InputNumber min={1} max={24} style={{ width: '100%' }} />
          </Form.Item>
        </Card>

        <Card title="파일 업로드" style={{ marginBottom: 24 }}>
          <Form.Item name="file_upload" label="문서 파일">
            <Upload.Dragger>
              <p><UploadOutlined style={{ fontSize: '48px', color: '#722ed1' }} /></p>
              <p>클릭하거나 파일을 여기로 드래그하세요</p>
              <p style={{ color: '#a6a6a6' }}>MD, DOCX 파일만 지원</p>
            </Upload.Dragger>
          </Form.Item>
        </Card>

        <Card title="사실확인 레퍼런스" style={{ marginBottom: 24 }}>
          <Form.Item name="reference_whitelist" label="신뢰할 수 있는 출처 URL">
            <Input.TextArea placeholder="신뢰할 수 있는 웹사이트 URL들을 줄바꿈으로 구분" rows={4} />
          </Form.Item>
        </Card>

        <Form.Item>
          <Button type="primary" htmlType="submit" icon={<SaveOutlined />} size="large">
            설정 저장
          </Button>
        </Form.Item>
      </Form>
    </div>
  )
}

export default UserSources