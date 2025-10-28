# 設計：通用 MCP 類型轉換系統

## 🎯 目標

建立一個**智能雙向轉換系統**，無論用戶在哪個客戶端安裝或修改 MCP，同步後所有客戶端都能正確載入。

## 📊 轉換矩陣

### 所有可能的來源類型

| 來源類型 | 可能出現在 | 說明 |
|---------|-----------|------|
| `stdio` | 所有客戶端 | 本地命令執行 |
| `http` | Claude Code | HTTP transport |
| `sse` | Claude Code | Server-Sent Events |
| `streamable-http` | Roo Code, Gemini | Roo Code 專有的串流 HTTP |
| 缺少 `type` | 任何客戶端 | 需要推斷類型 |

### 目標客戶端需求

| 目標客戶端 | 支援類型 | 不支援 | 特殊規則 |
|-----------|---------|--------|---------|
| **Claude Code** | `stdio`, `sse`, `http` | `streamable-http` | 需要移除 Roo 特有欄位 |
| **Roo Code** | `stdio`, `streamable-http` | - | 建議統一用 `streamable-http` |
| **Claude Desktop** | `stdio` | `http`, `sse`, `streamable-http` | 只保留 stdio，移除 type 欄位 |
| **Gemini CLI** | `stdio`, `streamable-http` | - | 僅全域配置 |

## 🔄 轉換邏輯

### 核心原則

1. **保留 stdio**：所有客戶端都支援，不需轉換
2. **推斷缺失類型**：根據配置內容推斷（有 `url` → 遠端，有 `command` → stdio）
3. **智能轉換遠端類型**：根據目標客戶端和是否有 headers 決定

### 轉換決策樹

```
輸入配置
    ↓
是否有 type？
    ↓
NO → 推斷類型
    - 有 url → 暫定為 'remote'
    - 有 command → 'stdio'
    ↓
YES → 使用現有 type
    ↓
根據目標客戶端轉換
    ↓
Claude Code:
    - stdio → stdio (保留)
    - streamable-http → http (有 headers) 或 sse (無 headers)
    - http → http (保留)
    - sse → sse (保留)
    ↓
Roo Code:
    - stdio → stdio (保留)
    - http → streamable-http
    - sse → streamable-http
    - streamable-http → streamable-http (保留)
    ↓
Claude Desktop:
    - stdio → stdio (保留，移除 type 欄位)
    - 其他 → 過濾掉 (return None)
    ↓
Gemini:
    - stdio → stdio (保留)
    - http → streamable-http
    - sse → streamable-http
    - streamable-http → streamable-http (保留)
```

## 💻 實作設計

### 函數 1: 推斷類型

```python
def infer_type(config: Dict[str, Any]) -> str:
    """推斷配置的類型

    Args:
        config: MCP 配置

    Returns:
        推斷的類型字串
    """
    if config.get('type'):
        return config['type']

    # 根據欄位推斷
    if 'url' in config:
        # 有 URL 表示遠端服務
        # 預設用最通用的 streamable-http
        return 'streamable-http'
    elif 'command' in config:
        return 'stdio'
    else:
        # 預設為 stdio
        return 'stdio'
```

### 函數 2: 通用轉換

```python
def normalize_server_config(
    self,
    config: Dict[str, Any],
    target_client: str
) -> Optional[Dict[str, Any]]:
    """通用的配置標準化函數

    支援所有客戶端之間的雙向轉換

    Args:
        config: 原始配置
        target_client: 目標客戶端
            - 'claude-code'
            - 'roo-code'
            - 'claude-desktop'
            - 'gemini'

    Returns:
        轉換後的配置，或 None 表示應過濾掉
    """
    normalized = config.copy()

    # 1. 推斷類型
    current_type = self.infer_type(normalized)

    # 2. stdio 類型特殊處理（所有客戶端都支援）
    if current_type == 'stdio':
        if target_client == 'claude-desktop':
            # Desktop 不需要 type 欄位
            normalized.pop('type', None)
        else:
            normalized['type'] = 'stdio'

        # 清理 Roo 特有欄位（如果目標不是 Roo）
        if target_client != 'roo-code':
            normalized.pop('autoApprove', None)
            normalized.pop('alwaysAllow', None)
            normalized.pop('disabled', None)

        return normalized

    # 3. 遠端類型轉換
    if target_client == 'claude-code':
        # Claude Code: streamable-http → http/sse
        if current_type == 'streamable-http':
            # 根據是否有 headers 決定
            if normalized.get('headers'):
                normalized['type'] = 'http'
            else:
                normalized['type'] = 'sse'
        elif current_type in ['http', 'sse']:
            # 保留原有類型
            normalized['type'] = current_type
        else:
            # 未知類型，預設為 sse
            normalized['type'] = 'sse'

        # 移除 Roo 特有欄位
        normalized.pop('autoApprove', None)
        normalized.pop('alwaysAllow', None)
        normalized.pop('disabled', None)

    elif target_client == 'roo-code':
        # Roo Code: http/sse → streamable-http
        if current_type in ['http', 'sse']:
            normalized['type'] = 'streamable-http'
        elif current_type == 'streamable-http':
            # 保留
            normalized['type'] = 'streamable-http'
        else:
            # 未知遠端類型，使用 streamable-http
            normalized['type'] = 'streamable-http'

    elif target_client == 'claude-desktop':
        # Claude Desktop: 只支援 stdio
        # 遠端類型全部過濾
        return None

    elif target_client == 'gemini':
        # Gemini: http/sse → streamable-http
        if current_type in ['http', 'sse']:
            normalized['type'] = 'streamable-http'
        elif current_type == 'streamable-http':
            # 保留
            normalized['type'] = 'streamable-http'
        else:
            # 未知遠端類型
            normalized['type'] = 'streamable-http'

        # 移除 Roo 特有欄位
        normalized.pop('autoApprove', None)
        normalized.pop('alwaysAllow', None)
        normalized.pop('disabled', None)

    return normalized
```

## 🧪 測試案例

### 場景 1: 用戶在 Roo Code 安裝新 MCP

```python
# 來源: Roo Code
roo_config = {
    "type": "streamable-http",
    "url": "https://mcp.canva.com/mcp",
    "alwaysAllow": ["tool1"]
}

# 同步到 Claude Code
result = normalize_server_config(roo_config, 'claude-code')
assert result == {
    "type": "sse",  # 無 headers → sse
    "url": "https://mcp.canva.com/mcp"
    # alwaysAllow 被移除
}

# 同步到 Claude Desktop
result = normalize_server_config(roo_config, 'claude-desktop')
assert result is None  # 遠端 MCP 被過濾

# 同步回 Roo Code
result = normalize_server_config(roo_config, 'roo-code')
assert result == roo_config  # 保持不變
```

### 場景 2: 用戶在 Claude Code 安裝新 MCP

```python
# 來源: Claude Code
claude_config = {
    "type": "http",
    "url": "https://mcp.context7.com/mcp",
    "headers": {"API_KEY": "xxx"}
}

# 同步到 Roo Code
result = normalize_server_config(claude_config, 'roo-code')
assert result == {
    "type": "streamable-http",  # http → streamable-http
    "url": "https://mcp.context7.com/mcp",
    "headers": {"API_KEY": "xxx"}
}

# 同步到 Gemini
result = normalize_server_config(claude_config, 'gemini')
assert result == {
    "type": "streamable-http",  # http → streamable-http
    "url": "https://mcp.context7.com/mcp",
    "headers": {"API_KEY": "xxx"}
}

# 同步回 Claude Code
result = normalize_server_config(claude_config, 'claude-code')
assert result == claude_config  # 保持不變
```

### 場景 3: 配置缺少 type 欄位

```python
# 來源: 任何客戶端（格式不完整）
incomplete_config = {
    "url": "https://mcp.example.com/mcp"
    # 缺少 type
}

# 同步到 Claude Code
result = normalize_server_config(incomplete_config, 'claude-code')
assert result == {
    "type": "sse",  # 推斷為遠端，無 headers → sse
    "url": "https://mcp.example.com/mcp"
}

# 同步到 Roo Code
result = normalize_server_config(incomplete_config, 'roo-code')
assert result == {
    "type": "streamable-http",  # 推斷為遠端 → streamable-http
    "url": "https://mcp.example.com/mcp"
}
```

### 場景 4: stdio 配置（最簡單）

```python
# 來源: 任何客戶端
stdio_config = {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "some-mcp-server"]
}

# 同步到所有客戶端都保持一致
for client in ['claude-code', 'roo-code', 'gemini']:
    result = normalize_server_config(stdio_config, client)
    assert result['type'] == 'stdio'
    assert result['command'] == 'npx'

# Claude Desktop 特殊：移除 type
result = normalize_server_config(stdio_config, 'claude-desktop')
assert 'type' not in result
assert result['command'] == 'npx'
```

## 📋 完整的轉換矩陣表

| 來源 Type | → Claude Code | → Roo Code | → Desktop | → Gemini |
|----------|--------------|-----------|-----------|----------|
| `stdio` | `stdio` | `stdio` | (無 type) | `stdio` |
| `http` | `http` | `streamable-http` | 過濾 | `streamable-http` |
| `sse` | `sse` | `streamable-http` | 過濾 | `streamable-http` |
| `streamable-http` (無 headers) | `sse` | `streamable-http` | 過濾 | `streamable-http` |
| `streamable-http` (有 headers) | `http` | `streamable-http` | 過濾 | `streamable-http` |
| 缺少 (有 url) | `sse` | `streamable-http` | 過濾 | `streamable-http` |
| 缺少 (有 command) | `stdio` | `stdio` | (無 type) | `stdio` |

## 🎯 實作檢查清單

- [ ] 實作 `infer_type()` 函數
- [ ] 重寫 `normalize_server_config()` 支援 `target_client` 參數
- [ ] 更新 `write_claude_code_config()` 調用新函數
- [ ] 更新 `write_roo_code_config()` 調用新函數
- [ ] 更新 `write_claude_desktop_config()` 調用新函數
- [ ] 更新 `write_gemini_config()` 調用新函數（如果有）
- [ ] 添加所有測試案例
- [ ] 測試雙向同步（Roo ↔ Claude Code）
- [ ] 測試邊緣案例（缺少 type、未知 type）
- [ ] 更新文檔說明轉換邏輯

## 🚀 預期結果

無論用戶在哪個客戶端安裝或修改 MCP：

✅ **Claude Code** 永遠不會看到 `streamable-http`
✅ **Roo Code** 所有遠端 MCP 都是 `streamable-http`
✅ **Claude Desktop** 只包含 stdio MCP
✅ **Gemini** 使用 `streamable-http` 作為標準遠端類型

同步是**冪等的**：多次同步不會改變結果

---

**設計者**: Claude (Sonnet 4.5)
**時間**: 2025-10-26 18:00
