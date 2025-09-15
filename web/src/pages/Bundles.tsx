import React, { useState, useEffect } from 'react'
import {
  Typography,
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  message,
  Popconfirm,
  Tag,
  Card,
  Statistic
} from 'antd'
import {
  PlusOutlined,
  DeleteOutlined,
  EyeOutlined,
  EditOutlined
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'

const { Title } = Typography
const { TextArea } = Input

interface Bundle {
  id: string
  title: string
  description?: string
  posts: any[]
  created_at: string
  updated_at: string
}

interface BundleListResponse {
  bundles: string[]
  total: number
}

interface BundleDetailResponse {
  bundle_id: string
  bundle: Bundle
}

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1'

const Bundles: React.FC = () => {
  const [bundles, setBundles] = useState<Bundle[]>([])
  const [loading, setLoading] = useState(false)
  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [selectedBundle, setSelectedBundle] = useState<Bundle | null>(null)
  const [form] = Form.useForm()

  // 번들 목록 조회
  const fetchBundles = async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('authToken')
      const response = await fetch(`${API_BASE_URL}/bundles/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (!response.ok) {
        throw new Error('번들 목록 조회 실패')
      }
      
      const data: BundleListResponse = await response.json()
      
      // 각 번들의 상세 정보 조회
      const bundleDetails = await Promise.all(
        data.bundles.map(async (bundleId) => {
          const detailResponse = await fetch(`${API_BASE_URL}/bundles/${bundleId}`, {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          })
          
          if (detailResponse.ok) {
            const detail: BundleDetailResponse = await detailResponse.json()
            return detail.bundle
          }
          return null
        })
      )
      
      setBundles(bundleDetails.filter((bundle): bundle is Bundle => bundle !== null))
    } catch (error) {
      message.error('번들 목록을 불러오는데 실패했습니다')
      console.error('Error fetching bundles:', error)
    } finally {
      setLoading(false)
    }
  }

  // 번들 생성
  const createBundle = async (values: { title: string; description?: string }) => {
    try {
      const token = localStorage.getItem('authToken')
      const response = await fetch(`${API_BASE_URL}/bundles/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(values),
      })
      
      if (!response.ok) {
        throw new Error('번들 생성 실패')
      }
      
      message.success('번들이 생성되었습니다')
      setCreateModalVisible(false)
      form.resetFields()
      fetchBundles()
    } catch (error) {
      message.error('번들 생성에 실패했습니다')
      console.error('Error creating bundle:', error)
    }
  }

  // 번들 삭제
  const deleteBundle = async (bundleId: string) => {
    try {
      const token = localStorage.getItem('authToken')
      const response = await fetch(`${API_BASE_URL}/bundles/${bundleId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (!response.ok) {
        throw new Error('번들 삭제 실패')
      }
      
      message.success('번들이 삭제되었습니다')
      fetchBundles()
    } catch (error) {
      message.error('번들 삭제에 실패했습니다')
      console.error('Error deleting bundle:', error)
    }
  }

  // 번들 상세보기
  const viewBundle = (bundle: Bundle) => {
    setSelectedBundle(bundle)
    setDetailModalVisible(true)
  }

  useEffect(() => {
    fetchBundles()
  }, [])

  const columns: ColumnsType<Bundle> = [
    {
      title: '제목',
      dataIndex: 'title',
      key: 'title',
      render: (text: string) => <strong>{text}</strong>,
    },
    {
      title: '설명',
      dataIndex: 'description',
      key: 'description',
      render: (text: string) => text || '-',
    },
    {
      title: '포스트 수',
      dataIndex: 'posts',
      key: 'posts',
      render: (posts: any[]) => (
        <Tag color={posts.length > 0 ? 'blue' : 'default'}>
          {posts.length}개
        </Tag>
      ),
    },
    {
      title: '생성일',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleDateString('ko-KR'),
    },
    {
      title: '수정일',
      dataIndex: 'updated_at',
      key: 'updated_at',
      render: (date: string) => new Date(date).toLocaleDateString('ko-KR'),
    },
    {
      title: '작업',
      key: 'action',
      render: (_, record: Bundle) => (
        <Space size="middle">
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => viewBundle(record)}
          >
            상세보기
          </Button>
          <Popconfirm
            title="번들 삭제"
            description="정말 이 번들을 삭제하시겠습니까?"
            onConfirm={() => deleteBundle(record.id)}
            okText="삭제"
            cancelText="취소"
          >
            <Button
              type="link"
              danger
              icon={<DeleteOutlined />}
            >
              삭제
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div className="page-header">
        <Title level={1}>번들 관리</Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setCreateModalVisible(true)}
          style={{ marginTop: 16 }}
        >
          새 번들 생성
        </Button>
      </div>

      {/* 통계 카드 */}
      <div style={{ marginBottom: 24 }}>
        <Card>
          <Statistic
            title="총 번들 수"
            value={bundles.length}
            suffix="개"
          />
        </Card>
      </div>

      {/* 번들 테이블 */}
      <Table
        columns={columns}
        dataSource={bundles}
        rowKey="id"
        loading={loading}
        pagination={{
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} items`,
        }}
      />

      {/* 번들 생성 모달 */}
      <Modal
        title="새 번들 생성"
        open={createModalVisible}
        onOk={form.submit}
        onCancel={() => {
          setCreateModalVisible(false)
          form.resetFields()
        }}
        okText="생성"
        cancelText="취소"
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={createBundle}
        >
          <Form.Item
            label="번들 제목"
            name="title"
            rules={[{ required: true, message: '번들 제목을 입력해주세요' }]}
          >
            <Input placeholder="번들 제목을 입력하세요" />
          </Form.Item>
          <Form.Item
            label="설명"
            name="description"
          >
            <TextArea
              rows={4}
              placeholder="번들에 대한 설명을 입력하세요 (선택사항)"
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* 번들 상세보기 모달 */}
      <Modal
        title="번들 상세정보"
        open={detailModalVisible}
        onCancel={() => {
          setDetailModalVisible(false)
          setSelectedBundle(null)
        }}
        footer={[
          <Button key="close" onClick={() => {
            setDetailModalVisible(false)
            setSelectedBundle(null)
          }}>
            닫기
          </Button>
        ]}
        width={800}
      >
        {selectedBundle && (
          <div>
            <p><strong>ID:</strong> {selectedBundle.id}</p>
            <p><strong>제목:</strong> {selectedBundle.title}</p>
            <p><strong>설명:</strong> {selectedBundle.description || '없음'}</p>
            <p><strong>포스트 수:</strong> {selectedBundle.posts.length}개</p>
            <p><strong>생성일:</strong> {new Date(selectedBundle.created_at).toLocaleString('ko-KR')}</p>
            <p><strong>수정일:</strong> {new Date(selectedBundle.updated_at).toLocaleString('ko-KR')}</p>
            
            {selectedBundle.posts.length > 0 && (
              <div>
                <Title level={4}>포스트 목록</Title>
                <ul>
                  {selectedBundle.posts.map((post, index) => (
                    <li key={index}>
                      {post.title || `포스트 ${index + 1}`}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}

export default Bundles