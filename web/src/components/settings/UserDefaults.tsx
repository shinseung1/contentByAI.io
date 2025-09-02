import React from 'react'
import { Card, Form, Select, Input, Typography, Button, Space, message, Row, Col } from 'antd'
import { SettingOutlined, SaveOutlined } from '@ant-design/icons'

const { Title, Text } = Typography

const UserDefaults: React.FC = () => {
  const [form] = Form.useForm()

  const handleSave = async (values: any) => {
    try {
      console.log('Saving user defaults:', values)
      message.success('생성 기본값이 저장되었습니다')
    } catch (error) {
      message.error('저장 중 오류가 발생했습니다')
    }
  }

  return (
    <div>
      <Title level={3}>생성 기본값</Title>
      <Text type="secondary">콘텐츠 생성 시 사용할 기본 설정을 관리합니다</Text>

      <Form
        form={form}
        layout="vertical"
        onFinish={handleSave}
        style={{ marginTop: 24 }}
        initialValues={{
          goal: 'traffic',
          tone: 'friendly',
          reading_level: 'general',
          length: 'medium',
          word_range: '1200-1500'
        }}
      >
        <Card title="목표 & 톤" style={{ marginBottom: 24 }}>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="goal" label="목적">
                <Select>
                  <Select.Option value="traffic">트래픽 증가</Select.Option>
                  <Select.Option value="leads">리드 생성</Select.Option>
                  <Select.Option value="brand">브랜드 신뢰</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="tone" label="톤">
                <Select>
                  <Select.Option value="friendly">친근한</Select.Option>
                  <Select.Option value="authoritative">권위적</Select.Option>
                  <Select.Option value="playful">유쾌한</Select.Option>
                  <Select.Option value="formal">공식적</Select.Option>
                  <Select.Option value="concise">간결한</Select.Option>
                  <Select.Option value="persuasive">설득적</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="reading_level" label="읽기 수준">
                <Select>
                  <Select.Option value="beginner">초급</Select.Option>
                  <Select.Option value="general">일반</Select.Option>
                  <Select.Option value="expert">전문가</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
        </Card>

        <Card title="길이 & 키워드" style={{ marginBottom: 24 }}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="length" label="길이">
                <Select>
                  <Select.Option value="short">짧음 (300-600자)</Select.Option>
                  <Select.Option value="medium">보통 (600-1200자)</Select.Option>
                  <Select.Option value="long">길음 (1200-2000자)</Select.Option>
                  <Select.Option value="custom">사용자 정의</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="word_range" label="사용자 정의 범위">
                <Input placeholder="예: 1200-1500" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="primary_keyword" label="기본 키워드">
            <Input placeholder="주요 키워드를 입력하세요" />
          </Form.Item>
          <Form.Item name="secondary_keywords" label="보조 키워드">
            <Select mode="tags" placeholder="보조 키워드들을 입력하고 Enter를 누르세요" />
          </Form.Item>
        </Card>

        <Card title="브랜드 가이드" style={{ marginBottom: 24 }}>
          <Form.Item name="required_terms" label="필수 포함 용어">
            <Select mode="tags" placeholder="반드시 포함할 용어들" />
          </Form.Item>
          <Form.Item name="forbidden_terms" label="금지 용어">
            <Select mode="tags" placeholder="사용하지 말아야 할 용어들" />
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

export default UserDefaults