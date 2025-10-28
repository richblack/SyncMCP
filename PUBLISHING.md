# SyncMCP 發布指南

## 📦 發布準備清單

### 1. 版本更新

在 `pyproject.toml` 中更新版本號：

```toml
[project]
version = "2.0.0"  # 移除 -dev 後綴
```

### 2. 更新文檔

- [ ] 更新 `CHANGELOG.md` 記錄所有變更
- [ ] 確認 `README.md` 的安裝指南正確
- [ ] 檢查所有文檔中的範例代碼可執行
- [ ] 更新 GitHub repository URL

### 3. 代碼品質檢查

```bash
# 執行所有品質檢查
make quality

# 執行測試
make test-cov

# 建構套件
make build

# 檢查套件品質
make build-check
```

### 4. 提交變更

```bash
git add .
git commit -m "chore: prepare for v2.0.0 release"
git push origin main
```

## 🚀 發布到 PyPI

### 前提條件

1. **註冊 PyPI 帳號**
   - 訪問 https://pypi.org/account/register/
   - 驗證 email

2. **設定 PyPI API Token**
   ```bash
   # 登入 PyPI 並建立 API token
   # https://pypi.org/manage/account/token/

   # 儲存 token 到 ~/.pypirc
   [pypi]
   username = __token__
   password = pypi-xxx...
   ```

### 發布步驟

#### 1. 清理舊的建構產物

```bash
rm -rf dist/ build/ *.egg-info
```

#### 2. 建構套件

```bash
python3.12 -m build
```

這會建立：
- `dist/syncmcp-2.0.0-py3-none-any.whl` (wheel)
- `dist/syncmcp-2.0.0.tar.gz` (source distribution)

#### 3. 檢查套件品質

```bash
python3.12 -m twine check dist/*
```

確保顯示：
```
Checking dist/syncmcp-2.0.0-py3-none-any.whl: PASSED
Checking dist/syncmcp-2.0.0.tar.gz: PASSED
```

#### 4. 測試上傳到 TestPyPI（可選）

```bash
# 上傳到 TestPyPI
python3.12 -m twine upload --repository testpypi dist/*

# 測試安裝
pip install --index-url https://test.pypi.org/simple/ syncmcp
```

#### 5. 正式上傳到 PyPI

```bash
python3.12 -m twine upload dist/*
```

輸入 username: `__token__`
輸入 password: `pypi-xxx...`（你的 API token）

#### 6. 驗證發布

訪問 https://pypi.org/project/syncmcp/ 確認套件已上傳。

測試安裝：
```bash
pip install syncmcp
syncmcp --version
```

## 🏷️ GitHub Release

### 1. 建立 Git Tag

```bash
git tag -a v2.0.0 -m "Release v2.0.0"
git push origin v2.0.0
```

### 2. 建立 GitHub Release

訪問 https://github.com/yourusername/SyncMCP/releases/new

填寫：
- **Tag**: v2.0.0
- **Release title**: SyncMCP v2.0.0 - Intelligent MCP Configuration Sync
- **Description**: 參考 CHANGELOG.md 內容

範例 Release Notes：
```markdown
## 🎉 SyncMCP v2.0.0

### ✨ 主要功能

- **智能配置同步**：自動在 Claude Code、Roo Code、Claude Desktop、Gemini CLI 之間同步 MCP 配置
- **差異檢測**：智能識別配置變更（新增/移除/修改）
- **自動備份**：同步前自動備份，支援一鍵恢復
- **互動式 TUI**：友善的終端使用者介面
- **MCP Server**：提供 LLM 工具整合
- **完整 CLI**：`syncmcp sync`, `status`, `diff`, `list` 等命令

### 📦 安裝

```bash
pip install syncmcp
```

### 📚 文檔

- [使用者指南](https://github.com/yourusername/SyncMCP/blob/main/docs/USER-GUIDE.md)
- [開發者指南](https://github.com/yourusername/SyncMCP/blob/main/docs/DEVELOPER-GUIDE.md)
- [MCP 整合](https://github.com/yourusername/SyncMCP/blob/main/MCP_INTEGRATION.md)

### 🐛 Bug 修復

請在 [Issues](https://github.com/yourusername/SyncMCP/issues) 回報問題。

### 🙏 致謝

感謝所有貢獻者！
```

### 3. 附加建構產物

上傳 `dist/` 中的檔案：
- `syncmcp-2.0.0-py3-none-any.whl`
- `syncmcp-2.0.0.tar.gz`

## 📝 發布後檢查清單

- [ ] PyPI 頁面顯示正確
- [ ] `pip install syncmcp` 可正常安裝
- [ ] GitHub Release 已建立
- [ ] 更新 README.md badges（版本、PyPI 下載量等）
- [ ] 宣傳到相關社群（可選）

## 🔄 版本號規則

SyncMCP 遵循 [Semantic Versioning](https://semver.org/)：

- **MAJOR** (X.0.0)：不相容的 API 變更
- **MINOR** (0.X.0)：新增功能，向後相容
- **PATCH** (0.0.X)：Bug 修復，向後相容

範例：
- `2.0.0` → `2.0.1`：Bug 修復
- `2.0.1` → `2.1.0`：新增功能
- `2.1.0` → `3.0.0`：重大變更

## 🚨 常見問題

### Q: twine upload 失敗

**A**: 檢查：
1. API token 是否正確
2. 版本號是否已存在於 PyPI
3. 網路連接是否正常

### Q: 套件安裝失敗

**A**: 檢查：
1. Python 版本 >= 3.10
2. 依賴項目是否可用
3. 使用 `pip install --upgrade pip`

### Q: 如何撤回發布

**A**: PyPI 不支援刪除已發布的版本（僅可 yank），建議：
1. 發布修正版本（例如 2.0.1）
2. 在 GitHub Release 中標註問題

## 📞 聯繫方式

- GitHub Issues: https://github.com/yourusername/SyncMCP/issues
- Email: your.email@example.com

---

**上次發布**: 未發布
**目標日期**: TBD
**狀態**: ✅ 準備就緒
