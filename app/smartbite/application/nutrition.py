"""
Serviço de cálculo de nutrição e porções usando método RER/MER
Fórmula veterinária padrão para cálculo de necessidade calórica
"""
from decimal import Decimal


class NutritionCalculator:
    """
    Calcula a porção diária recomendada usando a fórmula RER/MER
    
    RER = 70 × peso^0.75       (necessidade calórica em repouso)
    MER = RER × fatores        (necessidade de manutenção)
    Porção (g) = MER / kcal_por_grama
    """
    
    # Kcal por grama para diferentes tipos de ração (padrão veterinário: ~4 kcal/g)
    KCAL_PER_GRAM = 4.0
    
    # Fatores de vida por espécie e fase
    LIFE_STAGE_FACTORS = {
        "dog": {
            "puppy": 2.5,      # Filhote (0-12 meses)
            "adult": 1.5,      # Adulto (1-7 anos)
            "senior": 1.15,    # Sênior (7+ anos)
        },
        "cat": {
            "kitten": 2.5,     # Filhote (0-12 meses)
            "adult": 1.4,      # Adulto (1-10 anos)
            "senior": 1.1,     # Sênior (10+ anos)
        }
    }
    
    # Fatores de atividade
    ACTIVITY_FACTORS = {
        "low": 0.8,           # Sedentário
        "moderate": 1.1,      # Moderado
        "high": 1.4,          # Muito ativo
    }
    
    # Fatores de castração
    NEUTERED_FACTOR = 0.85
    INTACT_FACTOR = 1.0
    
    # Fatores de condição corporal
    BODY_CONDITION_FACTORS = {
        "underweight": 1.2,   # Abaixo do peso
        "ideal": 1.0,         # Peso ideal
        "overweight": 0.85,   # Sobrepeso
        "obese": 0.7,         # Obeso
    }
    
    # Fatores de objetivo alimentar
    FEEDING_GOAL_FACTORS = {
        "weight_loss": 0.75,
        "maintenance": 1.0,
        "weight_gain": 1.25,
    }
    
    @staticmethod
    def calculate_rer(weight_kg: float) -> float:
        """
        Calcula RER (Resting Energy Requirement)
        Fórmula: RER = 70 × (peso em kg)^0.75
        
        Args:
            weight_kg: Peso do animal em quilogramas
            
        Returns:
            RER em kcal/dia
        """
        weight = Decimal(str(weight_kg))
        return float(70 * (weight ** Decimal("0.75")))
    
    @staticmethod
    def get_life_stage_factor(species: str, age_months: int) -> float:
        """
        Retorna o fator de fase de vida baseado na espécie e idade
        
        Args:
            species: "dog" ou "cat"
            age_months: Idade em meses
            
        Returns:
            Fator multiplicador da fase de vida
        """
        if species not in NutritionCalculator.LIFE_STAGE_FACTORS:
            return 1.5  # Padrão para adulto
        
        stages = NutritionCalculator.LIFE_STAGE_FACTORS[species]
        
        if age_months < 12:
            return stages.get("puppy" if species == "dog" else "kitten", 2.5)
        elif age_months < 84:  # 7 anos em meses
            return stages.get("adult", 1.5)
        else:
            return stages.get("senior", 1.15)
    
    @classmethod
    def calculate_mer(
        cls,
        weight_kg: float,
        species: str,
        age_months: int,
        activity_level: str = "moderate",
        is_neutered: bool = False,
        body_condition: str = "ideal",
        feeding_goal: str = "maintenance",
        breed_factor: float = 1.0,
    ) -> float:
        """
        Calcula MER (Maintenance Energy Requirement)
        MER = RER × (fatores multiplicadores)
        
        Args:
            weight_kg: Peso em kg
            species: "dog" ou "cat"
            age_months: Idade em meses
            activity_level: "low", "moderate" ou "high"
            is_neutered: Se o animal é castrado
            body_condition: "underweight", "ideal", "overweight", "obese"
            feeding_goal: "weight_loss", "maintenance", "weight_gain"
            breed_factor: Fator específico da raça (padrão: 1.0)
            
        Returns:
            MER em kcal/dia
        """
        # Calcula RER base
        rer = cls.calculate_rer(weight_kg)
        
        # Aplica fatores multiplicadores
        life_stage_factor = cls.get_life_stage_factor(species, age_months)
        neutered_factor = cls.NEUTERED_FACTOR if is_neutered else cls.INTACT_FACTOR
        activity_factor = cls.ACTIVITY_FACTORS.get(activity_level, 1.1)
        body_condition_factor = cls.BODY_CONDITION_FACTORS.get(body_condition, 1.0)
        feeding_goal_factor = cls.FEEDING_GOAL_FACTORS.get(feeding_goal, 1.0)
        
        # MER = RER × (fatores)
        mer = rer * life_stage_factor * neutered_factor * activity_factor * body_condition_factor * feeding_goal_factor * breed_factor
        
        return mer
    
    @classmethod
    def calculate_daily_portion(
        cls,
        weight_kg: float,
        species: str,
        age_months: int,
        activity_level: str = "moderate",
        is_neutered: bool = False,
        body_condition: str = "ideal",
        feeding_goal: str = "maintenance",
        breed_factor: float = 1.0,
        kcal_per_gram: float = None,
    ) -> float:
        """
        Calcula a porção diária recomendada em gramas
        Porção (g) = MER / kcal_por_grama
        
        Args:
            weight_kg: Peso em kg
            species: "dog" ou "cat"
            age_months: Idade em meses
            activity_level: "low", "moderate" ou "high"
            is_neutered: Se o animal é castrado
            body_condition: "underweight", "ideal", "overweight", "obese"
            feeding_goal: "weight_loss", "maintenance", "weight_gain"
            breed_factor: Fator específico da raça
            kcal_per_gram: Kcal por grama da ração (default: 4.0)
            
        Returns:
            Porção recomendada em gramas por dia
        """
        if kcal_per_gram is None:
            kcal_per_gram = cls.KCAL_PER_GRAM
        
        mer = cls.calculate_mer(
            weight_kg=weight_kg,
            species=species,
            age_months=age_months,
            activity_level=activity_level,
            is_neutered=is_neutered,
            body_condition=body_condition,
            feeding_goal=feeding_goal,
            breed_factor=breed_factor,
        )
        
        # Porção em gramas
        portion_grams = mer / kcal_per_gram
        
        return round(portion_grams, 1)


# Função helper para uso simples
def calculate_pet_portion(pet) -> int:
    """
    Calcula a porção diária recomendada para um pet
    
    Args:
        pet: Instância do modelo Pet
        
    Returns:
        Porção recomendada em gramas (inteiro)
    """
    portion = NutritionCalculator.calculate_daily_portion(
        weight_kg=float(pet.weight),
        species=pet.species,
        age_months=pet.age,
        activity_level=pet.activity_level,
        is_neutered=getattr(pet, 'is_neutered', False),
        body_condition=getattr(pet, 'body_condition', 'ideal'),
        feeding_goal=pet.feeding_goal,
        breed_factor=float(getattr(pet, 'breed_factor', 1.0)),
    )
    return round(portion)
