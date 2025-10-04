# 🚀 Bindora Backend Deployment Guide

Complete guide for deploying the Bindora API to production environments.

## 📋 Deployment Options

### 1. Railway.app (Recommended - Easiest)

Railway provides PostgreSQL, Redis, and easy scaling out of the box.

#### Quick Deploy

1. **Connect Repository**
   ```bash
   # Fork or connect your GitHub repo to Railway
   ```

2. **Add PostgreSQL Service**
   - Go to Railway dashboard
   - Click "New" → "Database" → "PostgreSQL"
   - Name it `bindora-db`

3. **Add Redis Service**
   - Click "New" → "Database" → "Redis"
   - Name it `bindora-redis`

4. **Deploy Backend**
   - Click "New" → "GitHub" → Select your repo
   - Set build command: `pip install -r requirements.txt`
   - Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 4`

5. **Configure Environment Variables**
   ```bash
   DATABASE_URL=${{ PostgreSQL.DATABASE_URL }}
   REDIS_URL=${{ Redis.REDIS_URL }}
   API_HOST=0.0.0.0
   API_PORT=${{ PORT }}
   ALLOWED_ORIGINS=https://your-frontend-domain.com
   ```

6. **Deploy Frontend** (if using Railway)
   - Deploy your Next.js frontend to Railway
   - Update `NEXT_PUBLIC_API_URL` to point to backend

### 2. Render.com (Alternative)

Render provides free tier and PostgreSQL support.

#### Deploy Steps

1. **Create PostgreSQL Database**
   - New → PostgreSQL
   - Name: `bindora-db`
   - Copy connection string

2. **Create Redis Instance** (Optional)
   - New → Redis
   - Or use Railway's Redis

3. **Deploy Backend**
   - New → Web Service
   - Connect GitHub repo
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

4. **Environment Variables**
   ```bash
   DATABASE_URL=<your-postgresql-connection-string>
   REDIS_URL=<your-redis-url>
   ```

### 3. Docker Compose (Self-Hosted)

For complete control over your infrastructure.

#### Production Setup

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://bindora:password@db:5432/bindora
      - REDIS_URL=redis://redis:6379
      - API_HOST=0.0.0.0
      - ALLOWED_ORIGINS=https://yourdomain.com
    depends_on:
      - db
      - redis
    deploy:
      replicas: 3
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: ankane/pgvector:latest
    environment:
      - POSTGRES_DB=bindora
      - POSTGRES_USER=bindora
      - POSTGRES_PASSWORD=your-secure-password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

#### Deploy with Docker

```bash
# Build and deploy
docker-compose up -d

# Scale API instances
docker-compose up -d --scale api=3

# Monitor logs
docker-compose logs -f api
```

## 🔧 Production Configuration

### Security Checklist

- [ ] **Environment Variables**: Never commit `.env` files
- [ ] **Database Password**: Use strong, unique password
- [ ] **CORS Origins**: Restrict to your frontend domains only
- [ ] **Rate Limiting**: Implement per endpoint
- [ ] **HTTPS**: Enable SSL/TLS in production
- [ ] **Monitoring**: Set up error tracking (Sentry, etc.)

### Environment Variables Template

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Database (PostgreSQL)
DATABASE_URL=postgresql://bindora:your-secure-password@your-db-host:5432/bindora

# Caching (Redis)
REDIS_URL=redis://your-redis-host:6379

# AI Models
PROTEIN_MODEL=facebook/esm2_t33_650M_UR50D
DEVICE=cuda  # or cpu for CPU-only deployment

# External APIs (keep defaults unless rate limited)
CHEMBL_API_URL=https://www.ebi.ac.uk/chembl/api/data
UNIPROT_API_URL=https://rest.uniprot.org

# Performance
MAX_RESULTS=100
BATCH_SIZE=32
CACHE_TTL=3600

# Logging
LOG_LEVEL=INFO  # Set to DEBUG for troubleshooting
```

### SSL/TLS Configuration

#### Railway/Railway
Railway provides automatic HTTPS. Just use `https://` URLs.

#### Custom Domain with Nginx

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 📊 Monitoring & Observability

### Health Checks

```bash
# Application health
curl https://your-api.com/health

# Database connectivity
curl https://your-api.com/api/stats
```

### Logging

#### Railway Logs
```bash
# View logs in Railway dashboard
# Or use Railway CLI
railway logs
```

#### Docker Logs
```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f api

# View last 100 lines
docker-compose logs --tail=100 api
```

### Performance Monitoring

#### Key Metrics to Monitor

1. **Response Times**: < 2 seconds for search endpoints
2. **Error Rates**: < 1% for production
3. **Cache Hit Rates**: > 80% for protein embeddings
4. **Database Connections**: Monitor pool usage
5. **Memory Usage**: Watch for memory leaks

#### Monitoring Tools

- **Railway Metrics**: Built-in monitoring dashboard
- **New Relic**: APM and error tracking
- **DataDog**: Comprehensive monitoring
- **Grafana + Prometheus**: Custom dashboards

## 🔄 Maintenance & Updates

### Regular Tasks

#### Weekly
- [ ] Review error logs
- [ ] Check database performance
- [ ] Update dependencies (security patches)
- [ ] Monitor resource usage

#### Monthly
- [ ] Run data update scripts
- [ ] Review and optimize slow queries
- [ ] Update AI models if newer versions available
- [ ] Backup database

#### Quarterly
- [ ] Performance audit
- [ ] Security review
- [ ] Cost optimization
- [ ] Update deployment configurations

### Updating Dependencies

```bash
# Check for outdated packages
pip list --outdated

# Update specific package
pip install --upgrade package-name

# Update all packages (careful in production)
pip install -r requirements.txt --upgrade
```

### Database Maintenance

```sql
-- Analyze tables for query optimization
ANALYZE drugs;
ANALYZE proteins;
ANALYZE predictions;

-- Check table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public';

-- Vacuum and reindex (run during low traffic)
VACUUM ANALYZE;
REINDEX DATABASE bindora;
```

## 🚨 Troubleshooting

### Common Issues

#### High Memory Usage
```bash
# Check memory usage
docker stats

# If using too much memory:
# 1. Reduce batch sizes in config
# 2. Clear model caches
# 3. Scale down API instances
```

#### Slow Response Times
```bash
# Check database performance
EXPLAIN ANALYZE SELECT * FROM predictions WHERE protein_id = 1;

# Check cache hit rates
curl https://your-api.com/api/stats
```

#### Model Loading Errors
```bash
# Clear model cache
curl -X POST https://your-api.com/api/admin/cache/clear

# Restart API instance
railway service restart bindora-api
```

### Emergency Procedures

#### Database Recovery
```bash
# Create backup
pg_dump bindora > bindora_backup.sql

# Restore from backup
psql bindora < bindora_backup.sql
```

#### Service Rollback
```bash
# Railway rollback
railway rollback

# Docker rollback
docker-compose down
git pull
docker-compose up -d
```

## 📈 Scaling

### Horizontal Scaling

#### Railway Auto-scaling
- Railway automatically scales based on CPU/memory usage
- Set min/max instances in dashboard

#### Manual Scaling
```bash
# Docker Compose scaling
docker-compose up -d --scale api=5

# Railway scaling
railway service scale api=5
```

### Database Scaling

#### Read Replicas
```sql
-- Create read replica (PostgreSQL)
CREATE PUBLICATION bindora_pub FOR ALL TABLES;
-- Configure replica server
```

#### Connection Pooling
- Use PgBouncer for connection pooling
- Configure in docker-compose.yml

### CDN for Static Assets

If serving static files:
```nginx
location /static/ {
    proxy_pass https://your-cdn.com;
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## 💰 Cost Optimization

### Railway Pricing (as of 2024)

- **PostgreSQL**: $5/month (512MB RAM)
- **Redis**: $5/month (256MB RAM)
- **API Service**: $5/month per GB RAM
- **Bandwidth**: Free up to 100GB/month

### Cost Saving Tips

1. **Right-size instances**: Monitor usage and downsize if possible
2. **Auto-scaling**: Set appropriate min/max instances
3. **Database optimization**: Archive old data
4. **Caching**: Maximize cache hit rates
5. **CDN**: Use for static assets

### Free Tier Limitations

- **Railway**: 512MB RAM, 1GB storage per service
- **Render**: 512MB RAM, limited build time
- **Vercel**: 100GB bandwidth, 1000 serverless functions

## 🔒 Security

### Production Security Checklist

- [ ] **HTTPS Only**: Redirect HTTP to HTTPS
- [ ] **Strong Passwords**: Use password manager
- [ ] **Environment Isolation**: Separate prod/dev environments
- [ ] **API Keys**: Rotate regularly
- [ ] **Monitoring**: Alert on suspicious activity
- [ ] **Backups**: Regular encrypted backups
- [ ] **Access Control**: Principle of least privilege

### Security Headers

Add to your reverse proxy:

```nginx
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
```

## 📞 Support & Resources

### Getting Help

1. **Documentation**: Check this deployment guide
2. **Logs**: Review application and database logs
3. **Monitoring**: Check Railway/Render dashboards
4. **Community**: GitHub issues for bugs
5. **Professional Support**: Consider Railway/Render support

### Useful Commands

```bash
# Railway
railway logs --tail  # Follow logs
railway status       # Service status
railway open         # Open in browser

# Docker
docker ps           # Show running containers
docker logs -f api  # Follow API logs
docker stats        # Resource usage

# Database
psql $DATABASE_URL -c "SELECT COUNT(*) FROM drugs;"  # Quick query
```

### Resources

- **Railway Docs**: https://docs.railway.app/
- **Render Docs**: https://render.com/docs
- **PostgreSQL Docs**: https://www.postgresql.org/docs/
- **Redis Docs**: https://redis.io/documentation
- **FastAPI Deployment**: https://fastapi.tiangolo.com/deployment/

---

## ✅ Deployment Checklist

- [ ] **Environment Variables**: All configured correctly
- [ ] **Database**: PostgreSQL with pgvector running
- [ ] **Redis**: Cache service available
- [ ] **API Tests**: All endpoints working
- [ ] **Frontend Connected**: Can communicate with backend
- [ ] **HTTPS**: SSL certificate installed
- [ ] **Monitoring**: Health checks configured
- [ ] **Backups**: Database backup strategy in place
- [ ] **Security**: Production security measures implemented
- [ ] **Documentation**: Team has access to deployment docs

**🎉 Ready for Production!**

