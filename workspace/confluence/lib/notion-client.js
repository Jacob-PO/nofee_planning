import { Client } from '@notionhq/client';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Load .env from config directory
dotenv.config({ path: resolve(__dirname, '../../../config/confluence.env') });

/**
 * Notion API Client
 * @see https://developers.notion.com/
 */
class NotionClient {
  constructor(integrationToken = null) {
    // Notion 토큰은 환경변수 또는 파라미터로 전달
    this.token = integrationToken || process.env.NOTION_INTEGRATION_TOKEN;

    if (!this.token) {
      throw new Error('Missing Notion integration token. Please set NOTION_INTEGRATION_TOKEN in .env file.');
    }

    this.client = new Client({
      auth: this.token,
    });
  }

  /**
   * 페이지 ID 추출 (URL에서)
   * @param {string} pageUrl - Notion 페이지 URL
   * @returns {string} 페이지 ID
   */
  extractPageId(pageUrl) {
    // URL 형식: https://www.notion.so/jacobkim/2941d254f8088019aba3fe6126e89874
    // 또는: https://www.notion.so/2941d254f8088019aba3fe6126e89874
    const match = pageUrl.match(/([a-f0-9]{32})/);
    if (!match) {
      throw new Error('Invalid Notion page URL. Could not extract page ID.');
    }

    // 하이픈 추가하여 표준 UUID 형식으로 변환
    const id = match[1];
    return `${id.slice(0, 8)}-${id.slice(8, 12)}-${id.slice(12, 16)}-${id.slice(16, 20)}-${id.slice(20)}`;
  }

  /**
   * 페이지 조회
   * @param {string} pageId - 페이지 ID
   * @returns {Promise<Object>} 페이지 정보
   */
  async getPage(pageId) {
    try {
      const response = await this.client.pages.retrieve({ page_id: pageId });
      return response;
    } catch (error) {
      this.handleError(error, 'getPage');
    }
  }

  /**
   * 데이터베이스 생성
   * @param {string} parentPageId - 부모 페이지 ID
   * @param {string} title - 데이터베이스 제목
   * @param {Object} properties - 데이터베이스 속성 정의
   * @returns {Promise<Object>} 생성된 데이터베이스 정보
   */
  async createDatabase(parentPageId, title, properties) {
    try {
      const response = await this.client.databases.create({
        parent: {
          type: 'page_id',
          page_id: parentPageId,
        },
        title: [
          {
            type: 'text',
            text: {
              content: title,
            },
          },
        ],
        properties: properties,
      });
      return response;
    } catch (error) {
      this.handleError(error, 'createDatabase');
    }
  }

  /**
   * 데이터베이스 조회
   * @param {string} databaseId - 데이터베이스 ID
   * @returns {Promise<Object>} 데이터베이스 정보
   */
  async getDatabase(databaseId) {
    try {
      const response = await this.client.databases.retrieve({
        database_id: databaseId,
      });
      return response;
    } catch (error) {
      this.handleError(error, 'getDatabase');
    }
  }

  /**
   * 데이터베이스에 페이지(row) 추가
   * @param {string} databaseId - 데이터베이스 ID
   * @param {Object} properties - 페이지 속성
   * @returns {Promise<Object>} 생성된 페이지 정보
   */
  async createDatabasePage(databaseId, properties) {
    try {
      const response = await this.client.pages.create({
        parent: {
          type: 'database_id',
          database_id: databaseId,
        },
        properties: properties,
      });
      return response;
    } catch (error) {
      this.handleError(error, 'createDatabasePage');
    }
  }

  /**
   * 데이터베이스 쿼리
   * @param {string} databaseId - 데이터베이스 ID
   * @param {Object} filter - 필터 조건
   * @param {Array} sorts - 정렬 조건
   * @returns {Promise<Array>} 쿼리 결과
   */
  async queryDatabase(databaseId, filter = null, sorts = null) {
    try {
      const params = {
        database_id: databaseId,
      };

      if (filter) params.filter = filter;
      if (sorts) params.sorts = sorts;

      const response = await this.client.databases.query(params);
      return response.results;
    } catch (error) {
      this.handleError(error, 'queryDatabase');
    }
  }

  /**
   * 페이지의 블록 조회
   * @param {string} blockId - 블록 ID (페이지 ID와 동일)
   * @returns {Promise<Array>} 블록 목록
   */
  async getBlocks(blockId) {
    try {
      const response = await this.client.blocks.children.list({
        block_id: blockId,
        page_size: 100,
      });
      return response.results;
    } catch (error) {
      this.handleError(error, 'getBlocks');
    }
  }

  /**
   * 페이지에 블록 추가
   * @param {string} pageId - 페이지 ID
   * @param {Array} blocks - 추가할 블록 배열
   * @returns {Promise<Object>} 응답
   */
  async appendBlocks(pageId, blocks) {
    try {
      const response = await this.client.blocks.children.append({
        block_id: pageId,
        children: blocks,
      });
      return response;
    } catch (error) {
      this.handleError(error, 'appendBlocks');
    }
  }

  /**
   * 기존 블록 모두 삭제 후 새 블록 추가
   * @param {string} pageId - 페이지 ID
   * @param {Array} newBlocks - 새 블록 배열
   * @returns {Promise<Object>} 응답
   */
  async replaceBlocks(pageId, newBlocks) {
    try {
      // 1. 기존 블록 가져오기
      const existingBlocks = await this.getBlocks(pageId);

      // 2. 기존 블록 삭제
      for (const block of existingBlocks) {
        await this.client.blocks.delete({ block_id: block.id });
      }

      // 3. 새 블록 추가 (100개씩 나눠서)
      const BATCH_SIZE = 100;
      const results = [];

      for (let i = 0; i < newBlocks.length; i += BATCH_SIZE) {
        const batch = newBlocks.slice(i, i + BATCH_SIZE);
        console.log(`블록 추가 중... (${i + 1}-${Math.min(i + BATCH_SIZE, newBlocks.length)} / ${newBlocks.length})`);
        const result = await this.appendBlocks(pageId, batch);
        results.push(result);

        // API rate limit 방지를 위한 짧은 대기
        if (i + BATCH_SIZE < newBlocks.length) {
          await new Promise(resolve => setTimeout(resolve, 300));
        }
      }

      return results;
    } catch (error) {
      this.handleError(error, 'replaceBlocks');
    }
  }

  /**
   * 페이지 업데이트 (제목, 아이콘 등)
   * @param {string} pageId - 페이지 ID
   * @param {Object} properties - 업데이트할 속성
   * @returns {Promise<Object>} 응답
   */
  async updatePage(pageId, properties) {
    try {
      const response = await this.client.pages.update({
        page_id: pageId,
        properties: properties,
      });
      return response;
    } catch (error) {
      this.handleError(error, 'updatePage');
    }
  }

  /**
   * Heading 블록 생성
   * @param {number} level - 1, 2, 3
   * @param {string} text - 텍스트
   * @returns {Object} Notion 블록 객체
   */
  createHeading(level, text) {
    const type = `heading_${level}`;
    return {
      object: 'block',
      type: type,
      [type]: {
        rich_text: [{ type: 'text', text: { content: text } }],
      },
    };
  }

  /**
   * Paragraph 블록 생성
   * @param {string} text - 텍스트
   * @param {boolean} bold - 볼드 여부
   * @returns {Object} Notion 블록 객체
   */
  createParagraph(text, bold = false) {
    return {
      object: 'block',
      type: 'paragraph',
      paragraph: {
        rich_text: [
          {
            type: 'text',
            text: { content: text },
            annotations: { bold: bold },
          },
        ],
      },
    };
  }

  /**
   * Bulleted List 블록 생성
   * @param {string} text - 텍스트
   * @returns {Object} Notion 블록 객체
   */
  createBulletedList(text) {
    return {
      object: 'block',
      type: 'bulleted_list_item',
      bulleted_list_item: {
        rich_text: [{ type: 'text', text: { content: text } }],
      },
    };
  }

  /**
   * Numbered List 블록 생성
   * @param {string} text - 텍스트
   * @returns {Object} Notion 블록 객체
   */
  createNumberedList(text) {
    return {
      object: 'block',
      type: 'numbered_list_item',
      numbered_list_item: {
        rich_text: [{ type: 'text', text: { content: text } }],
      },
    };
  }

  /**
   * Callout 블록 생성 (info, warning, tip 등)
   * @param {string} text - 텍스트
   * @param {string} emoji - 이모지 (기본: 💡)
   * @returns {Object} Notion 블록 객체
   */
  createCallout(text, emoji = '💡') {
    return {
      object: 'block',
      type: 'callout',
      callout: {
        rich_text: [{ type: 'text', text: { content: text } }],
        icon: { type: 'emoji', emoji: emoji },
      },
    };
  }

  /**
   * Divider 블록 생성
   * @returns {Object} Notion 블록 객체
   */
  createDivider() {
    return {
      object: 'block',
      type: 'divider',
      divider: {},
    };
  }

  /**
   * Table 블록 생성
   * @param {number} tableWidth - 테이블 열 개수
   * @param {Array<Array<string>>} rows - 행 데이터
   * @returns {Object} Notion 블록 객체
   */
  createTable(tableWidth, rows) {
    const tableRows = rows.map((row) => ({
      type: 'table_row',
      table_row: {
        cells: row.map((cell) => [{ type: 'text', text: { content: cell } }]),
      },
    }));

    return {
      object: 'block',
      type: 'table',
      table: {
        table_width: tableWidth,
        has_column_header: true,
        has_row_header: false,
        children: tableRows,
      },
    };
  }

  /**
   * 에러 처리
   * @private
   */
  handleError(error, method) {
    console.error(`[${method}] Notion API Error:`, error.message);
    if (error.body) {
      console.error('Error details:', JSON.stringify(error.body, null, 2));
    }
    throw error;
  }
}

export default NotionClient;
