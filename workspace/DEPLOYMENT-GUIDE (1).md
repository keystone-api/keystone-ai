# Web IDE 部署指南

## 🎉 部署完成

您的 Web IDE 已經成功部署並運行！

## 🌐 訪問地址

**主要訪問 URL**:

```
https://3000-e440c233-6b30-4b6d-92b2-f1f8879fb5f0.sandbox-service.public.prod.myninja.ai
```

## ✨ 功能演示

### 1\. 代碼編輯器

-   打開任何文件進行編輯
-   支持語法高亮
-   自動補全
-   代碼格式化

### 2\. 文件管理

-   左側文件列表
-   點擊文件打開
-   支持多個文件同時打開

### 3\. 終端

-   底部終端窗口
-   輸入命令測試
-   可用命令: `help`, `clear`, `echo`, `date`, `ls`

### 4\. 實時預覽

-   右側預覽窗口
-   自動更新 HTML/CSS/JS
-   點擊刷新按鈕手動更新

### 5\. 布局切換

-   工具欄右側三個按鈕
-   編輯器模式 (僅編輯器)
-   分屏模式 (編輯器 + 預覽)
-   預覽模式 (僅預覽)

## 🎯 快速測試

### 測試 1: 編輯 HTML

1.  點擊左側 `index.html`
2.  修改 `<h1>` 標籤內容
3.  查看右側預覽自動更新

### 測試 2: 編輯 CSS

1.  點擊左側 `style.css`
2.  修改顏色或字體
3.  查看預覽實時變化

### 測試 3: 編輯 JavaScript

1.  點擊左側 `script.js`
2.  添加 `console.log("測試")`
3.  打開瀏覽器控制台查看輸出

### 測試 4: 使用終端

1.  在底部終端輸入 `help`
2.  嘗試其他命令
3.  輸入 `clear` 清空終端

### 測試 5: 創建新文件

1.  點擊工具欄 "New File"
2.  新文件會出現在文件列表
3.  開始編輯新文件

## 📱 響應式設計

### 桌面端 (推薦)

-   完整功能
-   最佳體驗
-   分屏視圖

### 平板端

-   適配布局
-   觸摸優化
-   可用所有功能

### 移動端

-   基本功能
-   垂直布局
-   簡化界面

## 🔧 本地開發

如果您想在本地運行：

```bash
cd /workspace/web-ide

# 安裝依賴
npm install

# 開發模式
npm run dev

# 訪問 http://localhost:3000
```

## 📦 生產部署

### 構建生產版本

```bash
npm run build
```

生成的文件在 `dist/` 目錄

### 部署到 Cloudflare Pages

1.  登入 Cloudflare Dashboard
2.  進入 Pages
3.  創建新項目
4.  連接 Git 倉庫或上傳 `dist/` 目錄
5.  構建命令: `npm run build`
6.  輸出目錄: `dist`

### 部署到 Vercel

```bash
npm install -g vercel
vercel --prod
```

### 部署到 Netlify

```bash
npm install -g netlify-cli
netlify deploy --prod --dir=dist
```

## 🎨 自定義配置

### 修改主題顏色

編輯 `src/index.css`:

```css
:root {
  --bg-primary: #1e1e1e;      /* 主背景色 */
  --bg-secondary: #252526;    /* 次背景色 */
  --accent-color: #007acc;    /* 強調色 */
  /* 修改這些變量來改變主題 */
}
```

### 修改編輯器設置

編輯 `src/components/Editor.jsx`:

```javascript
options={{
  fontSize: 14,        // 字體大小
  tabSize: 2,          // Tab 大小
  wordWrap: 'on',      // 自動換行
  minimap: { enabled: true },  // 小地圖
}}
```

### 添加更多預設文件

編輯 `src/App.jsx` 中的 `files` 狀態:

```javascript
const [files, setFiles] = useState([
  { id: 1, name: 'index.html', type: 'file', content: '...' },
  { id: 2, name: 'style.css', type: 'file', content: '...' },
  // 添加更多文件
])
```

## 🐛 故障排除

### 問題 1: 預覽不更新

-   點擊預覽窗口的刷新按鈕
-   檢查 HTML 文件是否有語法錯誤

### 問題 2: 終端無法輸入

-   點擊終端區域確保焦點
-   刷新頁面重新初始化

### 問題 3: 編輯器卡頓

-   關閉不需要的標籤
-   減少打開的文件數量
-   禁用小地圖 (minimap)

### 問題 4: 樣式錯亂

-   清除瀏覽器緩存
-   硬刷新 (Ctrl+Shift+R)

## 📊 性能優化

### 優化建議

1.  使用生產構建 (`npm run build`)
2.  啟用 CDN 加速
3.  壓縮靜態資源
4.  使用 Service Worker 緩存

### 監控指標

-   首次加載時間: < 3秒
-   編輯器響應時間: < 100ms
-   預覽更新時間: < 500ms

## 🔒 安全考慮

### 沙箱環境

-   預覽使用 iframe 沙箱
-   限制腳本執行權限
-   隔離用戶代碼

### 建議措施

1.  不要在預覽中運行不信任的代碼
2.  定期更新依賴包
3.  使用 HTTPS 連接
4.  實施內容安全策略 (CSP)

## 📚 更多資源

### 文檔

-   [Monaco Editor 文檔](https://microsoft.github.io/monaco-editor/)
-   [xterm.js 文檔](https://xtermjs.org/)
-   [React 文檔](https://react.dev/)
-   [Vite 文檔](https://vitejs.dev/)

### 社區

-   GitHub Issues
-   Stack Overflow
-   Discord 社群

## 🎓 學習資源

### 教程

1.  Monaco Editor 基礎
2.  xterm.js 終端開發
3.  React Hooks 進階
4.  Vite 構建優化

### 示例項目

-   VS Code Web
-   CodeSandbox
-   StackBlitz
-   Replit

## 🚀 下一步

### 建議改進

1.  添加文件上傳/下載
2.  實現多文件夾支持
3.  集成 Git 功能
4.  添加協作編輯
5.  實現插件系統
6.  添加主題切換
7.  實現快捷鍵配置
8.  添加代碼片段
9.  實現搜索和替換
10.  添加調試功能

### 集成建議

1.  與 SuperNinja Mode System 集成
2.  連接後端 API
3.  實現用戶認證
4.  添加項目管理
5.  實現雲端保存

## 📞 支持

如有問題或建議：

1.  查看 README.md
2.  檢查故障排除部分
3.  提交 GitHub Issue
4.  聯繫開發團隊

* * *

**部署時間**: 2024 **版本**: 1.0.0 **狀態**: ✅ 生產就緒