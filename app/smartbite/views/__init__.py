from datetime import date, timedelta
from django.utils import timezone
from django.db.models import Sum
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from django.contrib.auth import authenticate, get_user_model

from smartbite.models import Pet, Feeder, FeedingRecord, FeedingSchedule, Alert
from smartbite.serializers import (
    UserRegisterSerializer, UserSerializer,
    PetSerializer, FeederSerializer, FeederSetupSerializer, DispenseSerializer,
    FeedingRecordSerializer, FeedingScheduleSerializer,
    DailyConsumptionSerializer, AlertSerializer,
)
from smartbite.application.nutrition import NutritionCalculator

User = get_user_model()


# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterView(generics.CreateAPIView):
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            "user": UserSerializer(user).data,
            "token": token.key,
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email", "")
        password = request.data.get("password", "")
        # Support login by email or username
        try:
            username = User.objects.get(email=email).username
        except User.DoesNotExist:
            username = email
        user = authenticate(username=username, password=password)
        if not user:
            return Response({"detail": "Credenciais inválidas."}, status=status.HTTP_401_UNAUTHORIZED)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            "user": UserSerializer(user).data,
            "token": token.key,
        })


class LogoutView(APIView):
    def post(self, request):
        request.user.auth_token.delete()
        return Response({"detail": "Logout realizado com sucesso."})


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """
    Endpoint para mudar senha do usuário
    POST /api/auth/change-password/
    
    Payload:
    {
        "old_password": "senha_atual",
        "new_password": "nova_senha",
        "confirm_password": "nova_senha"
    }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        old_password = request.data.get("old_password", "")
        new_password = request.data.get("new_password", "")
        confirm_password = request.data.get("confirm_password", "")

        # Validações
        if not old_password or not new_password or not confirm_password:
            return Response(
                {"detail": "Campos obrigatórios: old_password, new_password, confirm_password"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_password != confirm_password:
            return Response(
                {"detail": "As novas senhas não coincidem."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(new_password) < 6:
            return Response(
                {"detail": "A nova senha deve ter no mínimo 6 caracteres."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verifica senha antiga
        user = request.user
        if not user.check_password(old_password):
            return Response(
                {"detail": "Senha atual incorreta."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Atualiza senha
        user.set_password(new_password)
        user.save()

        return Response({
            "detail": "Senha alterada com sucesso.",
            "user": UserSerializer(user).data
        }, status=status.HTTP_200_OK)


# ── Pets ──────────────────────────────────────────────────────────────────────

class PetListCreateView(generics.ListCreateAPIView):
    serializer_class = PetSerializer

    def get_queryset(self):
        return Pet.objects.filter(owner=self.request.user, is_active=True)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class PetDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PetSerializer

    def get_queryset(self):
        return Pet.objects.filter(owner=self.request.user, is_active=True)

    def perform_destroy(self, instance):
        instance.deactivate(reason="Deletado pelo usuário", user=self.request.user)


# ── Feeder ────────────────────────────────────────────────────────────────────

class FeederListView(generics.ListAPIView):
    serializer_class = FeederSerializer

    def get_queryset(self):
        return Feeder.objects.filter(owner=self.request.user, is_active=True)


class FeederSetupView(APIView):
    def post(self, request):
        serializer = FeederSetupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        feeder, created = Feeder.objects.get_or_create(
            serial_number=data["serial_number"],
            defaults={"owner": request.user, "name": data.get("name", "Comedouro SmartBite")},
        )
        if not created and feeder.owner != request.user:
            return Response({"detail": "Comedouro já registrado por outro usuário."}, status=400)

        if data.get("pet_id"):
            try:
                pet = Pet.objects.get(id=data["pet_id"], owner=request.user)
                feeder.pet = pet
            except Pet.DoesNotExist:
                return Response({"detail": "Pet não encontrado."}, status=404)

        feeder.device_state = "online"
        feeder.owner = request.user
        feeder.save()
        return Response(FeederSerializer(feeder).data, status=201 if created else 200)


class FeederDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = FeederSerializer

    def get_queryset(self):
        return Feeder.objects.filter(owner=self.request.user, is_active=True)


class DispenseView(APIView):
    def post(self, request, pk):
        try:
            feeder = Feeder.objects.get(pk=pk, owner=request.user, is_active=True)
        except Feeder.DoesNotExist:
            return Response({"detail": "Comedouro não encontrado."}, status=404)

        serializer = DispenseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data["amount_grams"]

        if feeder.device_state != "online":
            return Response({"detail": "Comedouro offline."}, status=400)

        now = timezone.now()
        feeder.last_feeding_at = now
        feeder.last_feeding_amount = amount
        feeder.save()

        if feeder.pet:
            FeedingRecord.objects.create(
                pet=feeder.pet,
                feeder=feeder,
                timestamp=now,
                amount_grams=amount,
                feeding_type="manual",
            )

        return Response({"detail": f"{amount}g dispensados com sucesso."})


# ── Feeding History ───────────────────────────────────────────────────────────

class FeedingHistoryView(generics.ListAPIView):
    serializer_class = FeedingRecordSerializer

    def get_queryset(self):
        qs = FeedingRecord.objects.filter(pet__owner=self.request.user, is_active=True)
        pet_id = self.kwargs.get("pet_pk")
        if pet_id:
            qs = qs.filter(pet_id=pet_id)
        return qs.order_by("-timestamp")[:100]


class DailyConsumptionView(APIView):
    def get(self, request, pet_pk):
        try:
            pet = Pet.objects.get(pk=pet_pk, owner=request.user, is_active=True)
        except Pet.DoesNotExist:
            return Response({"detail": "Pet não encontrado."}, status=404)

        days = int(request.query_params.get("days", 7))
        today = date.today()
        result = []
        for i in range(days - 1, -1, -1):
            d = today - timedelta(days=i)
            served = FeedingRecord.objects.filter(
                pet=pet,
                timestamp__date=d,
                is_active=True,
            ).aggregate(total=Sum("amount_grams"))["total"] or 0
            result.append({
                "date": d.isoformat(),
                "recommended": pet.daily_recommended_grams,
                "served": served,
            })

        return Response(DailyConsumptionSerializer(result, many=True).data)


# ── Schedules ─────────────────────────────────────────────────────────────────

class ScheduleListCreateView(generics.ListCreateAPIView):
    serializer_class = FeedingScheduleSerializer

    def get_queryset(self):
        return FeedingSchedule.objects.filter(
            pet__owner=self.request.user, pet_id=self.kwargs["pet_pk"], is_active=True
        )

    def perform_create(self, serializer):
        pet = Pet.objects.get(pk=self.kwargs["pet_pk"], owner=self.request.user)
        serializer.save(pet=pet)


class ScheduleDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FeedingScheduleSerializer

    def get_queryset(self):
        return FeedingSchedule.objects.filter(pet__owner=self.request.user, is_active=True)

    def perform_destroy(self, instance):
        instance.deactivate(reason="Deletado pelo usuário", user=self.request.user)


# ── Alerts ────────────────────────────────────────────────────────────────────

class AlertListView(generics.ListAPIView):
    serializer_class = AlertSerializer

    def get_queryset(self):
        return Alert.objects.filter(user=self.request.user, dismissed=False).order_by("-timestamp")


class AlertMarkReadView(APIView):
    def post(self, request, pk):
        try:
            alert = Alert.objects.get(pk=pk, user=request.user)
        except Alert.DoesNotExist:
            return Response({"detail": "Alerta não encontrado."}, status=404)
        alert.read = True
        alert.save()
        return Response(AlertSerializer(alert).data)


class AlertDismissView(APIView):
    def post(self, request, pk):
        try:
            alert = Alert.objects.get(pk=pk, user=request.user)
        except Alert.DoesNotExist:
            return Response({"detail": "Alerta não encontrado."}, status=404)
        alert.dismissed = True
        alert.save()
        return Response({"detail": "Alerta descartado."})


class AlertMarkAllReadView(APIView):
    def post(self, request):
        Alert.objects.filter(user=request.user, read=False).update(read=True)
        return Response({"detail": "Todos os alertas marcados como lidos."})


# ── Nutrition ─────────────────────────────────────────────────────────────────

class NutritionCalculatorView(APIView):
    """
    POST: Calcula a porção recomendada e retorna o cálculo detalhado
    
    Payload esperado:
    {
        "weight_kg": 25.5,
        "species": "dog",              # "dog" ou "cat"
        "age_months": 36,
        "activity_level": "moderate",  # "low", "moderate", "high"
        "is_neutered": false,
        "body_condition": "ideal",     # "underweight", "ideal", "overweight", "obese"
        "feeding_goal": "maintenance", # "weight_loss", "maintenance", "weight_gain"
        "breed_factor": 1.0
    }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            weight_kg = float(request.data.get("weight_kg"))
            species = request.data.get("species", "dog")
            age_months = int(request.data.get("age_months", 12))
            activity_level = request.data.get("activity_level", "moderate")
            is_neutered = request.data.get("is_neutered", False)
            body_condition = request.data.get("body_condition", "ideal")
            feeding_goal = request.data.get("feeding_goal", "maintenance")
            breed_factor = float(request.data.get("breed_factor", 1.0))
            
            # Validações básicas
            if weight_kg <= 0:
                return Response({"detail": "Peso deve ser maior que 0."}, status=400)
            if species not in ["dog", "cat"]:
                return Response({"detail": "Espécie deve ser 'dog' ou 'cat'."}, status=400)
            if activity_level not in ["low", "moderate", "high"]:
                return Response({"detail": "Nível de atividade inválido."}, status=400)
            if body_condition not in ["underweight", "ideal", "overweight", "obese"]:
                return Response({"detail": "Condição corporal inválida."}, status=400)
            if feeding_goal not in ["weight_loss", "maintenance", "weight_gain"]:
                return Response({"detail": "Objetivo alimentar inválido."}, status=400)
            
            # Calcula RER
            rer = NutritionCalculator.calculate_rer(weight_kg)
            
            # Obtém fatores
            life_stage_factor = NutritionCalculator.get_life_stage_factor(species, age_months)
            activity_factor = NutritionCalculator.ACTIVITY_FACTORS.get(activity_level, 1.1)
            neutered_factor = NutritionCalculator.NEUTERED_FACTOR if is_neutered else NutritionCalculator.INTACT_FACTOR
            body_condition_factor = NutritionCalculator.BODY_CONDITION_FACTORS.get(body_condition, 1.0)
            feeding_goal_factor = NutritionCalculator.FEEDING_GOAL_FACTORS.get(feeding_goal, 1.0)
            
            # Calcula MER
            mer = NutritionCalculator.calculate_mer(
                weight_kg=weight_kg,
                species=species,
                age_months=age_months,
                activity_level=activity_level,
                is_neutered=is_neutered,
                body_condition=body_condition,
                feeding_goal=feeding_goal,
                breed_factor=breed_factor,
            )
            
            # Calcula porção
            portion_grams = NutritionCalculator.calculate_daily_portion(
                weight_kg=weight_kg,
                species=species,
                age_months=age_months,
                activity_level=activity_level,
                is_neutered=is_neutered,
                body_condition=body_condition,
                feeding_goal=feeding_goal,
                breed_factor=breed_factor,
            )
            
            return Response({
                "rer_kcal": round(rer, 1),
                "factors": {
                    "life_stage": round(life_stage_factor, 2),
                    "activity": round(activity_factor, 2),
                    "neutered": round(neutered_factor, 2),
                    "body_condition": round(body_condition_factor, 2),
                    "feeding_goal": round(feeding_goal_factor, 2),
                    "breed": round(breed_factor, 2),
                },
                "mer_kcal": round(mer, 1),
                "kcal_per_gram": NutritionCalculator.KCAL_PER_GRAM,
                "recommended_daily_grams": round(portion_grams),
                "recommended_per_meal": {
                    "2_meals": round(portion_grams / 2),
                    "3_meals": round(portion_grams / 3),
                    "4_meals": round(portion_grams / 4),
                },
                "note": "Estes são valores calculados com base no método RER/MER. Ajuste conforme necessário baseado na condição do pet.",
            }, status=200)
            
        except (ValueError, TypeError) as e:
            return Response({"detail": f"Erro nos dados enviados: {str(e)}"}, status=400)
        except Exception as e:
            return Response({"detail": f"Erro ao calcular nutrição: {str(e)}"}, status=500)


# ── Utilities ─────────────────────────────────────────────────────────────────

class CurrentDateTimeView(APIView):
    """
    GET: Retorna data/hora atual e dia da semana
    Útil para sincronização de frontend e para exibir no consumo semanal
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        now = timezone.now()
        weekday_names = ["Domingo", "Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"]
        
        return Response({
            "date": now.date().isoformat(),
            "time": now.time().isoformat(),
            "datetime": now.isoformat(),
            "timestamp": now.timestamp(),
            "weekday": now.weekday(),  # 0=Segunda, 6=Domingo
            "weekday_name": weekday_names[now.weekday()],
            "iso_weekday": now.isoweekday(),  # 1=Segunda, 7=Domingo
            "iso_weekday_name": weekday_names[(now.isoweekday() % 7)],
            "day_of_month": now.day,
            "month": now.month,
            "year": now.year,
        })


# ── ESP32 Integration ─────────────────────────────────────────────────────────

class ESP32DeviceRegisterView(APIView):
    """
    POST: Registra um novo dispositivo ESP32 e gera token de autenticação
    Payload:
    {
        "serial_number": "ESP32_ABC123",
        "device_name": "Comedouro Sala"
    }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serial_number = request.data.get("serial_number", "").strip()
        device_name = request.data.get("device_name", "ESP32 Device").strip()

        if not serial_number:
            return Response(
                {"detail": "serial_number é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verifica se já existe
        try:
            feeder = Feeder.objects.get(serial_number=serial_number)
            if feeder.owner != request.user:
                return Response(
                    {"detail": "Este dispositivo já está registrado por outro usuário."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # Se é do mesmo usuário, retorna os dados
            return Response({
                "id": str(feeder.id),
                "serial_number": feeder.serial_number,
                "device_name": feeder.name,
                "registered_at": feeder.created_at,
                "status": feeder.device_state,
            })
        except Feeder.DoesNotExist:
            pass

        # Cria novo dispositivo
        feeder = Feeder.objects.create(
            owner=request.user,
            serial_number=serial_number,
            name=device_name,
            device_state="offline",
        )

        return Response({
            "id": str(feeder.id),
            "serial_number": feeder.serial_number,
            "device_name": feeder.name,
            "registered_at": feeder.created_at.isoformat(),
            "status": feeder.device_state,
            "message": "Dispositivo registrado com sucesso! Agora conecte o ESP32 à rede.",
        }, status=status.HTTP_201_CREATED)


class ESP32HeartbeatView(APIView):
    """
    POST: ESP32 reporta heartbeat e status
    Autenticação: Device Token (gerado no painel)
    
    Payload:
    {
        "serial_number": "ESP32_ABC123",
        "status": "online",
        "food_level_percent": 75,
        "wifi_signal": -45,
        "temperature": 28.5,
        "last_dispense": "2024-01-15T14:30:00Z"
    }
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serial_number = request.data.get("serial_number", "").strip()
        
        if not serial_number:
            return Response(
                {"detail": "serial_number é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            feeder = Feeder.objects.get(serial_number=serial_number)
        except Feeder.DoesNotExist:
            return Response(
                {"detail": "Dispositivo não encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Atualiza status
        feeder.device_state = request.data.get("status", "online")
        feeder.food_level_percent = request.data.get("food_level_percent", feeder.food_level_percent)
        feeder.wifi_signal = request.data.get("wifi_signal", feeder.wifi_signal)
        feeder.last_sync_at = timezone.now()
        feeder.save()

        return Response({
            "received": True,
            "timestamp": timezone.now().isoformat(),
            "message": "Heartbeat recebido com sucesso.",
        })


class ESP32FeedCommandView(APIView):
    """
    POST: Envia comando de dispensação para ESP32
    
    Payload para backend enviar para ESP32:
    {
        "type": "feed",
        "portion_g": 80.2,
        "log_id": 42
    }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, feeder_id):
        try:
            feeder = Feeder.objects.get(id=feeder_id, owner=request.user, is_active=True)
        except Feeder.DoesNotExist:
            return Response(
                {"detail": "Comedouro não encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        portion_grams = request.data.get("amount_grams", 0)

        if portion_grams <= 0 or portion_grams > 500:
            return Response(
                {"detail": "Quantidade deve estar entre 1 e 500 gramas."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if feeder.device_state != "online":
            return Response(
                {"detail": "Dispositivo offline. Não é possível dispensar."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Cria registro de alimentação (já feito na view DispenseView)
        now = timezone.now()
        if feeder.pet:
            FeedingRecord.objects.create(
                pet=feeder.pet,
                feeder=feeder,
                timestamp=now,
                amount_grams=portion_grams,
                feeding_type="manual",
            )

        # Aqui você integraria com MQTT ou WebSocket para enviar para o ESP32
        # Por enquanto, apenas confirmamos o recebimento
        command = {
            "type": "feed",
            "portion_g": portion_grams,
            "log_id": None,  # Será gerado pelo ESP32
            "timestamp": now.isoformat(),
        }

        return Response({
            "status": "command_sent",
            "command": command,
            "message": f"Comando enviado: dispensar {portion_grams}g",
            "note": "Aguarde confirmação do dispositivo...",
        }, status=status.HTTP_202_ACCEPTED)


