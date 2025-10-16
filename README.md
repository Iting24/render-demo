# 簡易 Flask 部落格 範例

這是一個使用 Flask 與 Flask-SQLAlchemy 的最小部落格範例。每篇文章包含三個欄位：標題 (title)、作者 (author)、內容 (content)。

快速開始（Windows PowerShell）：

```powershell
# 建議建立虛擬環境
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 安裝依賴
pip install -r requirements.txt

# (選用) 設定 secret key
$env:FLASK_SECRET = 'your-secret'

# 啟動應用（開發模式）
python app.py

# 預設會在 http://127.0.0.1:5000/ 查看
```

注意：此範例為學習用途；生產環境請使用適當的 WSGI 伺服器並設定更嚴謹的密鑰/資料庫設定與安全性。
