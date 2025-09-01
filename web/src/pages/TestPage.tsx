import React from 'react';
import { Layout, Typography, Breadcrumb, Space } from 'antd';
import { HomeOutlined, ExperimentOutlined } from '@ant-design/icons';
import ApiTester from '../components/ApiTester';

const { Content } = Layout;
const { Title } = Typography;

const TestPage: React.FC = () => {
  return (
    <Layout style={{ minHeight: '100vh', background: '#f0f2f5' }}>
      <Content style={{ padding: '24px' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <Breadcrumb style={{ marginBottom: 16 }}>
            <Breadcrumb.Item href="/">
              <HomeOutlined />
            </Breadcrumb.Item>
            <Breadcrumb.Item>
              <ExperimentOutlined />
              <span>API 테스트</span>
            </Breadcrumb.Item>
          </Breadcrumb>

          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <div>
              <Title level={1}>AI Writer API 테스트</Title>
              <Typography.Paragraph type="secondary" style={{ fontSize: '16px' }}>
                설정된 AI API들의 연결 상태를 확인하고 실시간으로 테스트할 수 있습니다.
                각 AI 제공자별로 연결 테스트와 콘텐츠 생성 테스트를 수행하여 
                시스템 상태를 모니터링하세요.
              </Typography.Paragraph>
            </div>

            <ApiTester />
          </Space>
        </div>
      </Content>
    </Layout>
  );
};

export default TestPage;