from django.contrib.auth.models import AbstractUser
from django.db import models
from cloudinary.models import CloudinaryField


class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('customer', 'Customer'),
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='customer'
    )
    nomor_hp = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.username
        
class MenuLayanan(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    

    price_self = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    price_couple = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    price_group = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    price_family = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    duration = models.CharField(max_length=50, blank=True, null=True)
    image = CloudinaryField(
        'image',
        folder='layanan',
        blank=True,
        null=True
    )
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.title
        
class Booking(models.Model):

    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('rejected', 'Rejected'),
    )

    BOOKING_STATUS_CHOICES = (
        ('waiting', 'Waiting'),
        ('progress', 'On Progress'),
        ('finished', 'Selesai'),
        ('cancelled', 'Dibatalkan'),
    )
        
    PAYMENT_CHOICES = (
        ('qris', 'QRIS'),
        ('tunai', 'Tunai'),
    )

    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bookings',
        null=True,
        blank=True
    )

    nama = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    nomor_hp = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )

    package_name = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    kategori = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )
        
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_CHOICES,
        default='qris'
    )
    deskripsi = models.TextField(
        blank=True,
        null=True
    )
    date = models.DateField()

    time = models.TimeField()

    bukti_pembayaran = models.ImageField(
        upload_to='bukti_pembayaran/',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    booking_status = models.CharField(
        max_length=20,
        choices=BOOKING_STATUS_CHOICES,
        default='waiting'
    )
    harga = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    drive_link = models.URLField(
        blank=True,
        null=True,
        verbose_name="Google Drive Link"
    )

    def __str__(self):

        if self.customer:
            return f"{self.customer.username} - {self.package_name}"

        return self.nama or "Booking"

