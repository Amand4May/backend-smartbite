# SmartBite — Back-end Django

API REST para o app SmartBite, comedouro inteligente para pets.

## Stack

- **Django 5** + **Django REST Framework**
- **PostgreSQL** como banco de dados
- **Token Authentication** (DRF)
- **drf-yasg** para documentação Swagger/ReDoc
- **django-cors-headers** para integração com o front-end React

---

## Rodando com Docker

```bash
# 1. Copie o arquivo de ambiente
cp .env.example .env

# 2. Suba os containers
docker-compose up --build

# 3. Crie um superusuário (opcional)
docker-compose exec web python manage.py createsuperuser
```

Acesse:
- **API:** http://localhost:8000/api/v1/
- **Swagger:** http://localhost:8000/api/docs/
- **Admin:** http://localhost:8000/admin/

---

## Rodando localmente (sem Docker)

```bash
cd app
pip install -r requirements/base.txt

# Configure o .env ou exporte as variáveis manualmente
export POSTGRES_HOST=localhost
export POSTGRES_DB=smartbite
# ...

python manage.py migrate
python manage.py runserver
```

---

## Endpoints da API

### Autenticação

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/auth/register/` | Cadastro de novo usuário |
| POST | `/api/v1/auth/login/` | Login (retorna token) |
| POST | `/api/v1/auth/logout/` | Logout (invalida token) |
| GET/PATCH | `/api/v1/auth/me/` | Perfil do usuário logado |

### Pets

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET/POST | `/api/v1/pets/` | Listar / criar pets |
| GET/PATCH/DELETE | `/api/v1/pets/{id}/` | Detalhes / editar / remover pet |
| GET | `/api/v1/pets/{id}/history/` | Histórico de alimentações |
| GET | `/api/v1/pets/{id}/consumption/` | Consumo diário (últimos 7 dias) |
| GET/POST | `/api/v1/pets/{id}/schedules/` | Agendamentos do pet |

### Comedouros

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/feeders/` | Listar comedouros |
| POST | `/api/v1/feeders/setup/` | Cadastrar/vincular comedouro |
| GET/PATCH | `/api/v1/feeders/{id}/` | Detalhes / editar comedouro |
| POST | `/api/v1/feeders/{id}/dispense/` | Dispensar ração manualmente |

### Agendamentos

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET/PATCH/DELETE | `/api/v1/schedules/{id}/` | Editar / remover agendamento |

### Alertas

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/alerts/` | Listar alertas ativos |
| POST | `/api/v1/alerts/mark-all-read/` | Marcar todos como lidos |
| POST | `/api/v1/alerts/{id}/read/` | Marcar alerta como lido |
| POST | `/api/v1/alerts/{id}/dismiss/` | Descartar alerta |

---

## Autenticação

Use o header `Authorization: Token <seu_token>` em todas as requisições autenticadas.

```bash
# Exemplo de login
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "senha123"}'

# Usar o token retornado
curl http://localhost:8000/api/v1/pets/ \
  -H "Authorization: Token abc123..."
```

---

## Modelos de Dados

- **User** — Usuário com campos de notificação e preferências
- **Pet** — Animal de estimação (espécie, raça, peso, objetivo alimentar)
- **Feeder** — Comedouro IoT (status, nível de ração, firmware)
- **FeedingRecord** — Histórico de cada alimentação
- **FeedingSchedule** — Agendamentos recorrentes por dia da semana
- **Alert** — Alertas gerados pelo sistema (ração baixa, pet não comeu etc.)
