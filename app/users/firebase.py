import os
import django
import requests
import json

# CONFIGURA DJANGO
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

# IMPORTA MODELOS
from smartbite.models.user import User
from smartbite.models.feeding import FeedingSchedule

# LINK DO FIREBASE
FIREBASE_URL = "https://alicac-774a2-default-rtdb.firebaseio.com"

# DICIONÁRIO FINAL
dados_firebase = {
    "usuarios": {}
}

# PEGA TODOS USUÁRIOS
usuarios = User.objects.all()

for usuario in usuarios:

    # ESTRUTURA DO USUÁRIO
    dados_usuario = {
        "username": usuario.username,
        "horarios": {}
    }

    # PEGA AGENDAMENTOS
    horarios = FeedingSchedule.objects.filter(
        pet__owner=usuario,
        enabled=True
    )

    for i, horario in enumerate(horarios, start=1):

        # CONVERTE HORA PARA 1400
        hora_formatada = int(horario.time.strftime("%H%M"))

        # ADICIONA HORÁRIO
        dados_usuario["horarios"][str(i)] = {
            "hora": hora_formatada,
            "peso": horario.amount_grams
        }

    # SALVA NO JSON FINAL
    dados_firebase["usuarios"][str(usuario.id)] = dados_usuario

# MOSTRA JSON
print(json.dumps(dados_firebase, indent=4, ensure_ascii=False))

# ENVIA PARA FIREBASE
requisicao = requests.put(
    f"{FIREBASE_URL}/usuarios.json",
    json=dados_firebase["usuarios"]
)

# RESULTADO
if requisicao.status_code == 200:
    print("\n✅ Dados enviados com sucesso!")
else:
    print("\n❌ Erro ao enviar:")
    print(requisicao.text)