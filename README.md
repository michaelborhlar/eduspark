# EduSpark — School Management Platform

A full-stack Django school portal with two separate routes:
- **`/student/`** — Beautiful student-facing portal
- **`/admin-panel/`** — Teacher/admin management dashboard

## Routes Summary
| URL | Purpose |
|-----|---------|
| `/student/` | Student registration, login, dashboard, exams, learning hub |
| `/admin-panel/` | Admin login, question bank, create tests/assignments/assessments, grade submissions |
| `/api/` | REST API consumed by both portals |
| `/django-admin/` | Django built-in superuser admin |

---

## Local Setup (Mac / Linux / Windows)

### 1. Clone & enter the project
```bash
git clone https://github.com/YOUR_USERNAME/eduspark.git
cd eduspark
```

### 2. Create virtual environment
```bash
python -m venv venv

# Mac/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run migrations
```bash
python manage.py migrate
```

### 5. Create a superuser (for admin panel)
```bash
python manage.py createsuperuser
```
When prompted:
- First name: e.g. `Admin`
- Surname: e.g. `User`
- Student class: `SSS1` (required by model, ignored for admins)
- Password: choose a strong password

### 6. Add subjects (via Django admin or shell)
```bash
python manage.py shell
```
```python
from core.models import Subject
for s in ['Mathematics','English','Biology','Chemistry','Physics','Government','Literature']:
    Subject.objects.get_or_create(name=s)
exit()
```

### 7. Collect static files
```bash
python manage.py collectstatic --noinput
```

### 8. Run the server
```bash
python manage.py runserver
```

### 9. Open in browser
| Portal | URL |
|--------|-----|
| Student Portal | http://localhost:8000/student/ |
| Admin Portal | http://localhost:8000/admin-panel/ |
| Django Admin | http://localhost:8000/django-admin/ |

---

## Deploying to Render (Free)

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/eduspark.git
git push -u origin main
```

### 2. Create a Render account
Go to https://render.com and sign up.

### 3. New Web Service
- Click **New → Web Service**
- Connect your GitHub repo
- Fill in:
  - **Name:** `eduspark`
  - **Runtime:** `Python 3`
  - **Build Command:** `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
  - **Start Command:** `gunicorn eduspark.wsgi`

### 4. Add Environment Variables in Render dashboard:
| Key | Value |
|-----|-------|
| `SECRET_KEY` | (generate a random 50-char string) |
| `DEBUG` | `False` |
| `PYTHON_VERSION` | `3.11.9` |

### 5. Deploy
Click **Create Web Service**. Render builds and deploys automatically.

### 6. Create superuser on Render
In Render dashboard → your service → **Shell** tab:
```bash
python manage.py createsuperuser
```

### 7. Add subjects on Render (Shell tab):
```bash
python manage.py shell -c "
from core.models import Subject
for s in ['Mathematics','English','Biology','Chemistry','Physics','Government','Literature']:
    Subject.objects.get_or_create(name=s)
print('Subjects created!')
"
```

Your app will be live at: `https://eduspark.onrender.com`

---

## Deploying to Railway

### 1. Install Railway CLI
```bash
npm install -g @railway/cli
railway login
```

### 2. Deploy
```bash
cd eduspark
railway init
railway up
```

### 3. Set environment variables
```bash
railway variables set SECRET_KEY="your-secret-key"
railway variables set DEBUG="False"
```

### 4. Run migrations
```bash
railway run python manage.py migrate
railway run python manage.py createsuperuser
```

---

## Deploying to a VPS (DigitalOcean / Hetzner / AWS EC2)

### 1. SSH into your server
```bash
ssh root@YOUR_SERVER_IP
```

### 2. Install Python & Nginx
```bash
apt update && apt install -y python3 python3-pip python3-venv nginx git
```

### 3. Clone repo
```bash
cd /var/www
git clone https://github.com/YOUR_USERNAME/eduspark.git
cd eduspark
```

### 4. Setup virtual env
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5. Environment variables
```bash
cp .env.example .env
nano .env   # fill in SECRET_KEY, DEBUG=False, ALLOWED_HOSTS=yourdomain.com
```

Update `settings.py` to read from `.env`:
```python
import os
SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback-key')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
```

### 6. Migrate & collect static
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

### 7. Create systemd service `/etc/systemd/system/eduspark.service`
```ini
[Unit]
Description=EduSpark Gunicorn
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/eduspark
ExecStart=/var/www/eduspark/venv/bin/gunicorn eduspark.wsgi:application --bind 127.0.0.1:8000 --workers 3
Restart=always
EnvironmentFile=/var/www/eduspark/.env

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl start eduspark
systemctl enable eduspark
```

### 8. Nginx config `/etc/nginx/sites-available/eduspark`
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location /static/ {
        alias /var/www/eduspark/staticfiles/;
    }

    location /media/ {
        alias /var/www/eduspark/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

```bash
ln -s /etc/nginx/sites-available/eduspark /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

### 9. Add SSL (free) with Certbot
```bash
apt install certbot python3-certbot-nginx -y
certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

---

## How to Use the Admin Panel

1. Go to `http://yoursite.com/admin-panel/`
2. Login with your superuser credentials
3. **First: Add Subjects** via the API shell command above
4. **Add Questions** to the Question Bank (with optional images)
5. **Create a Test** — pick subject, class, how many questions to draw, set time limit and dates
6. **Publish** — students can now see and take the test
7. **Review Submissions** — grade typed/image answers
8. **Grade Centre** — see all scores, export CSV

## How Students Use It

1. Go to `http://yoursite.com/student/`
2. Click **Get Started** → register with name, class (selected from dropdown), password
3. Their name is **automatically saved to their class roster**
4. Dashboard shows open tests, assignments, assessments
5. Take a test → every student gets **unique randomised questions**
6. For assessments with "Show Answers" enabled → see results + explanations immediately

---

## Project Structure
```
eduspark/
├── eduspark/
│   ├── settings.py       # Django settings
│   ├── urls.py           # Root URL config (student/ and admin-panel/ routes)
│   └── wsgi.py
├── core/
│   ├── models.py         # All database models
│   ├── views.py          # All API views
│   ├── serializers.py    # DRF serializers
│   ├── api_urls.py       # API URL patterns
│   └── admin.py          # Django admin registration
├── templates/
│   ├── student/
│   │   └── index.html    # Student Portal SPA
│   └── admin_panel/
│       └── index.html    # Admin Portal SPA
├── static/               # Static files
├── media/                # Uploaded files (questions images, videos, answers)
├── requirements.txt
├── Procfile              # For Render/Heroku
├── runtime.txt           # Python version
└── manage.py
```
