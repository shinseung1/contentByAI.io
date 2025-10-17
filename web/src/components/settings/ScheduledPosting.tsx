import React, { useState, useEffect } from 'react'
import { 
  Card, 
  Form, 
  Input, 
  Select, 
  Typography, 
  Button, 
  message, 
  DatePicker, 
  TimePicker, 
  Switch, 
  Space,
  Table,
  Modal,
  Tag,
  Divider,
  Radio,
  InputNumber,
  Tooltip
} from 'antd'
import { 
  ClockCircleOutlined, 
  SaveOutlined, 
  PlusOutlined, 
  EditOutlined,
  DeleteOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  LineChartOutlined,
  UserOutlined
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { api, ScheduledPost, CreateScheduledPostRequest } from '../../services/api'

const { Title, Text } = Typography
const { TextArea } = Input
const { Option } = Select

const ScheduledPosting: React.FC = () => {
  const [form] = Form.useForm()
  const [schedules, setSchedules] = useState<ScheduledPost[]>([])
  const [modalVisible, setModalVisible] = useState(false)
  const [editingSchedule, setEditingSchedule] = useState<ScheduledPost | null>(null)
  const [topicSource, setTopicSource] = useState<'user' | 'trend'>('user')
  const [loading, setLoading] = useState(false)

  // 실제 데이터 로드
  useEffect(() => {
    loadScheduledPosts()
  }, [])

  const loadScheduledPosts = async () => {
    try {
      setLoading(true)
      const posts = await api.listScheduledPosts()
      setSchedules(posts)
    } catch (error) {
      console.error('Failed to load scheduled posts:', error)
      message.error('스케줄 목록을 불러오는데 실패했습니다')
    } finally {
      setLoading(false)
    }
  }

  const handleSaveSchedule = async (values: any) => {
    try {
      setLoading(true)
      
      // 반복 설정 처리
      let repeatConfig: string | undefined = undefined
      if (values.repeatEnabled) {
        repeatConfig = JSON.stringify({
          enabled: true,
          type: values.repeatType,
          days: values.repeatType === 'weekly' ? values.repeatDays : undefined
        })
      }

      const scheduleData: CreateScheduledPostRequest = {
        title: values.title,
        topic: values.topicSource === 'user' ? values.topic : undefined,
        topic_source: values.topicSource,
        schedule_time: values.scheduleDateTime.format(),
        provider: values.provider,
        workflow_template_id: values.workflow_template_id,
        repeat_config: repeatConfig
      }

      if (editingSchedule) {
        await api.updateScheduledPost(editingSchedule.schedule_id, scheduleData)
        message.success('스케줄이 수정되었습니다')
      } else {
        await api.createScheduledPost(scheduleData)
        message.success('스케줄이 추가되었습니다')
      }

      // 목록 새로고침
      await loadScheduledPosts()
      
      setModalVisible(false)
      setEditingSchedule(null)
      form.resetFields()
    } catch (error) {
      console.error('Save schedule error:', error)
      message.error('저장 중 오류가 발생했습니다')
    } finally {
      setLoading(false)
    }
  }

  const handleEditSchedule = (schedule: ScheduledPost) => {
    setEditingSchedule(schedule)
    
    // repeat_config JSON 파싱
    let repeatData = { enabled: false, type: 'daily', days: [] }
    if (schedule.repeat_config) {
      try {
        repeatData = JSON.parse(schedule.repeat_config)
      } catch (e) {
        console.error('Failed to parse repeat_config:', e)
      }
    }
    
    form.setFieldsValue({
      title: schedule.title,
      topic: schedule.topic,
      topicSource: schedule.topic_source,
      scheduleDateTime: dayjs(schedule.schedule_time),
      provider: schedule.provider,
      workflow_template_id: schedule.workflow_template_id,
      repeatEnabled: repeatData.enabled || false,
      repeatType: repeatData.type || 'daily',
      repeatDays: repeatData.days || []
    })
    setTopicSource(schedule.topic_source)
    setModalVisible(true)
  }

  const handleDeleteSchedule = (scheduleId: string) => {
    Modal.confirm({
      title: '스케줄 삭제',
      content: '정말 이 스케줄을 삭제하시겠습니까?',
      onOk: async () => {
        try {
          await api.deleteScheduledPost(scheduleId)
          message.success('스케줄이 삭제되었습니다')
          await loadScheduledPosts() // 목록 새로고침
        } catch (error) {
          console.error('Delete schedule error:', error)
          message.error('삭제 중 오류가 발생했습니다')
        }
      }
    })
  }

  const toggleScheduleStatus = async (scheduleId: string) => {
    try {
      await api.toggleScheduledPostStatus(scheduleId)
      await loadScheduledPosts() // 목록 새로고침
      message.success('상태가 변경되었습니다')
    } catch (error) {
      console.error('Toggle status error:', error)
      message.error('상태 변경 중 오류가 발생했습니다')
    }
  }

  const columns = [
    {
      title: '제목',
      dataIndex: 'title',
      key: 'title',
      render: (text: string, record: ScheduledPost) => (
        <Space direction="vertical" size="small">
          <Text strong>{text}</Text>
          {record.topic && <Text type="secondary" style={{ fontSize: 12 }}>{record.topic}</Text>}
        </Space>
      )
    },
    {
      title: '주제 소스',
      dataIndex: 'topic_source',
      key: 'topic_source',
      render: (source: 'user' | 'trend') => (
        <Tag icon={source === 'user' ? <UserOutlined /> : <LineChartOutlined />} 
             color={source === 'user' ? 'blue' : 'green'}>
          {source === 'user' ? '사용자 지정' : '트렌드 기반'}
        </Tag>
      )
    },
    {
      title: '예약 시간',
      dataIndex: 'schedule_time',
      key: 'schedule_time',
      render: (time: string, record: ScheduledPost) => {
        // repeat_config 파싱
        let repeatData = { enabled: false, type: 'daily' }
        if (record.repeat_config) {
          try {
            repeatData = JSON.parse(record.repeat_config)
          } catch (e) {
            console.error('Failed to parse repeat_config:', e)
          }
        }
        
        return (
          <Space direction="vertical" size="small">
            <Text>{dayjs(time).format('YYYY-MM-DD HH:mm')}</Text>
            {repeatData.enabled && (
              <Tag size="small" color="purple">
                {repeatData.type === 'daily' ? '매일' : 
                 repeatData.type === 'weekly' ? '매주' : '매월'} 반복
              </Tag>
            )}
          </Space>
        )
      }
    },
    {
      title: 'AI 제공자',
      dataIndex: 'provider',
      key: 'provider',
      render: (provider: string) => (
        <Tag color={
          provider === 'gemini' ? 'blue' :
          provider === 'openai' ? 'green' :
          provider === 'claude' ? 'purple' : 'orange'
        }>
          {provider.toUpperCase()}
        </Tag>
      )
    },
    {
      title: '상태',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={
          status === 'pending' ? 'blue' :
          status === 'completed' ? 'green' :
          status === 'failed' ? 'red' : 'orange'
        }>
          {status === 'pending' ? '대기중' :
           status === 'completed' ? '완료' :
           status === 'failed' ? '실패' : '일시정지'}
        </Tag>
      )
    },
    {
      title: '작업',
      key: 'actions',
      render: (_: any, record: ScheduledPost) => (
        <Space>
          <Tooltip title={record.status === 'pending' ? '일시정지' : '재개'}>
            <Button 
              type="text" 
              icon={record.status === 'pending' ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
              onClick={() => toggleScheduleStatus(record.schedule_id)}
            />
          </Tooltip>
          <Tooltip title="수정">
            <Button 
              type="text" 
              icon={<EditOutlined />}
              onClick={() => handleEditSchedule(record)}
            />
          </Tooltip>
          <Tooltip title="삭제">
            <Button 
              type="text" 
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDeleteSchedule(record.schedule_id)}
            />
          </Tooltip>
        </Space>
      )
    }
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <Title level={3}>
            <ClockCircleOutlined style={{ marginRight: 8 }} />
            예약 포스팅 관리
          </Title>
          <Text type="secondary">자동 콘텐츠 생성 및 포스팅 스케줄을 관리합니다</Text>
        </div>
        <Button 
          type="primary" 
          icon={<PlusOutlined />}
          onClick={() => setModalVisible(true)}
          size="large"
        >
          새 스케줄 추가
        </Button>
      </div>

      <Card>
        <Table 
          columns={columns}
          dataSource={schedules}
          rowKey="schedule_id"
          pagination={{ pageSize: 10 }}
          loading={loading}
        />
      </Card>

      <Modal
        title={editingSchedule ? '스케줄 수정' : '새 스케줄 추가'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false)
          setEditingSchedule(null)
          form.resetFields()
        }}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSaveSchedule}
          initialValues={{
            topicSource: 'user',
            provider: 'gemini',
            workflow_template_id: 2,
            repeatEnabled: false,
            repeatType: 'daily'
          }}
        >
          <Form.Item name="title" label="스케줄 제목" rules={[{ required: true, message: '제목을 입력하세요' }]}>
            <Input placeholder="예: 매일 아침 트렌드 포스팅" />
          </Form.Item>

          <Form.Item name="topicSource" label="주제 설정 방식">
            <Radio.Group onChange={(e) => setTopicSource(e.target.value)}>
              <Radio value="user">
                <UserOutlined style={{ marginRight: 4 }} />
                사용자 지정 주제
              </Radio>
              <Radio value="trend">
                <LineChartOutlined style={{ marginRight: 4 }} />
                트렌드 기반 자동 선정
              </Radio>
            </Radio.Group>
          </Form.Item>

          {topicSource === 'user' && (
            <Form.Item 
              name="topic" 
              label="포스팅 주제"
              rules={[{ required: true, message: '주제를 입력하세요' }]}
            >
              <TextArea 
                placeholder="구체적인 주제를 입력하세요. 예: 2024년 AI 기술 동향 분석"
                rows={3}
              />
            </Form.Item>
          )}

          {topicSource === 'trend' && (
            <Card size="small" style={{ backgroundColor: '#f6ffed', marginBottom: 16 }}>
              <Text type="secondary">
                <LineChartOutlined style={{ marginRight: 4, color: '#52c41a' }} />
                트렌드 기반 모드에서는 예약된 시간에 다음 소스에서 인기 주제를 자동으로 선정합니다:
              </Text>
              <ul style={{ marginTop: 8, marginBottom: 0 }}>
                <li>Google Trends</li>
                <li>네이버 실시간 검색어</li>
                <li>소셜 미디어 트렌드</li>
                <li>뉴스 키워드</li>
              </ul>
            </Card>
          )}

          <Form.Item name="scheduleDateTime" label="예약 시간" rules={[{ required: true, message: '예약 시간을 선택하세요' }]}>
            <DatePicker 
              showTime 
              style={{ width: '100%' }}
              placeholder="날짜와 시간을 선택하세요"
              disabledDate={(current) => current && current < dayjs().startOf('day')}
            />
          </Form.Item>

          <Form.Item name="provider" label="AI 제공자">
            <Select>
              <Option value="gemini">Gemini</Option>
              <Option value="openai">OpenAI</Option>
              <Option value="claude">Claude</Option>
              <Option value="grok">Grok</Option>
            </Select>
          </Form.Item>

          <Form.Item name="workflow_template_id" label="워크플로우 템플릿">
            <Select>
              <Option value={2}>여행 정보전달</Option>
              <Option value={3}>시사 정보전달</Option>
              <Option value={4}>소셜 미디어 포스트</Option>
            </Select>
          </Form.Item>

          <Divider />

          <Form.Item name="repeatEnabled" label="반복 설정" valuePropName="checked">
            <Switch />
          </Form.Item>

          <Form.Item noStyle shouldUpdate={(prevValues, currentValues) => prevValues.repeatEnabled !== currentValues.repeatEnabled}>
            {({ getFieldValue }) => {
              return getFieldValue('repeatEnabled') ? (
                <>
                  <Form.Item name="repeatType" label="반복 주기">
                    <Radio.Group>
                      <Radio value="daily">매일</Radio>
                      <Radio value="weekly">매주</Radio>
                      <Radio value="monthly">매월</Radio>
                    </Radio.Group>
                  </Form.Item>

                  <Form.Item noStyle shouldUpdate={(prevValues, currentValues) => prevValues.repeatType !== currentValues.repeatType}>
                    {({ getFieldValue }) => {
                      return getFieldValue('repeatType') === 'weekly' ? (
                        <Form.Item name="repeatDays" label="반복 요일">
                          <Select mode="multiple" placeholder="요일을 선택하세요">
                            <Option value={1}>월요일</Option>
                            <Option value={2}>화요일</Option>
                            <Option value={3}>수요일</Option>
                            <Option value={4}>목요일</Option>
                            <Option value={5}>금요일</Option>
                            <Option value={6}>토요일</Option>
                            <Option value={0}>일요일</Option>
                          </Select>
                        </Form.Item>
                      ) : null
                    }}
                  </Form.Item>
                </>
              ) : null
            }}
          </Form.Item>

          <Form.Item style={{ marginTop: 24, marginBottom: 0 }}>
            <Space>
              <Button type="primary" htmlType="submit" icon={<SaveOutlined />}>
                {editingSchedule ? '수정' : '추가'}
              </Button>
              <Button onClick={() => {
                setModalVisible(false)
                setEditingSchedule(null)
                form.resetFields()
              }}>
                취소
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default ScheduledPosting