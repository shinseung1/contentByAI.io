import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Card,
  Calendar,
  Badge,
  Modal,
  Form,
  Input,
  Select,
  DatePicker,
  Button,
  Typography,
  List,
  Tag,
  Space,
  Tooltip,
  message,
  Popconfirm
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ClockCircleOutlined,
  CalendarOutlined
} from '@ant-design/icons';
import { generationAPI } from '../services/api';
import dayjs, { Dayjs } from 'dayjs';

const { Title, Text } = Typography;
const { Option } = Select;

interface ScheduledJob {
  id: string;
  topic: string;
  scheduled_at: string;
  status: string;
  tone?: string;
  word_count?: number;
  target_language?: string;
}

const Schedule: React.FC = () => {
  const [selectedDate, setSelectedDate] = useState<Dayjs>(dayjs());
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingJob, setEditingJob] = useState<ScheduledJob | null>(null);
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  const { data: scheduledJobs, isLoading } = useQuery({
    queryKey: ['scheduled-jobs'],
    queryFn: () => generationAPI.listJobs(),
    select: (data) => data.data.filter((job: any) => job.scheduled_at)
  });

  const createScheduleMutation = useMutation({
    mutationFn: (data: any) => generationAPI.generate(data),
    onSuccess: () => {
      message.success('예약이 성공적으로 등록되었습니다.');
      setIsModalVisible(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['scheduled-jobs'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '예약 등록에 실패했습니다.');
    }
  });

  const deleteScheduleMutation = useMutation({
    mutationFn: (jobId: string) => generationAPI.deleteJob(jobId),
    onSuccess: () => {
      message.success('예약이 삭제되었습니다.');
      queryClient.invalidateQueries({ queryKey: ['scheduled-jobs'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '예약 삭제에 실패했습니다.');
    }
  });

  const getJobsForDate = (date: Dayjs) => {
    if (!scheduledJobs) return [];
    
    return scheduledJobs.filter((job: ScheduledJob) => 
      dayjs(job.scheduled_at).format('YYYY-MM-DD') === date.format('YYYY-MM-DD')
    );
  };

  const dateCellRender = (value: Dayjs) => {
    const jobs = getJobsForDate(value);
    
    return (
      <div className="calendar-cell">
        {jobs.map((job: ScheduledJob) => (
          <Badge
            key={job.id}
            status={job.status === 'pending' ? 'processing' : 'default'}
            text={
              <span className="text-xs truncate block">
                {job.topic.length > 20 ? `${job.topic.substring(0, 20)}...` : job.topic}
              </span>
            }
          />
        ))}
      </div>
    );
  };

  const onDateSelect = (date: Dayjs) => {
    setSelectedDate(date);
  };

  const handleAddSchedule = () => {
    setEditingJob(null);
    form.resetFields();
    form.setFieldsValue({
      scheduled_at: selectedDate,
      tone: 'professional',
      word_count: 800,
      target_language: 'ko',
      include_images: true
    });
    setIsModalVisible(true);
  };

  const handleEditSchedule = (job: ScheduledJob) => {
    setEditingJob(job);
    form.setFieldsValue({
      ...job,
      scheduled_at: dayjs(job.scheduled_at)
    });
    setIsModalVisible(true);
  };

  const handleDeleteSchedule = (jobId: string) => {
    deleteScheduleMutation.mutate(jobId);
  };

  const onFinish = (values: any) => {
    const payload = {
      ...values,
      scheduled_at: values.scheduled_at.toISOString(),
      include_images: values.include_images || false
    };

    createScheduleMutation.mutate(payload);
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

  const selectedDateJobs = getJobsForDate(selectedDate);

  return (
    <div className="p-6">
      <div className="mb-6">
        <div className="flex justify-between items-start">
          <div>
            <Title level={2}>
              <CalendarOutlined className="mr-2" />
              콘텐츠 스케줄
            </Title>
            <Text type="secondary">
              콘텐츠 생성 일정을 관리하고 예약하세요.
            </Text>
          </div>
          
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleAddSchedule}
          >
            새 예약
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card title="캘린더" className="h-fit">
            <Calendar
              value={selectedDate}
              onSelect={onDateSelect}
              dateCellRender={dateCellRender}
              className="schedule-calendar"
            />
          </Card>
        </div>

        <div className="lg:col-span-1">
          <Card title={`${selectedDate.format('YYYY년 MM월 DD일')} 예약`}>
            {selectedDateJobs.length > 0 ? (
              <List
                itemLayout="vertical"
                size="small"
                dataSource={selectedDateJobs}
                renderItem={(job: ScheduledJob) => (
                  <List.Item
                    key={job.id}
                    actions={[
                      <Tooltip title="수정">
                        <Button
                          type="text"
                          icon={<EditOutlined />}
                          size="small"
                          onClick={() => handleEditSchedule(job)}
                        />
                      </Tooltip>,
                      <Popconfirm
                        title="이 예약을 삭제하시겠습니까?"
                        onConfirm={() => handleDeleteSchedule(job.id)}
                        okText="삭제"
                        cancelText="취소"
                      >
                        <Tooltip title="삭제">
                          <Button
                            type="text"
                            icon={<DeleteOutlined />}
                            size="small"
                            danger
                          />
                        </Tooltip>
                      </Popconfirm>
                    ]}
                  >
                    <List.Item.Meta
                      title={
                        <div className="flex items-center justify-between">
                          <span className="font-medium">{job.topic}</span>
                          <Tag color={job.status === 'pending' ? 'blue' : 'default'}>
                            {job.status === 'pending' ? '예약됨' : job.status}
                          </Tag>
                        </div>
                      }
                      description={
                        <div className="space-y-1">
                          <div className="flex items-center space-x-2 text-xs">
                            <ClockCircleOutlined />
                            <span>{dayjs(job.scheduled_at).format('HH:mm')}</span>
                            {job.tone && <Tag size="small">{job.tone}</Tag>}
                            {job.word_count && <span>{job.word_count}단어</span>}
                          </div>
                        </div>
                      }
                    />
                  </List.Item>
                )}
              />
            ) : (
              <div className="text-center py-8">
                <ClockCircleOutlined className="text-4xl text-gray-300 mb-2" />
                <Text type="secondary">이 날짜에 예약된 작업이 없습니다.</Text>
              </div>
            )}
          </Card>
        </div>
      </div>

      <Modal
        title={editingJob ? "예약 수정" : "새 예약 등록"}
        open={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          className="space-y-4"
        >
          <Form.Item
            label="주제"
            name="topic"
            rules={[
              { required: true, message: '주제를 입력해주세요!' },
              { min: 5, message: '주제는 최소 5자 이상 입력해주세요!' }
            ]}
          >
            <Input.TextArea
              placeholder="예: 인공지능과 머신러닝의 미래 전망"
              rows={3}
              maxLength={500}
              showCount
            />
          </Form.Item>

          <div className="grid grid-cols-2 gap-4">
            <Form.Item
              label="작성 톤"
              name="tone"
              rules={[{ required: true, message: '작성 톤을 선택해주세요!' }]}
            >
              <Select placeholder="작성 스타일">
                {toneOptions.map(option => (
                  <Option key={option.value} value={option.value}>
                    {option.label}
                  </Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item
              label="목표 단어 수"
              name="word_count"
              rules={[{ required: true, message: '단어 수를 입력해주세요!' }]}
            >
              <Select placeholder="단어 수">
                <Option value={500}>500 단어</Option>
                <Option value={800}>800 단어</Option>
                <Option value={1200}>1200 단어</Option>
                <Option value={1500}>1500 단어</Option>
                <Option value={2000}>2000 단어</Option>
              </Select>
            </Form.Item>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Form.Item
              label="언어"
              name="target_language"
              rules={[{ required: true, message: '언어를 선택해주세요!' }]}
            >
              <Select placeholder="언어">
                {languageOptions.map(option => (
                  <Option key={option.value} value={option.value}>
                    {option.label}
                  </Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item
              label="예약 시간"
              name="scheduled_at"
              rules={[{ required: true, message: '예약 시간을 선택해주세요!' }]}
            >
              <DatePicker
                showTime
                format="YYYY-MM-DD HH:mm"
                placeholder="예약 시간 선택"
                className="w-full"
                disabledDate={(current) => current && current < dayjs().startOf('day')}
              />
            </Form.Item>
          </div>

          <div className="flex justify-end space-x-2 pt-4">
            <Button onClick={() => setIsModalVisible(false)}>
              취소
            </Button>
            <Button
              type="primary"
              htmlType="submit"
              loading={createScheduleMutation.isPending}
              icon={<ClockCircleOutlined />}
            >
              {editingJob ? '수정' : '예약 등록'}
            </Button>
          </div>
        </Form>
      </Modal>
    </div>
  );
};

export default Schedule;