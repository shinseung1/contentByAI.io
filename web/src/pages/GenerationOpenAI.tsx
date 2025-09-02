import React from 'react'
import { Card, Form, Input, Button, Select, InputNumber, Switch, Typography, Space, message, Row, Col, Statistic } from 'antd'
import { BulbOutlined, SendOutlined, FireOutlined, GlobalOutlined } from '@ant-design/icons'

const { Title, Text } = Typography
const { TextArea } = Input

const GenerationOpenAI: React.FC = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = React.useState(false)

  const handleGenerate = async (values: any) => {
    setLoading(true)
    try {
      console.log('OpenAI generation request:', values)
      message.success('OpenAI 콘텐츠 생성 요청이 시작되었습니다!')
    } catch (error) {
      message.error('콘텐츠 생성 중 오류가 발생했습니다.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="page-header">
        <Title level={1}>
          <BulbOutlined /> OpenAI 콘텐츠 생성
        </Title>
        <Text type="secondary">OpenAI의 GPT 모델을 사용하여 창의적인 콘텐츠를 생성합니다</Text>
      </div>

      <Row gutter={[24, 24]}>
        <Col span={8}>
          <Card>
            <Statistic
              title="모델"
              value="GPT-4 Turbo"
              prefix={<FireOutlined />}
              valueStyle={{ color: '#10a37f' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="창의성"
              value="높음"
              prefix={<BulbOutlined />}
              valueStyle={{ color: '#ff6900' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="글로벌 지원"
              value="전세계"
              prefix={<GlobalOutlined />}
              valueStyle={{ color: '#0969da' }}
            />
          </Card>
        </Col>
      </Row>

      <Card 
        title={
          <Space>
            <BulbOutlined style={{ color: '#10a37f' }} />
            새로운 콘텐츠 생성
          </Space>
        }
        style={{ marginTop: 24 }}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleGenerate}
          initialValues={{
            provider: 'openai',
            tone: 'professional',
            word_count: 800,
            include_images: true,
            target_language: 'ko',
          }}
        >
          <Form.Item name="provider" hidden>
            <Input value="openai" />
          </Form.Item>

          <Form.Item
            name="topic"
            label="주제"
            rules={[
              { required: true, message: '주제를 입력해주세요.' },
              { min: 10, message: '주제는 최소 10자 이상이어야 합니다.' },
            ]}
          >
            <TextArea
              rows={3}
              placeholder="OpenAI GPT로 생성할 콘텐츠의 주제를 구체적으로 입력해주세요. 예: 'ChatGPT와 GPT-4의 창의적 글쓰기 활용법과 실무 적용 사례'"
            />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="tone" label="톤 앤 매너">
                <Select>
                  <Select.Option value="professional">전문적</Select.Option>
                  <Select.Option value="casual">캐주얼</Select.Option>
                  <Select.Option value="friendly">친근한</Select.Option>
                  <Select.Option value="academic">학술적</Select.Option>
                  <Select.Option value="conversational">대화형</Select.Option>
                  <Select.Option value="creative">창의적</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="word_count" label="목표 단어 수">
                <InputNumber
                  min={300}
                  max={3000}
                  step={100}
                  style={{ width: '100%' }}
                  placeholder="800"
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="target_language" label="언어">
                <Select>
                  <Select.Option value="ko">한국어</Select.Option>
                  <Select.Option value="en">영어</Select.Option>
                  <Select.Option value="ja">일본어</Select.Option>
                  <Select.Option value="zh">중국어</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="include_images" label="이미지 포함" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item style={{ marginTop: 32 }}>
            <Space size="large">
              <Button
                type="primary"
                htmlType="submit"
                icon={<SendOutlined />}
                loading={loading}
                size="large"
                style={{ 
                  background: 'linear-gradient(135deg, #10a37f, #0969da)',
                  border: 'none',
                  minWidth: '200px'
                }}
              >
                OpenAI로 생성 시작
              </Button>
              <Button size="large" onClick={() => form.resetFields()}>
                초기화
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>

      <Card 
        title="OpenAI 생성 히스토리" 
        style={{ marginTop: 24 }}
        extra={<Button type="link">전체 보기</Button>}
      >
        <div style={{ 
          textAlign: 'center', 
          padding: '40px 0', 
          color: '#a6a6a6' 
        }}>
          아직 OpenAI로 생성된 콘텐츠가 없습니다.
        </div>
      </Card>
    </div>
  )
}

export default GenerationOpenAI