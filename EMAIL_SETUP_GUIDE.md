# Email Setup Guide for OTP System

## Current Status
✅ SMTP configuration exists in `.env`  
⚠️ Email sending may not be working  
✅ DEBUG mode allows testing without email  

## Quick Test (No Email Needed)

When registering, the OTP is displayed in these locations:

### 1. Browser Console (Recommended)
1. Open browser Developer Tools (Press **F12**)
2. Go to **Console** tab
3. Look for: `DEBUG: OTP for your@email.com: 123456`
4. Copy the 6-digit code
5. Enter it in the OTP verification page

### 2. Server Logs
Check your terminal/PowerShell where the Flask app is running:
```
OTP generated (email not configured - check console)
DEBUG: OTP for user@nitc.ac.in: 123456
```

### 3. Network Tab
1. Press F12 → **Network** tab
2. Find the `/register` request
3. Click on it → **Preview** or **Response**
4. Look for OTP in the response

---

## Setting Up Gmail for Email Sending

### Step 1: Generate Gmail App Password

1. **Go to Google Account Security**
   - Visit: https://myaccount.google.com/security
   - Or: Google Account → Security

2. **Enable 2-Step Verification** (if not already enabled)
   - Click "2-Step Verification"
   - Follow prompts to enable
   - Required for app passwords

3. **Generate App Password**
   - Visit: https://myaccount.google.com/apppasswords
   - Or: Security → 2-Step Verification → App passwords (at bottom)
   - Select app: **Mail**
   - Select device: **Other (Custom name)**
   - Enter name: `NITC Exam Cell`
   - Click **Generate**
   - Copy the 16-character password (format: `xxxx xxxx xxxx xxxx`)

### Step 2: Update .env File

Open `.env` and update the SMTP section:

```dotenv
# SMTP Configuration for OTP emails
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=your-actual-gmail@gmail.com
SMTP_PASSWORD=your-16-char-app-password-here
SMTP_FROM=your-actual-gmail@gmail.com

# Debug Mode (shows OTP in console if email fails)
DEBUG_OTP=true
```

**Important**: 
- Remove spaces from app password: `xxxx xxxx xxxx xxxx` → `xxxxxxxxxxxxxxxx`
- Use the SAME email for both `SMTP_USER` and `SMTP_FROM`

### Step 3: Test Email Sending

Restart your Flask app and try registering again. You should receive actual emails!

---

## Alternative Email Providers

### Using Outlook/Hotmail

```dotenv
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USER=your-email@outlook.com
SMTP_PASSWORD=your-password
SMTP_FROM=your-email@outlook.com
```

### Using Yahoo Mail

```dotenv
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=465
SMTP_USER=your-email@yahoo.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=your-email@yahoo.com
```

### Using Custom SMTP Server

```dotenv
SMTP_SERVER=mail.yourdomain.com
SMTP_PORT=587
SMTP_USER=examcell@yourdomain.com
SMTP_PASSWORD=your-password
SMTP_FROM=examcell@yourdomain.com
```

---

## Testing SMTP Configuration

Create a test script to verify SMTP works:

```python
# test_smtp.py
import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

def test_smtp():
    smtp_server = os.environ.get('SMTP_SERVER')
    smtp_port = int(os.environ.get('SMTP_PORT', 465))
    smtp_user = os.environ.get('SMTP_USER')
    smtp_password = os.environ.get('SMTP_PASSWORD')
    
    print(f"Testing SMTP connection to {smtp_server}:{smtp_port}")
    print(f"Using account: {smtp_user}")
    
    try:
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=10)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
            server.starttls()
        
        server.login(smtp_user, smtp_password)
        print("✅ SMTP login successful!")
        
        # Send test email
        msg = MIMEText("This is a test email from NITC Exam Cell system.")
        msg['Subject'] = "Test Email - NITC Exam Cell"
        msg['From'] = smtp_user
        msg['To'] = smtp_user  # Send to yourself
        
        server.send_message(msg)
        print(f"✅ Test email sent to {smtp_user}")
        
        server.quit()
        print("✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_smtp()
```

Run it:
```bash
python test_smtp.py
```

---

## For Vercel Deployment

Add these environment variables in Vercel Dashboard:

1. Go to: https://vercel.com/dashboard
2. Select your project
3. Go to **Settings** → **Environment Variables**
4. Add each variable:
   - `SMTP_SERVER` = `smtp.gmail.com`
   - `SMTP_PORT` = `465`
   - `SMTP_USER` = `your-email@gmail.com`
   - `SMTP_PASSWORD` = `your-app-password`
   - `SMTP_FROM` = `your-email@gmail.com`
   - `DEBUG_OTP` = `false` (in production)

5. Click **Save**
6. **Redeploy** your application

---

## Troubleshooting

### "Authentication failed"
- ✅ Enable 2-Step Verification on Google Account
- ✅ Generate new App Password
- ✅ Use App Password, not regular Gmail password
- ✅ Remove spaces from app password

### "Connection timeout"
- ✅ Check firewall/antivirus blocking port 465
- ✅ Try port 587 with STARTTLS
- ✅ Check if Gmail access from "less secure apps" is needed

### "Name or service not known"
- ✅ Check internet connection
- ✅ Verify SMTP_SERVER spelling
- ✅ Try pinging smtp.gmail.com

### Emails going to spam
- ✅ Add proper email headers (already done)
- ✅ Use institutional domain email if possible
- ✅ Add SPF/DKIM records (advanced)

### OTP not received but no errors
- ✅ Check spam/junk folder
- ✅ Verify email address correct
- ✅ Check recipient's email settings
- ✅ Try with different email address

---

## Security Best Practices

1. **Never commit .env to Git** (already in .gitignore ✅)
2. **Use App Passwords** not regular passwords
3. **Rotate passwords** every 3-6 months
4. **Limit access** to SMTP credentials
5. **Monitor usage** for suspicious activity
6. **Use DEBUG_OTP=false** in production

---

## For Testing/Development

Keep `DEBUG_OTP=true` in your local `.env`:
- OTP will be shown in console
- Registration works even without email
- Faster testing during development

Set `DEBUG_OTP=false` in Vercel (production):
- OTP only sent via email
- More secure for real users
- Professional user experience

---

## Quick Reference

### Current Setup (Based on your .env)
```
Email: nitc.examcell@gmail.com
Server: smtp.gmail.com:465
Status: App password may need refresh
```

### To Test Right Now:
1. Register with any @nitc.ac.in email
2. Press F12 → Console
3. Copy OTP from console
4. Complete registration

### To Fix Email:
1. Get new Gmail App Password
2. Update SMTP_PASSWORD in .env
3. Restart Flask app
4. Test registration again

---

**Need Help?**
- Check server logs for detailed error messages
- Use test_smtp.py to diagnose connection issues
- Verify Gmail account security settings
