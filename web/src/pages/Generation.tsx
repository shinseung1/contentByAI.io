import React from 'react'
import { Card, Form, Input, Button, Select, InputNumber, Switch, Typography, Space, message } from 'antd'
import { EditOutlined, SendOutlined } from '@ant-design/icons'

const { Title } = Typography
const { TextArea } = Input

const Generation: React.FC = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = React.useState(false)

  const handleGenerate = async (values: any) => {
    setLoading(true)
    try {
      // API 호출 로직
      console.log('Generation request:', values)
      message.success('콘텐츠 생성 요청이 시작되었습니다!')
    } catch (error) {
      message.error('콘텐츠 생성 중 오류가 발생했습니다.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="page-header">
        <Title level={1}>콘텐츠 생성</Title>
      </div>

      <Card title={<><EditOutlined /> 새로운 콘텐츠 생성</>}>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleGenerate}
          initialValues={{
            tone: 'professional',
            word_count: 800,
            include_images: true,
            target_language: 'ko',
          }}
        >
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
              placeholder="생성할 콘텐츠의 주제를 구체적으로 입력해주세요. 예: '인공지능이 마케팅에 미치는 영향과 활용 방안'"
            />
          </Form.Item>

          <Form.Item name="tone" label="톤 앤 매너">
            <Select>
              <Select.Option value="professional">전문적</Select.Option>
              <Select.Option value="casual">캐주얼</Select.Option>
              <Select.Option value="friendly">친근한</Select.Option>
              <Select.Option value="academic">학술적</Select.Option>
              <Select.Option value="conversational">대화형</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item name="word_count" label="목표 단어 수">
            <InputNumber
              min={300}
              max={3000}
              step={100}
              style={{ width: '100%' }}
              placeholder="800"
            />
          </Form.Item>

          <Form.Item name="target_language" label="언어">
            <Select>
              <Select.Option value="ko">한국어</Select.Option>
              <Select.Option value="en">영어</Select.Option>
              <Select.Option value="ja">일본어</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item name="include_images" label="이미지 포함" valuePropName="checked">
            <Switch />
          </Form.Item>

          <Form.Item style={{ marginTop: 24 }}>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                icon={<SendOutlined />}
                loading={loading}
                size="large"
              >
                콘텐츠 생성 시작
              </Button>
              <Button size="large" onClick={() => form.resetFields()}>
                초기화
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>

      <Card 
        title="생성 히스토리" 
        style={{ marginTop: 24 }}
        extra={<Button type="link">전체 보기</Button>}
      >
        <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
          아직 생성된 콘텐츠가 없습니다.
        </div>
      </Card>
    </div>
  )
}

export default Generation