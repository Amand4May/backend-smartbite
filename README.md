# SmartBite — Backend Django

API REST para o app SmartBite, comedouro inteligente para pets.

## Stack

- **Django 5** + **Django REST Framework**
- **PostgreSQL** como banco de dados
- **Token Authentication** (DRF)
- **drf-yasg** para documentação Swagger/ReDoc
- **django-cors-headers** para integração com o front-end React

---

## Configuração & Variáveis de Ambiente

### Render (Production)

Adicione as seguintes variáveis de ambiente no painel do Render:

```
DJANGO_SECRET_KEY=sua-chave-secreta-aqui
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=seu-dominio.onrender.com
DATABASE_URL=postgresql://user:password@host/dbname
CORS_ALLOWED_ORIGINS=https://seu-frontend.vercel.app
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-ou-app-key
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=seu-email@gmail.com
```

### Desenvolvimento Local

```bash
cp .env.example .env
# Edite o .env com suas credenciais locais
```

---

## Rodando com Docker

```bash
# 1. Suba os containers
docker-compose up --build

# 2. Execute as migrations
docker-compose exec web python manage.py migrate

# 3. Crie um superusuário (opcional)
docker-compose exec web python manage.py createsuperuser
```

Acesse:
- **API:** http://localhost:8000/api/v1/
- **Swagger:** http://localhost:8000/api/docs/
- **Admin:** http://localhost:8000/admin/

---

## Rodando Localmente

```bash
cd app
pip install -r requirements/base.txt

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
| POST | `/api/v1/auth/logout/` | Logout |
| GET/PATCH | `/api/v1/auth/me/` | Perfil do usuário |
| POST | `/api/v1/auth/change-password/` | Mudar senha |

### Pets

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET/POST | `/api/v1/pets/` | Listar / criar pets |
| GET/PATCH/DELETE | `/api/v1/pets/{id}/` | Detalhes / editar / remover |
| GET | `/api/v1/pets/{id}/history/` | Histórico de alimentações |
| GET | `/api/v1/pets/{id}/consumption/` | Consumo diário (últimos 7 dias) |
| GET/POST | `/api/v1/pets/{id}/schedules/` | Agendamentos |
| GET/PATCH/DELETE | `/api/v1/schedules/{id}/` | Editar / remover agendamento |

### Nutrição

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/nutrition/calculate/` | Calcular porção (RER/MER) |

### Comedouros

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/feeders/` | Listar comedouros |
| POST | `/api/v1/feeders/setup/` | Cadastrar/vincular comedouro |
| GET/PATCH | `/api/v1/feeders/{id}/` | Detalhes / editar |
| POST | `/api/v1/feeders/{id}/dispense/` | Dispensar ração |
| POST | `/api/v1/feeders/{id}/feed-command/` | Comando de alimentação (ESP32) |

### Alertas

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/alerts/` | Listar alertas ativos |
| POST | `/api/v1/alerts/mark-all-read/` | Marcar todos como lidos |
| POST | `/api/v1/alerts/{id}/read/` | Marcar como lido |
| POST | `/api/v1/alerts/{id}/dismiss/` | Descartar |

### Utilitários

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/utils/datetime/` | Data/hora atual e dia da semana |

### ESP32 Integration

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/esp32/register/` | Registrar novo dispositivo |
| POST | `/api/v1/esp32/heartbeat/` | Heartbeat do dispositivo |

---

## Cálculo de Nutrição (RER/MER)

Veja [NUTRITION_CALCULATION.md](./NUTRITION_CALCULATION.md) para documentação completa.

### Exemplo de Uso

```bash
curl -X POST http://localhost:8000/api/v1/nutrition/calculate/ \
  -H "Authorization: Token seu-token" \
  -H "Content-Type: application/json" \
  -d '{
    "weight_kg": 25,
    "species": "dog",
    "age_months": 60,
    "activity_level": "moderate",
    "is_neutered": false,
    "body_condition": "ideal",
    "feeding_goal": "maintenance",
    "breed_factor": 1.0
  }'
```

### Resposta

```json
{
  "rer_kcal": 782.6,
  "factors": {
    "life_stage": 1.5,
    "activity": 1.1,
    "neutered": 1.0,
    "body_condition": 1.0,
    "feeding_goal": 1.0,
    "breed": 1.0
  },
  "mer_kcal": 1291.3,
  "recommended_daily_grams": 323,
  "recommended_per_meal": {
    "2_meals": 162,
    "3_meals": 108,
    "4_meals": 81
  }
}
```

---

## ESP32 Integration

### Fluxo de Comunicação

1. **Backend → ESP32**: Comando de dispensação
   ```json
   {
     "type": "feed",
     "portion_g": 80.2,
     "log_id": 42
   }
   ```

2. **ESP32 → Backend**: Confirmação e status
   ```json
   {
     "type": "feed_done",
     "dispensed_g": 79.5,
     "log_id": 42,
     "pet_id": 1
   }
   ```

3. **ESP32 → Backend**: Relatório de nível
   ```json
   {
     "type": "weight",
     "weight_g": 450.0
   }
   ```

4. **ESP32 → Backend**: Keep-alive
   ```json
   {
     "type": "ping"
   }
   ```

---

## Modelos & Campos

### User (Customizado)

```python
- id: UUID
- username, email, password
- phone, avatar_url
- notification_email: bool
- notification_push: bool
- notification_low_food: bool
- notification_pet_not_eating: bool
- notification_device_offline: bool
- low_food_threshold: int (%)
```

### Pet

```python
- id: UUID
- owner: ForeignKey(User)
- name: string
- species: 'dog' | 'cat'
- breed: string
- weight: decimal (kg)
- age: int (meses)
- activity_level: 'low' | 'moderate' | 'high'
- feeding_goal: 'weight_loss' | 'maintenance' | 'weight_gain'
- is_neutered: bool
- body_condition: 'underweight' | 'ideal' | 'overweight' | 'obese'
- breed_factor: decimal (1.0 padrão)
- daily_recommended_grams: int (calculado automaticamente)
```

### Feeder

```python
- id: UUID
- owner: ForeignKey(User)
- pet: ForeignKey(Pet, null=True)
- serial_number: string (único)
- name: string
- device_state: 'online' | 'offline' | 'processing'
- food_level_percent: int
- last_feeding_at: datetime
- last_feeding_amount: int (g)
- wifi_signal: int (dBm)
- last_sync_at: datetime
- firmware_version: string
```

---

## Autenticação

Use `Token Authentication`. Inclua o header em todas as requisições autenticadas:

```
Authorization: Token seu-token-aqui
```

---

## Deploy

### Render

1. Conecte seu repositório GitHub
2. Configure as variáveis de ambiente
3. Execute a migration automática:
   ```
   python manage.py migrate
   ```

---

## Scripts Úteis

```bash
# Criar superusuário
python manage.py createsuperuser

# Fazer migrations
python manage.py makemigrations
python manage.py migrate

# Resetar banco (cuidado!)
python manage.py flush

# Importar dados
python manage.py loaddata data.json

# Exportar dados
python manage.py dumpdata > data.json
```

---

## Licença

MIT

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
