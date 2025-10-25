import axios from 'axios';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Load .env from config directory (../../config/confluence.env)
dotenv.config({ path: resolve(__dirname, '../../../config/confluence.env') });

/**
 * Confluence REST API Client
 * @see https://developer.atlassian.com/cloud/confluence/rest/v1/intro/
 */
class ConfluenceClient {
  constructor() {
    this.baseUrl = process.env.CONFLUENCE_BASE_URL;
    this.email = process.env.CONFLUENCE_EMAIL;
    this.apiToken = process.env.CONFLUENCE_API_TOKEN;
    this.spaceKey = process.env.CONFLUENCE_SPACE_KEY;

    if (!this.baseUrl || !this.email || !this.apiToken) {
      throw new Error('Missing required environment variables. Please check your .env file.');
    }

    // API v1 엔드포인트
    this.apiUrl = `${this.baseUrl}/rest/api`;

    // Axios 인스턴스 생성
    this.client = axios.create({
      baseURL: this.apiUrl,
      auth: {
        username: this.email,
        password: this.apiToken,
      },
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    });
  }

  /**
   * 페이지 생성
   * @param {string} title - 페이지 제목
   * @param {string} content - 페이지 내용 (Confluence Storage Format)
   * @param {string} spaceKey - 스페이스 키 (선택사항, 기본값은 환경변수)
   * @param {string|null} parentId - 부모 페이지 ID (선택사항)
   * @returns {Promise<Object>} 생성된 페이지 정보
   */
  async createPage(title, content, spaceKey = null, parentId = null) {
    const space = spaceKey || this.spaceKey;

    const data = {
      type: 'page',
      title: title,
      space: {
        key: space,
      },
      body: {
        storage: {
          value: content,
          representation: 'storage',
        },
      },
    };

    // 부모 페이지가 있으면 추가
    if (parentId) {
      data.ancestors = [{ id: parentId }];
    }

    try {
      const response = await this.client.post('/content', data);
      return response.data;
    } catch (error) {
      this.handleError(error, 'createPage');
    }
  }

  /**
   * 페이지 업데이트
   * @param {string} pageId - 페이지 ID
   * @param {string} title - 새로운 제목
   * @param {string} content - 새로운 내용
   * @param {number} version - 현재 버전 번호
   * @returns {Promise<Object>} 업데이트된 페이지 정보
   */
  async updatePage(pageId, title, content, version) {
    const data = {
      version: {
        number: version + 1,
      },
      title: title,
      type: 'page',
      body: {
        storage: {
          value: content,
          representation: 'storage',
        },
      },
    };

    try {
      const response = await this.client.put(`/content/${pageId}`, data);
      return response.data;
    } catch (error) {
      this.handleError(error, 'updatePage');
    }
  }

  /**
   * 페이지 정보 조회
   * @param {string} pageId - 페이지 ID
   * @param {Array<string>} expand - 확장할 정보 (예: ['body.storage', 'version'])
   * @returns {Promise<Object>} 페이지 정보
   */
  async getPage(pageId, expand = ['body.storage', 'version']) {
    try {
      const response = await this.client.get(`/content/${pageId}`, {
        params: {
          expand: expand.join(','),
        },
      });
      return response.data;
    } catch (error) {
      this.handleError(error, 'getPage');
    }
  }

  /**
   * 제목으로 페이지 검색
   * @param {string} title - 페이지 제목
   * @param {string} spaceKey - 스페이스 키 (선택사항)
   * @returns {Promise<Object|null>} 페이지 정보 (없으면 null)
   */
  async getPageByTitle(title, spaceKey = null) {
    const space = spaceKey || this.spaceKey;

    try {
      const response = await this.client.get('/content', {
        params: {
          title: title,
          spaceKey: space,
          expand: 'body.storage,version',
        },
      });

      if (response.data.results.length > 0) {
        return response.data.results[0];
      }
      return null;
    } catch (error) {
      this.handleError(error, 'getPageByTitle');
    }
  }

  /**
   * 스페이스의 모든 페이지 목록 조회
   * @param {string} spaceKey - 스페이스 키 (선택사항)
   * @param {number} limit - 결과 개수 제한
   * @returns {Promise<Array>} 페이지 목록
   */
  async listPages(spaceKey = null, limit = 25) {
    const space = spaceKey || this.spaceKey;

    try {
      const response = await this.client.get('/content', {
        params: {
          spaceKey: space,
          limit: limit,
          expand: 'version',
        },
      });
      return response.data.results;
    } catch (error) {
      this.handleError(error, 'listPages');
    }
  }

  /**
   * 페이지 삭제
   * @param {string} pageId - 페이지 ID
   * @returns {Promise<void>}
   */
  async deletePage(pageId) {
    try {
      await this.client.delete(`/content/${pageId}`);
    } catch (error) {
      this.handleError(error, 'deletePage');
    }
  }

  /**
   * 마크다운을 Confluence Storage Format으로 변환 (간단한 버전)
   * @param {string} markdown - 마크다운 텍스트
   * @returns {string} Confluence Storage Format HTML
   */
  markdownToStorage(markdown) {
    let html = markdown
      // 헤더
      .replace(/^### (.*$)/gim, '<h3>$1</h3>')
      .replace(/^## (.*$)/gim, '<h2>$1</h2>')
      .replace(/^# (.*$)/gim, '<h1>$1</h1>')
      // 볼드
      .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
      // 이탤릭
      .replace(/\*(.*)\*/gim, '<em>$1</em>')
      // 링크
      .replace(/\[([^\]]+)\]\(([^\)]+)\)/gim, '<a href="$2">$1</a>')
      // 코드 블록
      .replace(/```(\w+)?\n([\s\S]*?)```/gim, '<ac:structured-macro ac:name="code"><ac:parameter ac:name="language">$1</ac:parameter><ac:plain-text-body><![CDATA[$2]]></ac:plain-text-body></ac:structured-macro>')
      // 인라인 코드
      .replace(/`([^`]+)`/gim, '<code>$1</code>')
      // 순서 없는 리스트
      .replace(/^\* (.*$)/gim, '<li>$1</li>')
      .replace(/(<li>.*<\/li>)/gim, '<ul>$1</ul>')
      // 줄바꿈
      .replace(/\n/gim, '<br/>');

    return html;
  }

  /**
   * 페이지 생성 또는 업데이트 (upsert)
   * @param {string} title - 페이지 제목
   * @param {string} content - 페이지 내용
   * @param {string} spaceKey - 스페이스 키 (선택사항)
   * @returns {Promise<Object>} 페이지 정보
   */
  async upsertPage(title, content, spaceKey = null) {
    const existingPage = await this.getPageByTitle(title, spaceKey);

    if (existingPage) {
      console.log(`페이지 "${title}" 업데이트 중...`);
      return await this.updatePage(
        existingPage.id,
        title,
        content,
        existingPage.version.number
      );
    } else {
      console.log(`페이지 "${title}" 생성 중...`);
      return await this.createPage(title, content, spaceKey);
    }
  }

  /**
   * 에러 처리
   * @private
   */
  handleError(error, method) {
    if (error.response) {
      console.error(`[${method}] API Error:`, error.response.status, error.response.data);
      throw new Error(`Confluence API Error: ${error.response.status} - ${JSON.stringify(error.response.data)}`);
    } else if (error.request) {
      console.error(`[${method}] Network Error:`, error.message);
      throw new Error(`Network Error: ${error.message}`);
    } else {
      console.error(`[${method}] Error:`, error.message);
      throw error;
    }
  }
}

export default ConfluenceClient;
