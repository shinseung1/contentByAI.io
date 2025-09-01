import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { 
  Card, 
  Form, 
  Input, 
  Select, 
  InputNumber, 
  Switch, 
  Button, 
  Typography, 
  Row, 
  Col,
  Alert,
  Space,
  DatePicker,
  message
} from 'antd';
import { 
  SendOutlined, 
  ClockCircleOutlined,
  FileTextOutlined,
  SettingOutlined
} from '@ant-design/icons';
import { generationAPI } from '../services/api';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { TextArea } = Input;
const { Option } = Select;

interface GenerateForm {
  topic: string;
  tone: string;
  word_count: number;
  include_images: boolean;
  target_language: string;
  scheduled_at?: string;
}

const Generate: React.FC = () => {
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const [scheduleMode, setScheduleMode] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const generateMutation = useMutation({
    mutationFn: (data: GenerateForm) => generationAPI.generate(data),
    onSuccess: (response) => {
      const jobId = response.data.job_id;
      setSuccessMessage(
        `콘텐츠 생성이 시작되었습니다! 작업 ID: ${jobId}`
      );
      message.success('콘텐츠 생성 요청이 성공적으로 제출되었습니다.');
      form.resetFields();
      
      setTimeout(() => {
        navigate(`/jobs/${jobId}`);
      }, 2000);
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || '콘텐츠 생성 요청 중 오류가 발생했습니다.';
      message.error(errorMessage);
    }
  });

  const onFinish = (values: GenerateForm) => {
    const payload = {
      ...values,
      scheduled_at: scheduleMode && values.scheduled_at 
        ? dayjs(values.scheduled_at).toISOString()
        : undefined
    };
    
    generateMutation.mutate(payload);
  };

  const toneOptions = [
    { value: 'professional', label: '전문적인' },
    { value: 'casual', label: '캐주얼한' },
    { value: 'friendly', label: '친근한' },
    { value: 'formal', label: '격식있는' },
    { value: 'humorous', label: '유머러스한' },
    { value: 'informative', label: '정보 전달적인' }
  ];

  const languageOptions = [
    { value: 'ko', label: '한국어' },
    { value: 'en', label: '영어' },
    { value: 'ja', label: '일본어' },
    { value: 'zh', label: '중국어' }
  ];

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6">
        <Title level={2}>
          <FileTextOutlined className="mr-2" />
          콘텐츠 생성
        </Title>
        <Text type="secondary">
          AI를 활용하여 고품질의 블로그 콘텐츠를 자동 생성하세요.
        </Text>
      </div>

      {successMessage && (
        <Alert
          message="생성 요청 성공"
          description={successMessage}
          type="success"
          showIcon
          closable
          className="mb-6"
          onClose={() => setSuccessMessage(null)}
        />
      )}

      <Card title="콘텐츠 생성 설정" className="shadow-lg">
        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          initialValues={{
            tone: 'professional',
            word_count: 800,
            include_images: true,
            target_language: 'ko'
          }}
          className="space-y-4"
        >
          <Row gutter={[24, 0]}>
            <Col xs={24} lg={16}>
              <Form.Item
                label="주제"
                name="topic"
                rules={[
                  { required: true, message: '주제를 입력해주세요!' },
                  { min: 5, message: '주제는 최소 5자 이상 입력해주세요!' },
                  { max: 500, message: '주제는 최대 500자까지 입력 가능합니다!' }
                ]}
              >
                <TextArea
                  placeholder="예: 인공지능과 머신러닝의 미래 전망과 사회에 미치는 영향"
                  rows={3}
                  maxLength={500}
                  showCount
                />
              </Form.Item>
            </Col>

            <Col xs={24} lg={8}>
              <Form.Item
                label="작성 톤"
                name="tone"
                rules={[{ required: true, message: '작성 톤을 선택해주세요!' }]}
              >
                <Select placeholder="작성 스타일을 선택하세요">
                  {toneOptions.map(option => (
                    <Option key={option.value} value={option.value}>
                      {option.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={[24, 0]}>
            <Col xs={24} sm={8}>
              <Form.Item
                label="목표 단어 수"
                name="word_count"
                rules={[
                  { required: true, message: '단어 수를 입력해주세요!' },
                  { type: 'number', min: 300, max: 3000, message: '300-3000 단어 사이로 입력해주세요!' }
                ]}
              >
                <InputNumber
                  min={300}
                  max={3000}
                  step={100}
                  className="w-full"
                  formatter={(value) => `${value} 단어`}
                  parser={(value) => value?.replace(' 단어', '') as any}
                />
              </Form.Item>
            </Col>

            <Col xs={24} sm={8}>
              <Form.Item
                label="언어"
                name="target_language"
                rules={[{ required: true, message: '언어를 선택해주세요!' }]}
              >
                <Select placeholder="언어를 선택하세요">
                  {languageOptions.map(option => (
                    <Option key={option.value} value={option.value}>
                      {option.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>

            <Col xs={24} sm={8}>
              <Form.Item
                label="이미지 포함"
                name="include_images"
                valuePropName="checked"
              >
                <Switch
                  checkedChildren="포함"
                  unCheckedChildren="미포함"
                />
              </Form.Item>
            </Col>
          </Row>

          <Card 
            size="small" 
            title={
              <Space>
                <SettingOutlined />
                <span>고급 설정</span>
              </Space>
            }
            className="bg-gray-50"
          >
            <Row gutter={[24, 0]} align="middle">
              <Col xs={24} sm={8}>
                <Form.Item
                  label="예약 실행"
                  className="mb-0"
                >
                  <Switch
                    checked={scheduleMode}
                    onChange={setScheduleMode}
                    checkedChildren={<ClockCircleOutlined />}
                    unCheckedChildren="즉시"
                  />
                </Form.Item>
              </Col>

              {scheduleMode && (
                <Col xs={24} sm={16}>
                  <Form.Item
                    label="예약 시간"
                    name="scheduled_at"
                    rules={[
                      { required: scheduleMode, message: '예약 시간을 선택해주세요!' }
                    ]}
                  >
                    <DatePicker
                      showTime
                      format="YYYY-MM-DD HH:mm"
                      placeholder="예약 시간 선택"
                      className="w-full"
                      disabledDate={(current) => current && current < dayjs().startOf('day')}
                    />
                  </Form.Item>
                </Col>
              )}
            </Row>
          </Card>

          <div className="text-center pt-6">
            <Space size="large">
              <Button
                size="large"
                onClick={() => form.resetFields()}
              >
                초기화
              </Button>
              
              <Button
                type="primary"
                size="large"
                htmlType="submit"
                loading={generateMutation.isPending}
                icon={scheduleMode ? <ClockCircleOutlined /> : <SendOutlined />}
                className="px-8"
              >
                {generateMutation.isPending
                  ? '생성 중...'
                  : scheduleMode
                  ? '예약 등록'
                  : '즉시 생성'
                }
              </Button>
            </Space>
          </div>
        </Form>
      </Card>

      <Card className="mt-6" size="small">
        <div className="text-center">
          <Text type="secondary" className="text-xs">
            💡 팁: 구체적이고 명확한 주제를 입력할수록 더 좋은 결과를 얻을 수 있습니다.
            생성된 콘텐츠는 작업 목록에서 확인하고 편집할 수 있습니다.
          </Text>
        </div>
      </Card>
    </div>
  );
};

export default Generate;