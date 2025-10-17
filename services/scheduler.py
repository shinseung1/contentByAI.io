#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
자동 포스팅 스케줄러 서비스
예약된 포스트를 자동으로 실행하는 백그라운드 서비스
"""

import asyncio
import json
import logging
import requests
import sys
import os
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import uuid4

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager, ScheduledPost, GenerationJob
from packages.gen.content_generator import ContentGenerator
from packages.gen.models import GenerationRequest

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TrendService:
    """트렌드 기반 주제 생성 서비스"""
    
    @staticmethod
    def get_trending_topics(count: int = 1) -> List[str]:
        """트렌드 기반 주제 생성"""
        # 실제 구현에서는 Google Trends API, 네이버 실시간 검색어 등을 활용
        # 현재는 샘플 주제 반환
        trending_topics = [
            "2024년 최신 AI 기술 동향과 전망",
            "겨울철 건강 관리법과 면역력 강화 방법", 
            "연말 맛집 추천 - 올해 핫한 음식 트렌드",
            "2024년 투자 전망과 주목할 섹터",
            "환경친화적 라이프스타일 실천 방법",
            "스마트워크 시대의 효율적인 업무 관리법",
            "K-컬처의 세계적 확산과 문화 콘텐츠 산업",
            "새해 다이어트와 운동 계획 세우기",
            "전기차 시장 변화와 미래 모빌리티",
            "메타버스와 가상현실 기술의 현재와 미래"
        ]
        
        import random
        selected_topics = random.sample(trending_topics, min(count, len(trending_topics)))
        logger.info(f"트렌드 기반 주제 생성: {selected_topics}")
        return selected_topics

class AutoPostingScheduler:
    """자동 포스팅 스케줄러"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.content_generator = ContentGenerator()
        self.trend_service = TrendService()
        self.running = False
        
    async def start(self):
        """스케줄러 시작"""
        self.running = True
        logger.info("자동 포스팅 스케줄러 시작")
        
        while self.running:
            try:
                await self.process_pending_posts()
                # 1분마다 체크
                await asyncio.sleep(60)
            except Exception as e:
                logger.error(f"스케줄러 처리 중 오류: {e}")
                await asyncio.sleep(60)
    
    def stop(self):
        """스케줄러 중지"""
        self.running = False
        logger.info("자동 포스팅 스케줄러 중지")
    
    async def process_pending_posts(self):
        """대기 중인 포스트 처리"""
        current_time = datetime.now().isoformat()
        pending_posts = self.db.get_pending_scheduled_posts(current_time)
        
        if not pending_posts:
            return
        
        logger.info(f"처리할 예약 포스트 {len(pending_posts)}개 발견")
        
        for post in pending_posts:
            try:
                await self.execute_scheduled_post(post)
            except Exception as e:
                logger.error(f"예약 포스트 {post.schedule_id} 처리 실패: {e}")
                # 실패 상태로 업데이트
                post.status = "failed"
                post.error_message = str(e)
                post.last_executed_at = datetime.now().isoformat()
                self.db.update_scheduled_post(post)
    
    async def execute_scheduled_post(self, scheduled_post: ScheduledPost):
        """예약 포스트 실행"""
        logger.info(f"예약 포스트 실행 시작: {scheduled_post.title}")
        
        # 주제 결정
        topic = self.determine_topic(scheduled_post)
        if not topic:
            raise Exception("주제를 결정할 수 없습니다")
        
        # 콘텐츠 생성 요청 생성
        generation_request = GenerationRequest(
            topic=topic,
            provider=scheduled_post.provider,
            tone="professional",  # 기본값
            word_count=800,  # 기본값
            include_images=False,  # 기본값
            target_language="ko",
            workflow_template_id=scheduled_post.workflow_template_id
        )
        
        # 콘텐츠 생성 작업 생성
        job_id = self.content_generator.create_job_id()
        
        try:
            # 콘텐츠 생성 (동기 처리)
            await self.content_generator.generate_content_async(job_id, generation_request)
            
            # 생성 성공 시 상태 업데이트
            scheduled_post.status = "completed"
            scheduled_post.generated_job_id = job_id
            scheduled_post.last_executed_at = datetime.now().isoformat()
            
            # 반복 설정이 있으면 다음 스케줄 생성
            if scheduled_post.repeat_config:
                self.create_next_schedule(scheduled_post)
            
            logger.info(f"예약 포스트 실행 완료: {scheduled_post.title}")
            
        except Exception as e:
            logger.error(f"콘텐츠 생성 실패: {e}")
            scheduled_post.status = "failed"
            scheduled_post.error_message = str(e)
            scheduled_post.last_executed_at = datetime.now().isoformat()
            raise
        
        finally:
            # 상태 업데이트
            self.db.update_scheduled_post(scheduled_post)
    
    def determine_topic(self, scheduled_post: ScheduledPost) -> str:
        """주제 결정"""
        if scheduled_post.topic_source == "user":
            return scheduled_post.topic
        elif scheduled_post.topic_source == "trend":
            # 트렌드 기반 주제 생성
            trending_topics = self.trend_service.get_trending_topics(1)
            return trending_topics[0] if trending_topics else None
        else:
            return scheduled_post.topic
    
    def create_next_schedule(self, completed_post: ScheduledPost):
        """반복 설정에 따른 다음 스케줄 생성"""
        if not completed_post.repeat_config:
            return
        
        try:
            repeat_config = json.loads(completed_post.repeat_config)
            if not repeat_config.get("enabled", False):
                return
            
            # 현재 시간 기준으로 다음 실행 시간 계산
            current_time = datetime.fromisoformat(completed_post.schedule_time)
            repeat_type = repeat_config.get("type", "daily")
            
            if repeat_type == "daily":
                next_time = current_time + timedelta(days=1)
            elif repeat_type == "weekly":
                next_time = current_time + timedelta(weeks=1)
            elif repeat_type == "monthly":
                # 월 단위는 대략 30일로 계산 (더 정확한 계산 필요시 dateutil 사용)
                next_time = current_time + timedelta(days=30)
            else:
                logger.warning(f"알 수 없는 반복 타입: {repeat_type}")
                return
            
            # 다음 스케줄 생성
            next_scheduled_post = ScheduledPost(
                schedule_id=str(uuid4()),
                title=completed_post.title,
                topic=completed_post.topic if completed_post.topic_source == "user" else None,
                topic_source=completed_post.topic_source,
                schedule_time=next_time.isoformat(),
                status="pending",
                provider=completed_post.provider,
                workflow_template_id=completed_post.workflow_template_id,
                repeat_config=completed_post.repeat_config,
                created_at=datetime.now().isoformat()
            )
            
            self.db.create_scheduled_post(next_scheduled_post)
            logger.info(f"다음 반복 스케줄 생성: {next_time.isoformat()}")
            
        except Exception as e:
            logger.error(f"다음 스케줄 생성 실패: {e}")

async def main():
    """메인 실행 함수"""
    scheduler = AutoPostingScheduler()
    
    try:
        await scheduler.start()
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단됨")
    except Exception as e:
        logger.error(f"스케줄러 실행 중 오류: {e}")
    finally:
        scheduler.stop()

if __name__ == "__main__":
    asyncio.run(main())