# Deployment Guide

## Production Deployment

### Prerequisites
- Python 3.8+
- pip
- A production WSGI server (Gunicorn, uWSGI, or Waitress)
- Reverse proxy (Nginx or Apache)
- Database (PostgreSQL recommended for production)

### Environment Setup

1. **Create a virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set environment variables:**
```bash
export FLASK_CONFIG=production
export SECRET_KEY=your-super-secret-key-here
export DATABASE_URL=postgresql://user:password@localhost/exam_cell
```

### Production Configuration

1. **Update config.py for production:**
```python
class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DATABASE_URL = os.environ.get('DATABASE_URL')
```

2. **Use a production WSGI server:**
```bash
# Using Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 run:app

# Using Waitress (Windows-friendly)
pip install waitress
waitress-serve --host=0.0.0.0 --port=8000 run:app
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/your/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /uploads {
        alias /path/to/your/app/uploads;
        expires 1d;
    }
}
```

### Security Considerations

1. **Change default passwords:**
   - Update admin and staff passwords in production
   - Use strong, unique passwords

2. **Secure file uploads:**
   - Validate file types and sizes
   - Scan uploaded files for malware
   - Store uploads outside web root

3. **Database security:**
   - Use strong database passwords
   - Enable SSL connections
   - Regular backups

4. **HTTPS:**
   - Use SSL certificates
   - Redirect HTTP to HTTPS
   - Set secure cookie flags

### Monitoring

1. **Application logs:**
```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
```

2. **Error tracking:**
   - Consider using Sentry or similar service
   - Monitor application performance

### Backup Strategy

1. **Database backups:**
```bash
# Daily backup script
pg_dump exam_cell > backup_$(date +%Y%m%d).sql
```

2. **File backups:**
```bash
# Backup uploads and downloads
tar -czf files_backup_$(date +%Y%m%d).tar.gz uploads/ downloads/
```

### Docker Deployment

1. **Create Dockerfile:**
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "run:app"]
```

2. **Docker Compose:**
```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_CONFIG=production
      - SECRET_KEY=your-secret-key
    volumes:
      - ./uploads:/app/uploads
      - ./downloads:/app/downloads
      - ./logs:/app/logs
    depends_on:
      - db

  db:
    image: postgres:13
    environment:
      POSTGRES_DB: exam_cell
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Performance Optimization

1. **Database indexing:**
   - Add indexes on frequently queried columns
   - Optimize queries

2. **Caching:**
   - Use Redis for session storage
   - Cache frequently accessed data

3. **Static files:**
   - Use CDN for static assets
   - Enable gzip compression

### Troubleshooting

1. **Common issues:**
   - Check file permissions
   - Verify database connections
   - Monitor disk space
   - Check application logs

2. **Performance issues:**
   - Monitor database queries
   - Check memory usage
   - Optimize file operations
