# 🚀 **VPS Deployment Guide - English Teacher Academy**

## 📋 **Complete Production Deployment Tutorial**

This guide will help you deploy your English Teacher Academy application on a VPS with best practices for security, performance, and maintainability.

---

## 🛠️ **Prerequisites**

### 📦 **What You Need**
- ✅ VPS Server (Ubuntu 20.04+ recommended)
- ✅ Domain name (optional but recommended)
- ✅ Basic Linux command line knowledge
- ✅ SSH access to your VPS

### 💰 **Recommended VPS Specifications**
- **CPU**: 2+ cores
- **RAM**: 4GB+ 
- **Storage**: 50GB+ SSD
- **Bandwidth**: Unlimited or 1TB+

### 🌐 **Recommended VPS Providers**
- **Iranian**: ParsVDS, Asanveb, FandoghCloud
- **International**: DigitalOcean, Linode, Vultr

---

## 🔧 **Step 1: Initial Server Setup**

### 🔐 **1.1 Connect to Your VPS**
```bash
ssh root@YOUR_SERVER_IP
```

### 👤 **1.2 Create a Non-Root User**
```bash
# Create user
adduser academy
usermod -aG sudo academy

# Switch to new user
su - academy
```

### 🔒 **1.3 Configure SSH Key Authentication (Optional but Recommended)**
```bash
# On your local machine, generate SSH key
ssh-keygen -t rsa -b 4096 -C "your-email@example.com"

# Copy public key to server
ssh-copy-id academy@YOUR_SERVER_IP
```

### 🛡️ **1.4 Basic Security Setup**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y curl wget git ufw fail2ban

# Configure firewall
sudo ufw allow OpenSSH
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

---

## 🐳 **Step 2: Install Docker and Docker Compose**

### 📦 **2.1 Install Docker**
```bash
# Remove old versions
sudo apt remove docker docker-engine docker.io containerd runc

# Install dependencies
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Add Docker GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### 🔧 **2.2 Install Docker Compose**
```bash
# Download Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Make executable
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

---

## 📁 **Step 3: Project Setup**

### 📥 **3.1 Clone Your Project**
```bash
# Create project directory
mkdir -p /home/academy/projects
cd /home/academy/projects

# Clone your repository (replace with your repo URL)
git clone https://github.com/YOUR_USERNAME/EnglishTeacherMobina.git
cd EnglishTeacherMobina

# Set proper permissions
sudo chown -R academy:academy /home/academy/projects
```

### 📝 **3.2 Create Production Environment File**
```bash
# Navigate to project directory
cd /home/academy/projects/EnglishTeacherMobina

# Create production .env file
cp .env.example .env
nano .env
```

**Edit `.env` with your production values:**
```env
# Django Settings - Production
DEBUG=False
SECRET_KEY=your-super-secure-secret-key-here-64-characters-long
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,YOUR_SERVER_IP

# Database Configuration
DB_NAME=englishteacher_production
DB_USER=englishteacher_user
DB_PASSWORD=your-very-secure-database-password
DB_HOST=db
DB_PORT=5432

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-academy-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password
ADMIN_EMAIL=admin@youracademy.com

# Redis Configuration
REDIS_URL=redis://redis:6379/1

# Media and Static Files
MEDIA_URL=/media/
STATIC_URL=/static/
MEDIA_ROOT=/var/www/englishteacher/media
STATIC_ROOT=/var/www/englishteacher/static

# Security Settings
SECURE_SSL_REDIRECT=True
SECURE_BROWSER_XSS_FILTER=True
SECURE_CONTENT_TYPE_NOSNIFF=True
X_FRAME_OPTIONS=DENY
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# Academy Details
ACADEMY_NAME=Your Academy Name
ACADEMY_PHONE=021-12345678
ACADEMY_EMAIL=info@youracademy.com
ACADEMY_ADDRESS=Your Academy Address
```

### 🔐 **3.3 Generate Secure Secret Key**
```bash
# Generate a secure secret key
python3 -c "
import secrets
import string
alphabet = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
secret_key = ''.join(secrets.choice(alphabet) for i in range(64))
print(f'SECRET_KEY={secret_key}')
"
```

---

## 🐘 **Step 4: Database Setup**

### 📊 **4.1 Create Database Directories**
```bash
# Create directories for persistent data
sudo mkdir -p /var/lib/postgresql/data
sudo mkdir -p /var/lib/redis/data
sudo mkdir -p /var/www/englishteacher/{static,media,logs}

# Set permissions
sudo chown -R 999:999 /var/lib/postgresql/data
sudo chown -R 999:999 /var/lib/redis/data
sudo chown -R $USER:$USER /var/www/englishteacher
```

---

## 🚀 **Step 5: Deploy with Docker Compose**

### 🏗️ **5.1 Build and Start Services**
```bash
# Navigate to project root
cd /home/academy/projects/EnglishTeacherMobina

# Build and start services
docker-compose up -d --build

# Check if services are running
docker-compose ps
```

### 📋 **5.2 Initial Setup Commands**
```bash
# Wait for database to be ready (about 30 seconds)
sleep 30

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Check logs
docker-compose logs web
```

---

## 🌐 **Step 6: Nginx and SSL Setup**

### 📝 **6.1 Install Nginx (if not using Docker Nginx)**
```bash
# Install Nginx
sudo apt install -y nginx

# Create site configuration
sudo nano /etc/nginx/sites-available/englishteacher
```

**Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com YOUR_SERVER_IP;

    client_max_body_size 100M;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias /var/www/englishteacher/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/englishteacher/media/;
        expires 1y;
        add_header Cache-Control "public";
    }

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 🔗 **6.2 Enable Site**
```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/englishteacher /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### 🔒 **6.3 SSL Certificate with Certbot**
```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

---

## 🔄 **Step 7: Process Management and Monitoring**

### 📊 **7.1 Set Up Log Monitoring**
```bash
# Create log rotation
sudo nano /etc/logrotate.d/englishteacher
```

**Logrotate Configuration:**
```
/var/www/englishteacher/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    sharedscripts
    copytruncate
}
```

### 🔄 **7.2 Auto-restart Services**
```bash
# Create systemd service for auto-restart
sudo nano /etc/systemd/system/englishteacher.service
```

**Systemd Service:**
```ini
[Unit]
Description=English Teacher Academy
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/academy/projects/EnglishTeacherMobina
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

```bash
# Enable service
sudo systemctl enable englishteacher.service
sudo systemctl start englishteacher.service
```

---

## 🔧 **Step 8: Backup Strategy**

### 📦 **8.1 Database Backup Script**
```bash
# Create backup directory
mkdir -p /home/academy/backups

# Create backup script
nano /home/academy/scripts/backup.sh
```

**Backup Script:**
```bash
#!/bin/bash
BACKUP_DIR="/home/academy/backups"
DATE=$(date +"%Y%m%d_%H%M%S")

# Database backup
docker-compose exec -T db pg_dump -U englishteacher_user englishteacher_production > "$BACKUP_DIR/db_backup_$DATE.sql"

# Media files backup
tar -czf "$BACKUP_DIR/media_backup_$DATE.tar.gz" /var/www/englishteacher/media/

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

```bash
# Make executable
chmod +x /home/academy/scripts/backup.sh

# Add to crontab for daily backups
crontab -e
# Add line: 0 2 * * * /home/academy/scripts/backup.sh
```

---

## 🔄 **Step 9: Deployment and Updates**

### 🚀 **9.1 Deployment Script**
```bash
# Create deployment script
nano /home/academy/scripts/deploy.sh
```

**Deployment Script:**
```bash
#!/bin/bash
set -e

echo "🚀 Starting deployment..."

# Navigate to project directory
cd /home/academy/projects/EnglishTeacherMobina

# Pull latest changes
git pull origin main

# Backup database before update
/home/academy/scripts/backup.sh

# Stop services
docker-compose down

# Rebuild and start
docker-compose up -d --build

# Wait for services
sleep 30

# Run migrations
docker-compose exec web python manage.py migrate

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Check health
curl -f http://localhost:8000/ || echo "❌ Health check failed"

echo "✅ Deployment completed successfully!"
```

```bash
# Make executable
chmod +x /home/academy/scripts/deploy.sh
```

---

## 📊 **Step 10: Monitoring and Maintenance**

### 🔍 **10.1 Basic Monitoring Commands**
```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f web
docker-compose logs -f db
docker-compose logs -f nginx

# Check resource usage
docker stats

# Check disk space
df -h

# Check memory usage
free -h
```

### 🔧 **10.2 Useful Maintenance Commands**
```bash
# Update application
/home/academy/scripts/deploy.sh

# Restart services
docker-compose restart

# View database shell
docker-compose exec db psql -U englishteacher_user -d englishteacher_production

# Django shell
docker-compose exec web python manage.py shell

# Create Django superuser
docker-compose exec web python manage.py createsuperuser
```

---

## 🚨 **Step 11: Troubleshooting**

### ❌ **Common Issues and Solutions**

#### **Issue 1: Services won't start**
```bash
# Check Docker status
sudo systemctl status docker

# Check compose logs
docker-compose logs

# Restart Docker
sudo systemctl restart docker
```

#### **Issue 2: Database connection failed**
```bash
# Check database logs
docker-compose logs db

# Verify environment variables
docker-compose exec web env | grep DB_

# Test database connection
docker-compose exec db psql -U englishteacher_user -d englishteacher_production -c "SELECT 1;"
```

#### **Issue 3: Static files not loading**
```bash
# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Check Nginx configuration
sudo nginx -t

# Check file permissions
ls -la /var/www/englishteacher/static/
```

#### **Issue 4: High memory usage**
```bash
# Check Docker stats
docker stats

# Clean unused Docker resources
docker system prune -f

# Restart services with lower memory
docker-compose restart
```

---

## 🔐 **Step 12: Security Checklist**

### ✅ **Security Best Practices**

- [ ] **Firewall configured** (only ports 22, 80, 443 open)
- [ ] **SSH key authentication** enabled
- [ ] **Root login disabled**
- [ ] **Strong passwords** for all accounts
- [ ] **SSL certificate** installed and auto-renewing
- [ ] **Regular backups** scheduled
- [ ] **Keep system updated** (`sudo apt update && sudo apt upgrade`)
- [ ] **Monitor logs** regularly
- [ ] **Use environment variables** for sensitive data
- [ ] **Database accessible only from localhost**

### 🛡️ **Additional Security Measures**
```bash
# Install fail2ban for brute force protection
sudo apt install fail2ban

# Configure automatic updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure unattended-upgrades

# Set up log monitoring
sudo apt install logwatch
```

---

## 📈 **Step 13: Performance Optimization**

### ⚡ **Performance Tips**

#### **13.1 Optimize Nginx**
```nginx
# Add to /etc/nginx/nginx.conf
gzip on;
gzip_comp_level 6;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

# Enable caching
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

#### **13.2 Database Optimization**
```bash
# Optimize PostgreSQL
docker-compose exec db psql -U englishteacher_user -d englishteacher_production -c "VACUUM ANALYZE;"
```

#### **13.3 Monitor Performance**
```bash
# Install htop for system monitoring
sudo apt install htop

# Monitor in real-time
htop
```

---

## 🎉 **Step 14: Final Verification**

### ✅ **Deployment Checklist**

1. **Services Running**
   ```bash
   docker-compose ps
   # All services should show "Up"
   ```

2. **Website Accessible**
   - Open browser and visit your domain
   - Check HTTP redirects to HTTPS
   - Verify all pages load correctly

3. **Admin Panel Working**
   - Visit `/admin/`
   - Login with superuser account
   - Test adding content

4. **Database Connectivity**
   ```bash
   docker-compose exec web python manage.py dbshell
   ```

5. **Static Files Loading**
   - Check CSS and images load properly
   - Verify Font Awesome icons display

6. **Email Configuration**
   - Test contact form submission
   - Verify admin receives notifications

7. **SSL Certificate**
   ```bash
   # Check SSL grade
   curl -I https://yourdomain.com
   ```

8. **Backups Working**
   ```bash
   /home/academy/scripts/backup.sh
   ls -la /home/academy/backups/
   ```

---

## 📞 **Support and Maintenance**

### 🆘 **When You Need Help**

- **Server Issues**: Contact your VPS provider
- **Application Issues**: Check Docker logs
- **Domain Issues**: Contact your domain registrar
- **SSL Issues**: Re-run Certbot

### 📅 **Regular Maintenance Schedule**

- **Daily**: Check logs and backups
- **Weekly**: Update system packages
- **Monthly**: Review security and performance
- **Quarterly**: Test backup restoration

---

## 🎯 **Success! Your Academy is Live!**

🎊 **Congratulations!** Your English Teacher Academy is now running on a production VPS with:

- ✅ **Professional Docker setup**
- ✅ **SSL encryption**
- ✅ **Automated backups**
- ✅ **Performance optimization**
- ✅ **Security best practices**
- ✅ **Easy deployment process**

Your academy is ready to accept students and provide excellent English language education online! 🌟

---

**💡 Pro Tip**: Keep this guide handy for future updates and maintenance. Share it with your technical team for consistent deployments. 