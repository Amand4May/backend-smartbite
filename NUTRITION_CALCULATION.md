# 📊 Cálculo de Nutrição RER/MER - Documentação

## Visão Geral

O sistema SmartBite agora calcula automaticamente a porção diária recomendada para cada animal usando a **fórmula veterinária padrão RER/MER** (Resting Energy Requirement / Maintenance Energy Requirement).

## Fórmula Base

### RER (Resting Energy Requirement)
```
RER = 70 × peso^0.75
```
Calcula a energia necessária para o animal em repouso, em kcal/dia.

### MER (Maintenance Energy Requirement)
```
MER = RER × (fatores multiplicadores)
```
Calcula a energia total necessária baseada em vários fatores.

### Porção Diária
```
Porção (g) = MER / kcal_por_grama
```
Padrão: 4 kcal/grama (usual em rações comerciais)

## Fatores Multiplicadores

### 1. **Fase de Vida**
Ajusta o requerimento calórico conforme a idade do animal:

| Espécie | Filhote (0-12m) | Adulto (1-7a) | Sênior (7+a) |
|---------|-----------------|---------------|-------------|
| Cachorro | 2.5 | 1.5 | 1.15 |
| Gato | 2.5 | 1.4 | 1.1 |

### 2. **Castração**
- **Castrado/Esterilizado**: ×0.85
- **Inteiro**: ×1.0

Animais castrados consomem menos energia devido ao metabolismo mais lento.

### 3. **Nível de Atividade**
- **Baixo** (sedentário): ×0.8
- **Moderado** (normal): ×1.1
- **Alto** (muito ativo): ×1.4

### 4. **Condição Corporal**
Ajusta baseado no peso atual vs. peso ideal:

| Condição | Fator |
|----------|-------|
| Abaixo do peso | ×1.2 |
| Peso ideal | ×1.0 |
| Sobrepeso | ×0.85 |
| Obeso | ×0.7 |

### 5. **Objetivo Alimentar**
- **Perda de peso**: ×0.75
- **Manutenção**: ×1.0
- **Ganho de peso**: ×1.25

### 6. **Fator de Raça** (Customizável)
Permite ajustes específicos por raça (padrão: 1.0)

## Exemplos de Cálculo

### Exemplo 1: Cachorro adulto 25kg, moderado, não castrado
```
RER = 70 × 25^0.75 = 782.6 kcal

Fatores aplicados:
- Fase de vida (adulto): 1.5
- Castração (inteiro): 1.0
- Atividade (moderada): 1.1
- Condição (ideal): 1.0
- Objetivo (manutenção): 1.0
- Raça: 1.0

MER = 782.6 × 1.5 × 1.0 × 1.1 × 1.0 × 1.0 × 1.0 = 1,291 kcal

Porção = 1,291 / 4 = 323g/dia
  - Café: 161g
  - Jantar: 161g
```

### Exemplo 2: Gato jovem 4kg, castrado, muito ativo
```
RER = 70 × 4^0.75 = 198.0 kcal

Fatores:
- Fase de vida (adulto): 1.4
- Castração: 0.85
- Atividade (alta): 1.4
- Condição (ideal): 1.0
- Objetivo (manutenção): 1.0
- Raça: 1.0

MER = 198.0 × 1.4 × 0.85 × 1.4 × 1.0 × 1.0 × 1.0 = 330 kcal

Porção = 330 / 4 = 82.5g/dia
  - Manhã: 41g
  - Noite: 41g
```

## Uso no Backend

### Model: Pet
Novos campos adicionados:

```python
is_neutered = models.BooleanField(default=False)  # Castrado?
body_condition = models.CharField(                 # Condição corporal
    choices=[
        ('underweight', 'Abaixo do peso'),
        ('ideal', 'Peso ideal'),
        ('overweight', 'Sobrepeso'),
        ('obese', 'Obeso'),
    ]
)
breed_factor = models.DecimalField(                # Fator específico da raça
    max_digits=3, decimal_places=2, default=1.0
)
daily_recommended_grams = models.PositiveIntegerField()  # Porção calculada
```

### Serializer: PetSerializer
O cálculo é feito automaticamente ao criar ou atualizar um pet:

```python
# Ao criar um pet
pet = Pet.objects.create(
    name="Rex",
    weight=25,
    age=60,
    species="dog",
    activity_level="moderate",
    ...
)
# daily_recommended_grams é calculado automaticamente

# Ao atualizar
pet.weight = 26
pet.save()
# daily_recommended_grams é recalculado
```

### API Endpoint: `/api/nutrition/calculate/`
**Método**: POST  
**Autenticação**: JWT Token  

Permite calcular nutrição sem salvar um pet (útil para onboarding/simulação).

**Request:**
```json
{
    "weight_kg": 25,
    "species": "dog",
    "age_months": 60,
    "activity_level": "moderate",
    "is_neutered": false,
    "body_condition": "ideal",
    "feeding_goal": "maintenance",
    "breed_factor": 1.0
}
```

**Response:**
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
    "kcal_per_gram": 4.0,
    "recommended_daily_grams": 323,
    "recommended_per_meal": {
        "2_meals": 162,
        "3_meals": 108,
        "4_meals": 81
    },
    "note": "Estes são valores calculados com base no método RER/MER..."
}
```

## Uso no Frontend (React)

### 1. Chamar a API de Cálculo
Útil durante o onboarding para mostrar estimativa:

```typescript
const response = await fetch(`${API_URL}/api/nutrition/calculate/`, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Token ${token}`,
    },
    body: JSON.stringify({
        weight_kg: 25,
        species: 'dog',
        age_months: 60,
        activity_level: 'moderate',
        is_neutered: false,
        body_condition: 'ideal',
        feeding_goal: 'maintenance',
        breed_factor: 1.0,
    }),
});

const data = await response.json();
console.log(`Porção recomendada: ${data.recommended_daily_grams}g/dia`);
```

### 2. Mostrar Informação no Perfil do Pet
O valor já vem no endpoint `/api/pets/<id>/`:

```json
{
    "id": "uuid",
    "name": "Rex",
    "daily_recommended_grams": 323,
    ...
}
```

### 3. Exibir Recomendação de Refeições
Usar os valores `recommended_per_meal` para sugerir quantidades:

```
Recomendações:
- 2 refeições: 162g cada
- 3 refeições: 108g cada
- 4 refeições: 81g cada
```

## Migração do Banco de Dados

Execute após deploy:

```bash
python manage.py migrate
```

A migração `0004_add_nutrition_fields.py` adiciona:
- Campo `is_neutered`
- Campo `body_condition`
- Campo `breed_factor`

## Considerações Importantes

1. **Valores iniciais**: Se os novos campos não forem preenchidos, usam-se defaults:
   - `is_neutered`: False
   - `body_condition`: 'ideal'
   - `breed_factor`: 1.0

2. **Ajustes veterinários**: Recomenda-se que usuários consultem um veterinário para validar as recomendações do sistema.

3. **Rações diferentes**: O cálculo assume 4 kcal/grama. Se usar ração com densidade calórica diferente, o valor deve ser ajustado manualmente.

4. **Monitoramento**: O sistema permite rastrear consumo real vs. recomendado através dos registros de alimentação.

## Próximas Melhorias

- [ ] Configurar kcal/grama da ração no perfil de usuário
- [ ] Alertas se consumo > recomendado por X dias
- [ ] Recomendações automáticas de ajuste baseadas em histórico
- [ ] Integração com histórico de peso para avaliar tendências
