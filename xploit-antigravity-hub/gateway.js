const http = require('http');
const https = require('https');
const url = require('url');

/**
 * Universal Model Gateway Adapter
 * Bridges Google Gemini Protobuf/JSON schema <-> OpenAI/Ollama/DeepSeek/OpenRouter schema.
 */

// Convert Gemini contents array to OpenAI messages array
function geminiToOpenAIMessages(contents = []) {
  const messages = [];

  for (const item of contents) {
    const role = (item.role === 'model' || item.role === 'assistant') ? 'assistant' : 'user';
    let text = '';

    if (Array.isArray(item.parts)) {
      text = item.parts
        .map(p => (typeof p === 'string' ? p : p.text || ''))
        .filter(Boolean)
        .join('\n');
    } else if (typeof item.parts === 'string') {
      text = item.parts;
    }

    if (text) {
      messages.push({ role, content: text });
    }
  }

  if (messages.length === 0) {
    messages.push({ role: 'user', content: 'Hello' });
  }

  return messages;
}

// Convert OpenAI streaming chunk to Gemini streaming candidate chunk
function openAIDeltaToGeminiChunk(deltaContent, isFirst = false, isLast = false) {
  return JSON.stringify({
    candidates: [
      {
        content: {
          parts: [{ text: deltaContent || '' }],
          role: 'model'
        },
        finishReason: isLast ? 'STOP' : undefined,
        index: 0
      }
    ],
    usageMetadata: isLast ? { candidatesTokenCount: 1, promptTokenCount: 1, totalTokenCount: 2 } : undefined
  });
}

// Test connection to provider
async function testProviderConnection(config) {
  const start = Date.now();
  const provider = config.provider || 'ollama';
  let targetUrl = config.endpoint || 'http://127.0.0.1:11434/v1';

  if (provider === 'deepseek') {
    targetUrl = 'https://api.deepseek.com/v1';
  } else if (provider === 'openrouter') {
    targetUrl = 'https://openrouter.ai/api/v1';
  }

  if (!targetUrl.endsWith('/chat/completions')) {
    targetUrl = targetUrl.replace(/\/+$/, '') + '/chat/completions';
  }

  const payload = JSON.stringify({
    model: config.model || (provider === 'deepseek' ? 'deepseek-chat' : 'llama3'),
    messages: [{ role: 'user', content: 'ping' }],
    max_tokens: 2
  });

  const parsed = new URL(targetUrl);
  const isHttps = parsed.protocol === 'https:';
  const client = isHttps ? https : http;

  const headers = {
    'Content-Type': 'application/json',
    'Content-Length': Buffer.byteLength(payload),
    'HTTP-Referer': 'https://github.com/asrarkhann116-ops/red-gravity',
    'X-Title': 'Red Gravity Gateway'
  };

  if (config.apiKey) {
    headers['Authorization'] = `Bearer ${config.apiKey}`;
  }

  return new Promise((resolve) => {
    const req = client.request(targetUrl, { method: 'POST', headers, timeout: 7000 }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        const latencyMs = Date.now() - start;
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve({
            success: true,
            statusCode: res.statusCode,
            latencyMs,
            message: `Connected to ${provider} in ${latencyMs}ms.`,
            endpoint: targetUrl
          });
        } else {
          resolve({
            success: false,
            statusCode: res.statusCode,
            latencyMs,
            error: `Target returned HTTP ${res.statusCode}: ${data.substring(0, 150)}`
          });
        }
      });
    });

    req.on('error', (err) => {
      resolve({
        success: false,
        latencyMs: Date.now() - start,
        error: `Connection error: ${err.message}`
      });
    });

    req.on('timeout', () => {
      req.destroy();
      resolve({
        success: false,
        latencyMs: Date.now() - start,
        error: 'Connection timed out (7000ms).'
      });
    });

    req.write(payload);
    req.end();
  });
}

// Proxy streaming request from Antigravity to target provider
function proxyGeminiToOpenAI(req, res, config) {
  let bodyStr = '';
  req.on('data', chunk => bodyStr += chunk);
  req.on('end', () => {
    let geminiPayload = {};
    try {
      geminiPayload = JSON.parse(bodyStr || '{}');
    } catch (e) {
      geminiPayload = {};
    }

    const messages = geminiToOpenAIMessages(geminiPayload.contents || []);
    const provider = config.provider || 'ollama';
    let targetUrl = config.endpoint || 'http://127.0.0.1:11434/v1';

    if (provider === 'deepseek') {
      targetUrl = 'https://api.deepseek.com/v1';
    } else if (provider === 'openrouter') {
      targetUrl = 'https://openrouter.ai/api/v1';
    }

    if (!targetUrl.endsWith('/chat/completions')) {
      targetUrl = targetUrl.replace(/\/+$/, '') + '/chat/completions';
    }

    const targetModel = config.model || (provider === 'deepseek' ? 'deepseek-chat' : 'llama3');
    const openAIPayload = JSON.stringify({
      model: targetModel,
      stream: true,
      messages,
      temperature: geminiPayload.generationConfig?.temperature || 0.7,
      max_tokens: geminiPayload.generationConfig?.maxOutputTokens || 4096
    });

    const parsed = new URL(targetUrl);
    const client = parsed.protocol === 'https:' ? https : http;

    const headers = {
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(openAIPayload),
      'HTTP-Referer': 'https://github.com/asrarkhann116-ops/red-gravity',
      'X-Title': 'Red Gravity Gateway'
    };
    if (config.apiKey) {
      headers['Authorization'] = `Bearer ${config.apiKey}`;
    }

    // Set streaming headers for Antigravity IDE
    res.writeHead(200, {
      'Content-Type': 'text/event-stream; charset=utf-8',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'Access-Control-Allow-Origin': '*'
    });

    const proxyReq = client.request(targetUrl, { method: 'POST', headers }, (proxyRes) => {
      let buffer = '';

      proxyRes.on('data', (chunk) => {
        buffer += chunk.toString();
        const lines = buffer.split('\n');
        buffer = lines.pop(); // Keep unfinished line

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed || !trimmed.startsWith('data:')) continue;
          if (trimmed === 'data: [DONE]') {
            res.write(`data: ${openAIDeltaToGeminiChunk('', false, true)}\n\n`);
            continue;
          }

          try {
            const parsedChunk = JSON.parse(trimmed.slice(5).trim());
            const textDelta = parsedChunk.choices?.[0]?.delta?.content || '';
            if (textDelta) {
              const geminiChunk = openAIDeltaToGeminiChunk(textDelta, false, false);
              res.write(`data: ${geminiChunk}\n\n`);
            }
          } catch(e) {}
        }
      });

      proxyRes.on('end', () => {
        res.end();
      });
    });

    proxyReq.on('error', (err) => {
      res.write(`data: ${JSON.stringify({ error: err.message })}\n\n`);
      res.end();
    });

    proxyReq.write(openAIPayload);
    proxyReq.end();
  });
}

module.exports = {
  geminiToOpenAIMessages,
  openAIDeltaToGeminiChunk,
  testProviderConnection,
  proxyGeminiToOpenAI
};

