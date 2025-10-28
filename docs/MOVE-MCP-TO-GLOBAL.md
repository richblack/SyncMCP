# 將專案級別的 MCP 移動到全域級別

## 📌 為什麼需要移動？

SyncMCP 工具目前**不支援專案級別的 MCP 配置**（Bug #13）。如果你的 MCP 是在專案目錄中新增的，它們不會被 SyncMCP 同步到其他客戶端（Roo Code、Claude Desktop、Gemini CLI）。

將 MCP 移動到全域級別後，SyncMCP 就能正常同步這些配置。

---

## 🔍 如何檢查 MCP 的位置

### 方法 1: 使用 jq 命令

```bash
# 列出全域 MCP
cat ~/.claude.json | jq '.mcpServers | keys'

# 列出當前專案的 MCP
cat ~/.claude.json | jq --arg pwd "$PWD" '.projects[$pwd].mcpServers | keys'

# 列出所有專案及其 MCP
cat ~/.claude.json | jq '.projects | to_entries[] | {project: .key, mcps: (.value.mcpServers | keys)}'
```

### 方法 2: 直接查看配置文件

```bash
# macOS/Linux
code ~/.claude.json

# 或使用任何文字編輯器
nano ~/.claude.json
```

查看結構：
```json
{
  "mcpServers": { ... },  // 全域 MCP
  "projects": {
    "/path/to/your/project": {
      "mcpServers": { ... }  // 專案級別 MCP
    }
  }
}
```

---

## 🚀 移動步驟

### 自動方法（推薦）

使用這個簡單的命令自動移動專案 MCP 到全域：

```bash
# 1. 切換到專案目錄
cd /Users/youlinhsieh/Documents/tech_projects/AIPM-Client

# 2. 列出當前專案的 MCP
claude mcp list

# 3. 對每個專案級別的 MCP 執行以下操作：
#    a. 記錄 MCP 配置
#    b. 刪除專案級別的 MCP
#    c. 在全域重新新增

# 以 chrome-devtools 為例：
claude mcp remove chrome-devtools

# 4. 切換到非專案目錄（確保新增到全域）
cd ~

# 5. 重新新增 MCP（這次會新增到全域）
claude mcp add chrome-devtools npx chrome-devtools-mcp@latest

# 6. 驗證 MCP 已在全域
cat ~/.claude.json | jq '.mcpServers | keys' | grep chrome-devtools

# 7. 同步到其他客戶端
syncmcp sync
```

---

### 手動方法（如果自動方法失敗）

#### 步驟 1: 備份配置文件

```bash
cp ~/.claude.json ~/.claude.json.backup.$(date +%Y%m%d_%H%M%S)
```

#### 步驟 2: 提取專案 MCP 配置

```bash
# 查看並記錄專案 MCP 的完整配置
cat ~/.claude.json | jq '.projects["/Users/youlinhsieh/Documents/tech_projects/AIPM-Client"].mcpServers'
```

輸出範例：
```json
{
  "chrome-devtools": {
    "type": "stdio",
    "command": "npx",
    "args": [
      "chrome-devtools-mcp@latest"
    ],
    "env": {}
  }
}
```

#### 步驟 3: 編輯配置文件

```bash
code ~/.claude.json
# 或
nano ~/.claude.json
```

手動操作：
1. 找到 `"mcpServers": {` 部分（在文件頂層，不在 projects 內）
2. 複製專案 MCP 的配置到這裡
3. 刪除 `projects[專案路徑].mcpServers` 中的該 MCP
4. 保存文件

**修改前**：
```json
{
  "mcpServers": {
    "context7": { ... },
    "notion": { ... }
  },
  "projects": {
    "/Users/youlinhsieh/Documents/tech_projects/AIPM-Client": {
      "mcpServers": {
        "chrome-devtools": {
          "type": "stdio",
          "command": "npx",
          "args": ["chrome-devtools-mcp@latest"]
        }
      }
    }
  }
}
```

**修改後**：
```json
{
  "mcpServers": {
    "context7": { ... },
    "notion": { ... },
    "chrome-devtools": {
      "type": "stdio",
      "command": "npx",
      "args": ["chrome-devtools-mcp@latest"],
      "env": {}
    }
  },
  "projects": {
    "/Users/youlinhsieh/Documents/tech_projects/AIPM-Client": {
      "mcpServers": {}
    }
  }
}
```

#### 步驟 4: 重啟 Claude Code

```bash
# 完全退出 Claude Code
# 然後重新啟動

# 或使用命令行
pkill -f "Claude Code"
claude --version  # 這會啟動新的實例
```

#### 步驟 5: 驗證

```bash
# 1. 檢查全域 MCP
claude mcp list

# 2. 或直接查看配置
cat ~/.claude.json | jq '.mcpServers | keys'

# 3. 確認專案 MCP 已清空或移除
cat ~/.claude.json | jq '.projects["/Users/youlinhsieh/Documents/tech_projects/AIPM-Client"].mcpServers'
```

預期輸出應該是 `{}` 或 null。

#### 步驟 6: 同步到其他客戶端

```bash
# 使用 SyncMCP 同步
syncmcp sync

# 或預覽同步
syncmcp sync --dry-run
```

---

## 📋 完整範例腳本

如果你有多個專案級別的 MCP 需要移動，使用這個腳本：

```bash
#!/bin/bash
# move-project-mcps-to-global.sh

PROJECT_PATH="/Users/youlinhsieh/Documents/tech_projects/AIPM-Client"
CONFIG_FILE="$HOME/.claude.json"

echo "📋 正在移動專案 MCP 到全域..."

# 1. 備份
echo "1️⃣ 備份配置文件..."
cp "$CONFIG_FILE" "${CONFIG_FILE}.backup.$(date +%Y%m%d_%H%M%S)"

# 2. 列出專案 MCP
echo "2️⃣ 檢查專案 MCP..."
PROJECT_MCPS=$(jq -r --arg path "$PROJECT_PATH" '.projects[$path].mcpServers | keys[]' "$CONFIG_FILE" 2>/dev/null)

if [ -z "$PROJECT_MCPS" ]; then
    echo "✅ 沒有專案級別的 MCP 需要移動"
    exit 0
fi

echo "📦 找到以下專案 MCP："
echo "$PROJECT_MCPS"

# 3. 對每個 MCP 執行移動
echo "3️⃣ 開始移動..."
cd "$PROJECT_PATH"

for MCP_NAME in $PROJECT_MCPS; do
    echo "  📤 移動 $MCP_NAME ..."

    # 刪除專案級別的 MCP
    claude mcp remove "$MCP_NAME" 2>/dev/null

    # 獲取 MCP 配置
    MCP_CONFIG=$(jq -r --arg path "$PROJECT_PATH" --arg name "$MCP_NAME" \
        '.projects[$path].mcpServers[$name]' "$CONFIG_FILE")

    # 提取 command 和 args（簡化版本，實際可能需要更複雜的邏輯）
    COMMAND=$(echo "$MCP_CONFIG" | jq -r '.command')
    ARGS=$(echo "$MCP_CONFIG" | jq -r '.args | join(" ")')

    # 在全域重新新增
    cd ~
    claude mcp add "$MCP_NAME" "$COMMAND" $ARGS

    echo "  ✅ $MCP_NAME 已移動到全域"
done

# 4. 驗證
echo "4️⃣ 驗證結果..."
echo "全域 MCP："
jq '.mcpServers | keys' "$CONFIG_FILE"

echo "專案 MCP："
jq --arg path "$PROJECT_PATH" '.projects[$path].mcpServers | keys' "$CONFIG_FILE"

# 5. 同步
echo "5️⃣ 同步到其他客戶端..."
syncmcp sync

echo "✅ 完成！"
```

使用方法：
```bash
chmod +x move-project-mcps-to-global.sh
./move-project-mcps-to-global.sh
```

---

## ✅ 驗證清單

移動完成後，確認以下事項：

- [ ] 執行 `claude mcp list` 可以看到移動的 MCP
- [ ] 執行 `cat ~/.claude.json | jq '.mcpServers | keys'` 顯示該 MCP
- [ ] 專案目錄的 `.mcpServers` 已清空或移除該 MCP
- [ ] 執行 `syncmcp list` 可以看到該 MCP
- [ ] 執行 `syncmcp sync` 成功同步
- [ ] 在 Roo Code/Claude Desktop 中可以使用該 MCP

---

## 🔧 常見問題

### Q1: 移動後 MCP 無法使用？

**檢查步驟**：
1. 重啟 Claude Code
2. 確認配置文件格式正確（使用 `jq . ~/.claude.json` 驗證 JSON）
3. 檢查 MCP 的 command 和 args 是否正確

### Q2: 如何恢復到專案級別？

如果你想撤銷，從備份恢復：
```bash
cp ~/.claude.json.backup.XXXXXX ~/.claude.json
# 重啟 Claude Code
```

### Q3: 移動後其他專案也能看到這個 MCP？

是的，這是**全域 MCP** 的特性。所有專案都能使用全域 MCP。如果你需要專案隔離，等待 SyncMCP 的 Bug #13 修復。

### Q4: 可以只移動部分 MCP 嗎？

可以，只對需要同步的 MCP 執行移動操作。專案特定的工具可以保留在專案級別。

### Q5: .mcp.json 文件怎麼處理？

如果專案有 `.mcp.json` 文件：
1. 這些 MCP 也是專案級別的
2. 需要手動將配置複製到 `~/.claude.json` 的 `mcpServers`
3. 可以選擇保留或刪除 `.mcp.json`

---

## 📚 相關文檔

- [Bug #13 報告](../rfp/BUG-13-project-level-mcp.md) - 詳細的技術說明
- [測試文檔](../user-requirements/docs/test.md) - 測試記錄和已知問題
- [SyncMCP README](../README.md) - 工具使用說明

---

## 💡 最佳實踐建議

### 應該放在全域的 MCP：
- ✅ 通用工具（filesystem, notion, context7）
- ✅ 需要跨客戶端同步的 MCP
- ✅ 團隊共享的 API 服務

### 可以保留在專案級別的 MCP：
- 📁 專案特定的測試工具
- 📁 僅該專案使用的私有 API
- 📁 實驗性的 MCP（不想同步到其他地方）

**注意**: 專案級別的 MCP 目前不會被 SyncMCP 同步。

---

**最後更新**: 2025-10-29
**相關 Issue**: Bug #13 - 不支援專案級別 MCP 配置
**狀態**: 臨時解決方案（等待正式修復）
