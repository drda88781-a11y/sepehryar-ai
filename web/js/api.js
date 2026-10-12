/**
 * Sepehryar AI Enterprise - Unified API Client
 * Manages network communication, token injection, and health checks.
 */

const API_CONFIG = {
  baseUrl: window.location.origin,
  token: 'sepehryar-local-token-change-in-prod',
  defaultDb: 'Sepehr_Main2_1405'
};

class SepehryarApiClient {
  constructor(config = API_CONFIG) {
    this.config = config;
  }

  getHeaders() {
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${this.config.token}`,
      'bypass-tunnel-reminder': 'true'
    };
  }

  /**
   * Health probe check
   */
  async checkHealth() {
    try {
      const res = await fetch(`${this.config.baseUrl}/health`, {
        headers: { 'bypass-tunnel-reminder': 'true' }
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      console.warn('Health check failed:', err);
      return { status: 'error', message: err.message };
    }
  }

  /**
   * Hardware & DB system diagnostics
   */
  async getDiagnostics() {
    const res = await fetch(`${this.config.baseUrl}/api/system/health`, {
      headers: this.getHeaders()
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  }

  /**
   * Reset conversation session
   */
  resetChatSession() {
    this.currentSessionId = 'session_' + Date.now().toString(36) + '_' + Math.random().toString(36).substring(2, 7);
  }

  /**
   * AI Chat Interaction (Autonomous Smart Agent)
   */
  async sendChat(query, database = null, sessionId = null, thinkingMode = 'balanced') {
    if (!this.currentSessionId) {
      this.resetChatSession();
    }
    const payload = {
      query: query.trim(),
      session_id: sessionId || this.currentSessionId,
      database: database || this.config.defaultDb,
      thinking_mode: thinkingMode
    };

    const res = await fetch(`${this.config.baseUrl}/api/chat`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `خطای سرور (${res.status})`);
    }

    return await res.json();
  }

  /**
   * Real-time Streaming AI Chat with Live Thinking Events (SSE)
   */
  async sendChatStream(query, database = null, onToken = null, onDone = null, onError = null, onThinkingStep = null, onThinkingDone = null, thinkingMode = 'balanced') {
    if (!this.currentSessionId) {
      this.resetChatSession();
    }
    const payload = {
      query: query.trim(),
      session_id: this.currentSessionId,
      database: database || this.config.defaultDb,
      thinking_mode: thinkingMode
    };

    try {
      const res = await fetch(`${this.config.baseUrl}/api/chat/stream`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `خطای سرور (${res.status})`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop();

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith('data: ')) {
            const jsonStr = trimmed.substring(6).trim();
            if (!jsonStr) continue;
            try {
              const data = JSON.parse(jsonStr);
              if (data.type === 'thinking_step' && onThinkingStep) {
                onThinkingStep(data);
              } else if (data.type === 'thinking_done' && onThinkingDone) {
                onThinkingDone(data);
              } else if (data.type === 'token' && onToken && data.content) {
                onToken(data.content);
              } else if (data.type === 'done' && onDone) {
                onDone();
              } else if (data.type === 'error' && onError) {
                onError(new Error(data.error || 'خطای استریم'));
              }
            } catch (e) {
              // Ignore partial JSON parse
            }
          }
        }
      }

      if (onDone) onDone();
    } catch (err) {
      if (onError) onError(err);
      else throw err;
    }
  }

  /**
   * Safe Read-Only SQL Query execution
   */
  async executeSql(sql, database = null, maxRows = 50) {
    const payload = {
      sql: sql.trim(),
      database: database || this.config.defaultDb,
      max_rows: maxRows
    };

    const res = await fetch(`${this.config.baseUrl}/api/sql/execute-readonly`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `خطا در اجرای کوئری (${res.status})`);
    }

    return await res.json();
  }

  /**
   * Connect to SQL Server database on demand
   */
  async connectDatabase(database = null) {
    const res = await fetch(`${this.config.baseUrl}/api/database/connect`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ database: database || this.config.defaultDb })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `خطای اتصال (${res.status})`);
    }
    return await res.json();
  }

  /**
   * Disconnect from SQL Server database
   */
  async disconnectDatabase() {
    const res = await fetch(`${this.config.baseUrl}/api/database/disconnect`, {
      method: 'POST',
      headers: this.getHeaders()
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `خطای قطع اتصال (${res.status})`);
    }
    return await res.json();
  }

  /**
   * Get current database connection status
   */
  async getDatabaseStatus() {
    const res = await fetch(`${this.config.baseUrl}/api/database/status`, {
      headers: this.getHeaders()
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  }
}

// Export singleton
window.apiClient = new SepehryarApiClient();
