from decimal import Decimal

from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser



class User(AbstractUser):
    # custom user model, role-based access
    ROLE_CHOICES = (
        ('farmer', 'Farmer'),
        ('porter', 'Porter'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='admin')
    phone_number = models.CharField(max_length=15, unique=True, blank=True, null=True)

    def __str__(self):
        return f"{self.username} {self.role}"


class BaseModel(models.Model):
    # abstract base model with common timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class FarmerProfile(BaseModel):
    # complete farmer profile model

    # Farmer profile
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='farmer_profile')
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    national_id_number = models.CharField(max_length=20, blank=True, null=True, unique=True)
    phone_number=models.CharField(max_length=15, blank=True,null=True, unique=True )


    # Farm info
    farm_name = models.CharField(max_length=200, blank=True, null=True)
    farm_size_acres = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    number_of_cows = models.IntegerField(default=0)
    membership_number = models.CharField(max_length=50, blank=True, null=True, unique=True)
    join_date = models.DateField(auto_now_add=True)
    mpesa_number = models.CharField(max_length=15, blank=True, null=True, unique=True)

    # stats auto-updated by system
    total_milk_delivered = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_earnings = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class PorterProfile(BaseModel):
    # porter/collector profile
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='porter_profile')
    profile_image = models.ImageField(upload_to='porter_profiles/', blank=True, null=True)
    employee_id = models.CharField(max_length=50, blank=True, null=True, unique=True)
    national_id_number = models.CharField(max_length=20, blank=True, null=True, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    route_name = models.CharField(max_length=100)
    assigned_farmers = models.ManyToManyField(FarmerProfile, related_name='assigned_porters', blank=True)
    hire_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    total_collections = models.IntegerField(default=0)
    total_litres_collected = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.employee_id}"


class MilkCollection(BaseModel):
    # milk collection model
    SESSION_CHOICES = (
        ('morning', 'Morning'),
        ('evening', 'Evening'),
    )
    farmer = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE, related_name='milk_collections')
    porter = models.ForeignKey(PorterProfile, on_delete=models.CASCADE, related_name='milk_collections')
    litres = models.DecimalField(max_digits=10, decimal_places=2)
    collection_date = models.DateField(auto_now_add=True)
    session = models.CharField(max_length=20, choices=SESSION_CHOICES, default='morning')
    price_per_litre = models.DecimalField(max_digits=10, decimal_places=2,default=50.0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"Milk Collection from {self.farmer.user.first_name} by {self.litres} on {self.collection_date}"

    def save(self, *args, **kwargs):
        # calculate total amount
        if self.litres is not None and self.price_per_litre is not None:
            self.total_amount = Decimal(self.litres) * Decimal(self.price_per_litre)
        super().save(*args, **kwargs)


class Feedback(BaseModel):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("resolved", "Resolved"),
        ("rejected", "Rejected"),
    )

    farmer = models.ForeignKey(
        FarmerProfile,
        on_delete=models.CASCADE,
        related_name="feedbacks"
    )

    title = models.CharField(max_length=200)
    description = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_feedbacks"
    )

    def __str__(self):
        return self.title


class Notice(BaseModel):
    TARGET_CHOICES = (
        ("all", "All"),
        ("farmers", "Farmers"),
        ("porters", "Porters"),
    )

    title = models.CharField(max_length=200)
    message = models.TextField()

    target = models.CharField(
        max_length=20,
        choices=TARGET_CHOICES,
        default="all"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    is_important = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class Payment(BaseModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    METHOD_CHOICES = [
        ('mpesa', 'Mpesa'),
        ('cash', 'Cash'),
    ]

    farmer = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    originator_conversation_id = models.CharField(max_length=100, blank=True, null=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    transaction_ref=models.CharField(max_length=100, unique=True, null=True)

    def __str__(self):
        ref = self.originator_conversation_id or str(self.id)
        return f"{ref} KES {self.amount}"