import React from 'react'
import { Card, Form, Input, Select, Typography, Button, message, TimePicker, Switch } from 'antd'
import { GlobalOutlined, SaveOutlined } from '@ant-design/icons'

const { Title, Text } = Typography

const UserSEO: React.FC = () => {
  const [form] = Form.useForm()

  const handleSave = async (values: any) => {
    try {
      message.success('SEO/배포 기본값이 저장되었습니다')
    } catch (error) {
      message.error('저장 중 오류가 발생했습니다')
    }
  }

  return (
    <div>
      <Title level={3}>SEO/배포 기본값</Title>
      <Text type="secondary">SEO 최적화와 배포 설정의 기본값을 관리합니다</Text>

      <Form form={form} layout="vertical" onFinish={handleSave} style={{ marginTop: 24 }}>
        <Card title="메타 태그 템플릿" style={{ marginBottom: 24 }}>
          <Form.Item name="meta_title_template" label="메타 타이틀 템플릿">
            <Input placeholder="예: {title} | 회사명" />
          </Form.Item>
          <Form.Item name="meta_description_template" label="메타 디스크립션 템플릿">
            <Input.TextArea placeholder="예: {summary} - 더 자세한 내용은 블로그에서 확인하세요." rows={3} />
          </Form.Item>
        </Card>

        <Card title="Open Graph 설정" style={{ marginBottom: 24 }}>
          <Form.Item name="og_image_default" label="기본 OG 이미지 URL">
            <Input placeholder="https://example.com/default-og-image.jpg" />
          </Form.Item>
          <Form.Item name="og_site_name" label="사이트 이름">
            <Input placeholder="회사명 또는 사이트명" />
          </Form.Item>
        </Card>

        <Card title="배포 설정" style={{ marginBottom: 24 }}>
          <Form.Item name="default_channel" label="기본 채널">
            <Select>
              <Select.Option value="blog">블로그</Select.Option>
              <Select.Option value="social">소셜 미디어</Select.Option>
              <Select.Option value="newsletter">뉴스레터</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="default_category" label="기본 카테고리">
            <Input placeholder="예: 기술" />
          </Form.Item>
          <Form.Item name="default_tags" label="기본 태그">
            <Select mode="tags" placeholder="기본으로 사용할 태그들" />
          </Form.Item>
        </Card>

        <Card title="예약 발행" style={{ marginBottom: 24 }}>
          <Form.Item name="default_publish_time" label="기본 발행 시간">
            <TimePicker style={{ width: '100%' }} format="HH:mm" />
          </Form.Item>
          <Form.Item name="auto_refresh_enabled" label="자동 리프레시 활성화" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Card>

        <Form.Item>
          <Button type="primary" htmlType="submit" icon={<SaveOutlined />} size="large">
            기본값 저장
          </Button>
        </Form.Item>
      </Form>
    </div>
  )
}

export default UserSEO