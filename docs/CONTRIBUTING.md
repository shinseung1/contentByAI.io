# 기여 가이드

AI Writer 프로젝트에 기여해주셔서 감사합니다! 이 문서는 기여 방법과 개발 규칙에 대해 설명합니다.

## 🤝 기여 방법

### 1. 이슈 생성
- 버그 리포트, 기능 제안, 질문 등을 [Issues](https://github.com/your-repo/issues)에 등록
- 템플릿을 사용하여 명확하고 상세한 설명 제공

### 2. 개발 환경 설정
```bash
# 1. 포크 및 클론
git clone https://github.com/your-username/CreateAutoContentByAi.git
cd CreateAutoContentByAi

# 2. 개발 브랜치 생성
git checkout -b feature/your-feature-name

# 3. 개발 환경 설정
make dev-setup
```

### 3. 개발 및 테스트
```bash
# 개발 서버 실행
make dev

# 코드 품질 검사
make lint

# 테스트 실행
make test

# 타입 검사
mypy .
```

### 4. 커밋 및 푸시
```bash
# 변경사항 커밋
git add .
git commit -m "feat: add new feature description"

# 푸시
git push origin feature/your-feature-name
```

### 5. Pull Request 생성
- 명확한 제목과 설명 작성
- 관련된 이슈 번호 참조
- 변경사항에 대한 테스트 완료 확인

## 📝 코딩 스타일

### Python
- **PEP 8** 준수
- **Black** 포맷터 사용 (라인 길이: 88)
- **Type hints** 필수 사용
- **Docstring** 작성 (Google style)

```python
def example_function(param: str, count: int = 10) -> List[str]:
    """Example function with proper typing and docstring.
    
    Args:
        param: Description of param
        count: Number of items to return
        
    Returns:
        List of processed strings
        
    Raises:
        ValueError: If param is empty
    """
    if not param:
        raise ValueError("param cannot be empty")
    
    return [f"{param}_{i}" for i in range(count)]
```

### TypeScript/JavaScript
- **ES6+** 문법 사용
- **TypeScript strict mode** 활성화
- **ESLint + Prettier** 사용
- **함수형 컴포넌트** 선호

```typescript
interface Props {
  title: string;
  items: string[];
  onSelect?: (item: string) => void;
}

const ExampleComponent: React.FC<Props> = ({ title, items, onSelect }) => {
  const handleClick = useCallback((item: string) => {
    onSelect?.(item);
  }, [onSelect]);

  return (
    <div>
      <h2>{title}</h2>
      {items.map(item => (
        <button key={item} onClick={() => handleClick(item)}>
          {item}
        </button>
      ))}
    </div>
  );
};
```

## 🏗️ 아키텍처 원칙

### SOLID 원칙 준수
1. **Single Responsibility**: 각 클래스/모듈은 하나의 책임만
2. **Open-Closed**: 확장에는 열려있고 수정에는 닫혀있어야 함
3. **Liskov Substitution**: 하위 타입은 상위 타입을 완전히 대체 가능
4. **Interface Segregation**: 클라이언트는 사용하지 않는 인터페이스에 의존하면 안됨
5. **Dependency Inversion**: 고수준 모듈은 저수준 모듈에 의존하면 안됨

### 새로운 Publisher 추가 예시
```python
# 1. BasePublisher 상속
class NewPlatformPublisher(BasePublisher):
    def get_platform_name(self) -> str:
        return "newplatform"
    
    async def publish_draft(self, title: str, content: str, metadata: PostMetadata, images: Optional[Dict[str, bytes]] = None) -> PublishResult:
        # 구현
        pass

# 2. Factory에 등록
class PublisherFactory:
    _publishers = {
        "wordpress": WordPressPublisher,
        "blogger": BloggerPublisher,
        "newplatform": NewPlatformPublisher,  # 추가
    }
```

## 🧪 테스트 작성

### 단위 테스트
```python
import pytest
from packages.publisher.wp.publisher import WordPressPublisher

class TestWordPressPublisher:
    @pytest.fixture
    def publisher(self):
        config = {
            "base_url": "https://test.com",
            "username": "test",
            "password": "test"
        }
        return WordPressPublisher(config)
    
    def test_platform_name(self, publisher):
        assert publisher.get_platform_name() == "wordpress"
    
    @pytest.mark.asyncio
    async def test_publish_draft(self, publisher, mock_wp_client):
        # 테스트 구현
        pass
```

### 통합 테스트
```python
@pytest.mark.integration
class TestPublisherIntegration:
    @pytest.mark.asyncio
    async def test_wordpress_publish_flow(self):
        # 전체 플로우 테스트
        pass
```

## 📦 의존성 관리

### Python 패키지 추가
```bash
# pyproject.toml에 의존성 추가 후
pip install -e .

# 개발 의존성인 경우
pip install -e .[dev]
```

### Node.js 패키지 추가
```bash
cd web
npm install package-name
# 또는 개발 의존성
npm install -D package-name
```

## 🚀 배포 및 릴리스

### 버전 관리
- **Semantic Versioning** (Major.Minor.Patch) 사용
- `pyproject.toml`과 `package.json`에서 버전 동기화

### 릴리스 프로세스
1. 기능 개발 완료
2. 테스트 통과 확인
3. 문서 업데이트
4. 버전 번호 업데이트
5. 태그 생성 및 릴리스

## 📋 체크리스트

### Pull Request 체크리스트
- [ ] 코드가 스타일 가이드를 따름
- [ ] 모든 테스트가 통과함
- [ ] 타입 체크 통과
- [ ] 새로운 기능에 대한 테스트 추가
- [ ] 문서 업데이트
- [ ] 브레이킹 체인지 문서화
- [ ] 성능에 영향을 주는 변경사항 검토

### 코드 리뷰 기준
- **기능성**: 요구사항을 올바르게 구현했는가?
- **성능**: 성능상 문제는 없는가?
- **보안**: 보안 취약점은 없는가?
- **유지보수성**: 코드가 이해하기 쉽고 수정하기 쉬운가?
- **테스트**: 적절한 테스트가 있는가?

## 🐛 버그 신고

### 버그 리포트에 포함될 내용
- **환경 정보**: OS, Python 버전, Node.js 버전 등
- **재현 단계**: 단계별 재현 방법
- **예상 결과**: 예상했던 동작
- **실제 결과**: 실제 발생한 동작
- **로그 파일**: 관련 에러 로그
- **스크린샷**: UI 관련 이슈인 경우

### 버그 우선순위
- **Critical**: 시스템 크래시, 데이터 손실
- **High**: 핵심 기능 불가
- **Medium**: 부분적 기능 이상
- **Low**: 사소한 UI 문제, 개선사항

## 💡 기능 제안

### 새로운 기능 제안시 고려사항
- **문제 정의**: 해결하려는 문제가 명확한가?
- **사용자 가치**: 사용자에게 실질적 도움이 되는가?
- **기술적 타당성**: 현재 아키텍처에 적합한가?
- **유지보수성**: 장기적으로 유지보수 가능한가?
- **성능 영향**: 기존 기능에 영향을 주지 않는가?

## 📞 커뮤니티

- **GitHub Issues**: 버그 신고, 기능 요청
- **GitHub Discussions**: 일반적인 질문, 아이디어 논의
- **Email**: 보안 이슈나 민감한 사항

## 🏆 기여자 인정

모든 기여자는 프로젝트의 README와 릴리스 노트에 기록됩니다. 기여 유형:

- 💻 코드 기여
- 📖 문서 개선
- 🐛 버그 신고
- 💡 아이디어 제안
- 🎨 디자인 개선
- 🧪 테스트 추가
- 🌍 번역

감사합니다! 🙏