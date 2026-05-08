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
