# Backend — Variáveis de Ambiente para Deploy

## Render.com (Production)

Copie e configure estas variáveis no painel do Render:

```
# Django
DJANGO_SECRET_KEY=sua-chave-secreta-muito-longa-aqui-minimo-50-caracteres
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=seu-backend.onrender.com

# Database (PostgreSQL fornecido pelo Render)
DATABASE_URL=postgresql://user:password@host:5432/dbname

# CORS (Frontend)
CORS_ALLOWED_ORIGINS=https://seu-frontend.vercel.app

# Email (para notificações)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-ou-app-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=seu-email@gmail.com

# Opcional: Secret key adicional
SECRET_KEY_ADDITIONAL=additional-secret-for-encryption
```

### Como Gerar uma DJANGO_SECRET_KEY:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Gmail App Password:

1. Ative 2-Factor Authentication na sua conta Google
2. Vá para https://myaccount.google.com/apppasswords
3. Selecione "Mail" e "Windows Computer"
4. Copie a senha gerada (16 caracteres)
5. Use como `EMAIL_HOST_PASSWORD`

---

## Frontend — Variáveis de Ambiente para Deploy

## Vercel

Copie e configure estas variáveis no painel da Vercel (Settings → Environment Variables):

```
VITE_API_URL=https://seu-backend.onrender.com/api/v1
```

### Para Desenvolvimento Local (.env.local)

```
VITE_API_URL=http://localhost:8000/api/v1
```

---

## Resumo Rápido

| Variável | Backend | Frontend | Valor |
|----------|---------|----------|-------|
| `DJANGO_SECRET_KEY` | ✅ | ❌ | Use `python -c "..."` |
| `DJANGO_DEBUG` | ✅ | ❌ | `False` (prod) |
| `DATABASE_URL` | ✅ | ❌ | URL do PostgreSQL |
| `CORS_ALLOWED_ORIGINS` | ✅ | ❌ | https://seu-frontend.vercel.app |
| `EMAIL_HOST_USER` | ✅ | ❌ | seu-email@gmail.com |
| `EMAIL_HOST_PASSWORD` | ✅ | ❌ | App password do Gmail |
| `VITE_API_URL` | ❌ | ✅ | URL do backend |

---

## Deployment Passo a Passo

### 1. Backend (Render)

1. Conecte seu repo GitHub no Render
2. Selecione branch `main`
3. Adicione as variáveis de ambiente listadas acima
4. Deploy automático quando fizer push

```bash
# Localmente, antes de fazer push:
git add .
git commit -m "Deploy config"
git push origin main
```

### 2. Frontend (Vercel)

1. Conecte seu repo GitHub no Vercel
2. Framework: **Vite**
3. Build command: `bun run build`
4. Output directory: `dist`
5. Adicione `VITE_API_URL`
6. Deploy automático

---

## Verificação

Após deploy, teste a conexão:

```bash
# Teste o backend
curl https://seu-backend.onrender.com/api/v1/utils/datetime/

# Teste o frontend
curl https://seu-frontend.vercel.app
```

Se ambos respondem, está pronto! 🎉
