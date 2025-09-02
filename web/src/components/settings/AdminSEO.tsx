import React from 'react'
import { Card, Form, Input, InputNumber, Switch, Typography, Space, Button, message, Select } from 'antd'
import { GlobalOutlined, SaveOutlined } from '@ant-design/icons'

const { Title, Text } = Typography
const { TextArea } = Input

const AdminSEO: React.FC = () => {
  const [form] = Form.useForm()

  const handleSave = async (values: any) => {
    try {
      console.log('Saving SEO settings:', values)
      message.success('SEO 설정이 저장되었습니다')
    } catch (error) {
      message.error('저장 중 오류가 발생했습니다')
    }
  }

  return (
    <div>
      <Title level={3}>SEO/배포 설정</Title>
      <Text type="secondary">SEO 기본값과 배포 채널을 관리합니다</Text>

      <Form
        form={form}
        layout="vertical"
        onFinish={handleSave}
        style={{ marginTop: 24 }}
        initialValues={{
          meta_title_length: 60,
          meta_description_length: 160,
          faq_count: 5,
          og_enabled: true,
          auto_refresh_days: 90
        }}
      >
        <Card title={<Space><GlobalOutlined />SEO 기본값</Space>} style={{ marginBottom: 24 }}>
          <Form.Item name="meta_title_length" label="메타 타이틀 최대 길이">
            <InputNumber min={30} max={100} suffix="글자" style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="meta_description_length" label="메타 디스크립션 최대 길이">
            <InputNumber min={100} max={200} suffix="글자" style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="faq_count" label="FAQ 개수">
            <InputNumber min={3} max={10} suffix="개" style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="og_enabled" label="Open Graph 태그 자동 생성" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Card>

        <Card title="퍼블리시 채널" style={{ marginBottom: 24 }}>
          <Form.Item name="default_channel" label="기본 채널">
            <Select>
              <Select.Option value="wordpress">WordPress</Select.Option>
              <Select.Option value="headless">Headless CMS</Select.Option>
              <Select.Option value="git">Git Export</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="default_category" label="기본 카테고리">
            <Input placeholder="예: 기술 블로그" />
          </Form.Item>
          <Form.Item name="default_tags" label="기본 태그">
            <Select mode="tags" placeholder="태그를 입력하고 Enter를 누르세요" />
          </Form.Item>
        </Card>

        <Card title="스케줄러 설정" style={{ marginBottom: 24 }}>
          <Form.Item name="default_timezone" label="기본 시간대">
            <Select defaultValue="Asia/Seoul">
              <Select.Option value="Asia/Seoul">Asia/Seoul</Select.Option>
              <Select.Option value="UTC">UTC</Select.Option>
              <Select.Option value="America/New_York">America/New_York</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="auto_refresh_days" label="자동 리프레시 주기">
            <InputNumber min={30} max={365} suffix="일" style={{ width: '100%' }} />
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

export default AdminSEO