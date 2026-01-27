# Deployment - Triển khai ứng dụng lên Production

## Tổng quan

Hướng dẫn deploy dự án lên môi trường production (miễn phí) với:
- **Backend**: PythonAnywhere hoặc Render
- **Frontend**: Vercel
- **Database**: (Optional) PostgreSQL trên Supabase

---

## 🚀 Part 1: Deploy Backend (FastAPI)

### Option 1: PythonAnywhere (Recommended - Free Tier)

#### Ưu điểm:
- ✅ Free tier với 1 web app
- ✅ Hỗ trợ Python tốt
- ✅ Dễ setup
- ✅ Có MySQL database miễn phí

#### Bước triển khai:

**1. Tạo tài khoản**
- Truy cập [pythonanywhere.com](https://www.pythonanywhere.com/)
- Đăng ký tài khoản miễn phí

**2. Upload code**
```bash
# Trên local, tạo file requirements.txt
pip freeze > requirements.txt

# Hoặc dùng Git
git init
git add .
git commit -m "Initial commit"
git push origin main
```

**3. Clone repo trên PythonAnywhere**
```bash
# Mở Bash console trên PythonAnywhere
git clone https://github.com/your-username/your-repo.git
cd your-repo/backend
```

**4. Tạo virtual environment**
```bash
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**5. Configure Web App**
- Vào tab "Web"
- Click "Add a new web app"
- Chọn "Manual configuration"
- Chọn Python 3.10

**6. WSGI Configuration**
Sửa file WSGI config:
```python
import sys
path = '/home/yourusername/your-repo/backend'
if path not in sys.path:
    sys.path.append(path)

from main import app as application
```

**7. Static files & CORS**
Trong `main.py`, update CORS:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.vercel.app"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**8. Reload web app**
- Click "Reload" button
- Truy cập `https://yourusername.pythonanywhere.com`

#### Troubleshooting:
- **Error logs**: Tab "Error log" để xem lỗi
- **File paths**: Kiểm tra đường dẫn tuyệt đối
- **Dependencies**: Đảm bảo tất cả packages đã install

---

### Option 2: Render (Alternative - Free Tier)

#### Ưu điểm:
- ✅ Auto-deploy từ GitHub
- ✅ Free tier với 750 giờ/tháng
- ✅ Hỗ trợ Docker
- ⚠️ Sleep sau 15 phút không dùng (cần 30s để wake up)

#### Bước triển khai:

**1. Tạo `render.yaml`**
```yaml
services:
  - type: web
    name: sales-forecast-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.10.0
```

**2. Push to GitHub**
```bash
git add render.yaml
git commit -m "Add Render config"
git push
```

**3. Deploy trên Render**
- Truy cập [render.com](https://render.com/)
- Connect GitHub repo
- Chọn "New Web Service"
- Render sẽ tự động deploy

---

## 🌐 Part 2: Deploy Frontend (Next.js)

### Vercel (Recommended - Free Tier)

#### Ưu điểm:
- ✅ Được tạo bởi team Next.js
- ✅ Auto-deploy từ GitHub
- ✅ Free tier unlimited
- ✅ CDN toàn cầu
- ✅ Automatic HTTPS

#### Bước triển khai:

**1. Update API URL**
Tạo file `.env.local`:
```bash
NEXT_PUBLIC_API_URL=https://yourusername.pythonanywhere.com
```

Update `lib/api.ts`:
```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
```

**2. Push to GitHub**
```bash
git add .
git commit -m "Add environment variables"
git push
```

**3. Deploy trên Vercel**
- Truy cập [vercel.com](https://vercel.com/)
- Click "Import Project"
- Connect GitHub repo
- Chọn `frontend` folder
- Add environment variable: `NEXT_PUBLIC_API_URL`
- Click "Deploy"

**4. Custom Domain (Optional)**
- Mua domain trên Namecheap, GoDaddy
- Vào Vercel Settings > Domains
- Add custom domain
- Update DNS records

---

## 🗄️ Part 3: Database (Optional)

### Nếu cần database thay vì CSV:

#### Supabase (PostgreSQL - Free Tier)

**1. Tạo project**
- Truy cập [supabase.com](https://supabase.com/)
- Create new project

**2. Tạo table**
```sql
CREATE TABLE sales (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(50),
    order_date DATE,
    customer_id VARCHAR(50),
    customer_name VARCHAR(100),
    region VARCHAR(50),
    category VARCHAR(50),
    sales DECIMAL(10, 2),
    profit DECIMAL(10, 2),
    discount DECIMAL(5, 2)
);
```

**3. Import CSV data**
- Dùng Supabase Table Editor
- Hoặc Python script:
```python
from supabase import create_client
import pandas as pd

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
df = pd.read_csv('data.csv')

for _, row in df.iterrows():
    supabase.table('sales').insert(row.to_dict()).execute()
```

**4. Update backend**
```python
# requirements.txt
supabase

# main.py
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def load_data():
    response = supabase.table('sales').select('*').execute()
    return pd.DataFrame(response.data)
```

---

## 🔒 Part 4: Environment Variables & Security

### Backend (.env)
```bash
# .env (không commit lên Git!)
DATABASE_URL=postgresql://user:pass@host/db
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your-key
SECRET_KEY=your-secret-key
```

### Frontend (.env.local)
```bash
# .env.local (không commit lên Git!)
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

### .gitignore
```
# Environment
.env
.env.local
.env.production

# Python
__pycache__/
*.pyc
venv/

# Next.js
.next/
node_modules/
```

---

## 📊 Part 5: Monitoring & Analytics

### 1. Error Tracking - Sentry

```bash
# Backend
pip install sentry-sdk

# main.py
import sentry_sdk
sentry_sdk.init(dsn="your-dsn")
```

### 2. Analytics - Google Analytics

```typescript
// Frontend - app/layout.tsx
import Script from 'next/script'

export default function RootLayout({ children }) {
  return (
    <html>
      <head>
        <Script
          src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"
          strategy="afterInteractive"
        />
      </head>
      <body>{children}</body>
    </html>
  )
}
```

---

## 🚀 Part 6: CI/CD (Continuous Integration/Deployment)

### GitHub Actions

Tạo `.github/workflows/deploy.yml`:
```yaml
name: Deploy

on:
  push:
    branches: [ main ]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to PythonAnywhere
        run: |
          # SSH vào PythonAnywhere và pull code
          
  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Vercel
        run: npx vercel --prod --token=${{ secrets.VERCEL_TOKEN }}
```

---

## 📋 Checklist trước khi Deploy

- [ ] Test local thoroughly
- [ ] Update CORS origins
- [ ] Set environment variables
- [ ] Add .gitignore
- [ ] Remove sensitive data
- [ ] Test API endpoints
- [ ] Check mobile responsive
- [ ] Add error handling
- [ ] Setup monitoring
- [ ] Document API

---

## 💰 Cost Comparison

| Service | Free Tier | Paid |
|---------|-----------|------|
| **PythonAnywhere** | 1 web app, 512MB storage | $5/month |
| **Render** | 750 hours/month | $7/month |
| **Vercel** | Unlimited | $20/month (Pro) |
| **Supabase** | 500MB database | $25/month |

---

## 🔗 Useful Links

- [PythonAnywhere Help](https://help.pythonanywhere.com/)
- [Render Documentation](https://render.com/docs)
- [Vercel Documentation](https://vercel.com/docs)
- [Supabase Documentation](https://supabase.com/docs)

---

## 💡 Tips Deployment

1. **Test locally first**: Đảm bảo mọi thứ chạy tốt trước khi deploy
2. **Use environment variables**: Không hardcode URLs, keys
3. **Monitor errors**: Setup Sentry hoặc logging
4. **Backup data**: Thường xuyên backup database
5. **Update dependencies**: Giữ packages up-to-date
6. **Use HTTPS**: Luôn dùng HTTPS cho production
7. **Cache static files**: Tăng tốc độ load
8. **Optimize images**: Compress images trước khi upload
