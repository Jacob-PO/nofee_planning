# Confluence REST API 연동

NoFee 워크스페이스와 Confluence를 연동하기 위한 도구입니다.

## 설정 방법

### 1. 의존성 설치

```bash
cd nofee-jacob/confluence
npm install
```

### 2. 환경 변수 설정

**중요**: API 키는 `config/confluence.env` 파일에서 관리됩니다.

`config/confluence.env.example` 파일을 참고하여 `config/confluence.env`를 생성하세요:

```bash
# 워크스페이스 루트에서 실행
cp config/confluence.env.example config/confluence.env
```

`config/confluence.env` 파일 내용:

```env
CONFLUENCE_BASE_URL=https://nofee-workspace.atlassian.net/wiki
CONFLUENCE_EMAIL=your-email@example.com
CONFLUENCE_API_TOKEN=your-api-token-here
CONFLUENCE_SPACE_KEY=PM
```

### 3. API 토큰 생성

1. Atlassian 계정 설정으로 이동: https://id.atlassian.com/manage-profile/security/api-tokens
2. "Create API token" 클릭
3. 토큰 이름 입력 (예: "nofee-confluence-api")
4. 생성된 토큰을 복사하여 `config/confluence.env` 파일의 `CONFLUENCE_API_TOKEN`에 입력

### 4. Space Key 확인

Confluence 스페이스 URL에서 Space Key를 확인할 수 있습니다:
- URL 형식: `https://nofee-workspace.atlassian.net/wiki/spaces/SPACEKEY/...`
- 예시: PM 스페이스의 경우 `CONFLUENCE_SPACE_KEY=PM`

## 사용 방법

### 페이지 목록 조회

```bash
npm run list-pages
```

스페이스의 모든 페이지 목록을 조회합니다.

### 새 페이지 생성

```bash
npm run create-page
```

테스트 페이지를 생성합니다. 자동으로 타임스탬프가 포함된 제목이 생성됩니다.

### 페이지 조회

```bash
npm run get-page "페이지 제목"
```

특정 페이지의 내용을 조회합니다.

예시:
```bash
npm run get-page "NoFee API 문서"
```

### 페이지 업데이트

```bash
npm run update-page "페이지 제목"
```

기존 페이지를 업데이트합니다.

예시:
```bash
npm run update-page "테스트 페이지"
```

### API 문서 동기화

```bash
npm run sync-api-docs
```

프로젝트의 API 문서를 Confluence에 자동으로 동기화합니다. 페이지가 없으면 생성하고, 있으면 업데이트합니다.

## API 클라이언트 사용 예제

직접 코드에서 Confluence API를 사용하려면:

```javascript
import ConfluenceClient from './lib/confluence-client.js';

const client = new ConfluenceClient();

// 페이지 생성
const page = await client.createPage(
  '새 페이지 제목',
  '<p>페이지 내용</p>'
);

// 페이지 조회
const existingPage = await client.getPageByTitle('기존 페이지');

// 페이지 업데이트
await client.updatePage(
  existingPage.id,
  '업데이트된 제목',
  '<p>업데이트된 내용</p>',
  existingPage.version.number
);

// 페이지 생성 또는 업데이트 (upsert)
await client.upsertPage(
  '페이지 제목',
  '<p>내용</p>'
);
```

## Confluence Storage Format

Confluence는 HTML과 유사하지만 자체적인 Storage Format을 사용합니다:

### 기본 HTML 태그
- `<h1>`, `<h2>`, `<h3>`: 헤더
- `<p>`: 단락
- `<strong>`, `<em>`: 볼드, 이탤릭
- `<ul>`, `<ol>`, `<li>`: 리스트
- `<a href="">`: 링크
- `<code>`: 인라인 코드

### Confluence 매크로

#### 코드 블록
```xml
<ac:structured-macro ac:name="code">
  <ac:parameter ac:name="language">javascript</ac:parameter>
  <ac:plain-text-body><![CDATA[
    console.log('Hello World');
  ]]></ac:plain-text-body>
</ac:structured-macro>
```

#### 정보 박스
```xml
<ac:structured-macro ac:name="info">
  <ac:rich-text-body>
    <p>중요한 정보를 표시합니다.</p>
  </ac:rich-text-body>
</ac:structured-macro>
```

다른 매크로: `note`, `warning`, `tip`

#### 접기/펼치기
```xml
<ac:structured-macro ac:name="expand">
  <ac:parameter ac:name="title">클릭하여 펼치기</ac:parameter>
  <ac:rich-text-body>
    <p>숨겨진 내용</p>
  </ac:rich-text-body>
</ac:structured-macro>
```

## 활용 예시

### 1. CI/CD 파이프라인 통합

GitHub Actions나 Jenkins에서 배포 후 자동으로 릴리스 노트를 Confluence에 업데이트:

```yaml
# .github/workflows/deploy.yml
- name: Update Confluence Release Notes
  run: |
    cd config/confluence
    npm install
    node scripts/sync-api-docs.js
```

### 2. 개발 문서 자동 생성

프로젝트의 README나 API 스펙을 주기적으로 Confluence에 동기화:

```javascript
import fs from 'fs';
import ConfluenceClient from './lib/confluence-client.js';

const client = new ConfluenceClient();
const readme = fs.readFileSync('../../README.md', 'utf8');
const htmlContent = client.markdownToStorage(readme);

await client.upsertPage('프로젝트 README', htmlContent);
```

### 3. 작업 로그 자동 기록

개발 진행 상황을 자동으로 Confluence에 기록:

```javascript
const logEntry = `
  <h3>${new Date().toLocaleDateString()}</h3>
  <ul>
    <li>구현 완료: 사용자 인증 기능</li>
    <li>버그 수정: 페이지 로딩 이슈</li>
    <li>다음 작업: 관리자 대시보드 개발</li>
  </ul>
`;

await client.upsertPage('개발 로그 - ' + new Date().toISOString().split('T')[0], logEntry);
```

## 문제 해결

### 401 Unauthorized 오류
- API 토큰이 올바른지 확인
- 이메일 주소가 정확한지 확인
- 토큰이 만료되지 않았는지 확인

### 404 Not Found 오류
- Space Key가 올바른지 확인
- 페이지가 실제로 존재하는지 확인
- 권한이 있는지 확인

### Network Error
- Confluence URL이 올바른지 확인
- 네트워크 연결 상태 확인
- 방화벽 설정 확인

## 참고 자료

- [Confluence REST API v1 문서](https://developer.atlassian.com/cloud/confluence/rest/v1/intro/)
- [Confluence Storage Format](https://confluence.atlassian.com/doc/confluence-storage-format-790796544.html)
- [Atlassian API Tokens](https://confluence.atlassian.com/cloud/api-tokens-938839638.html)

## 라이센스

이 프로젝트는 NoFee 워크스페이스의 일부입니다.
