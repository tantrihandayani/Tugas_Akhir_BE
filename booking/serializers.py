import re
from rest_framework import serializers
from .models import MenuLayanan, User, Booking
from django.contrib.auth.password_validation import validate_password


class LayananSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuLayanan
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'nomor_hp']

    def validate_nomor_hp(self, value):
        if not re.match(r"^08\d{8,11}$", value):
            raise serializers.ValidationError(
                "Nomor HP harus diawali 08 dan terdiri dari 10-13 digit."
            )
        return value


class RegisterSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'nomor_hp']

    def validate_nomor_hp(self, value):
        if not re.match(r"^08\d{8,11}$", value):
            raise serializers.ValidationError(
                "Nomor HP harus diawali 08 dan terdiri dari 10-13 digit."
            )
        return value

    def create(self, validated_data):

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            nomor_hp=validated_data.get('nomor_hp')
        )

        user.role = 'customer'
        user.save()

        return user
    
class ChangePasswordSerializer(serializers.Serializer):

    old_password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"}
    )

    new_password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"}
    )

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        if attrs["old_password"] == attrs["new_password"]:
            raise serializers.ValidationError(
                {
                    "new_password":
                    "Password baru tidak boleh sama dengan password lama."
                }
            )
        return attrs

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = "__all__"

    def create(self, validated_data):

        layanan = validated_data.get("layanan")

        package_name = validated_data.get("package_name")
        kategori = validated_data.get("kategori", "").lower()

        # Jika layanan tidak dikirim,
        # cari berdasarkan package_name sebagai fallback
        if layanan is None and package_name:
            layanan = MenuLayanan.objects.filter(
                title=package_name
            ).first()

            if layanan:
                validated_data["layanan"] = layanan

        harga = 0

        if layanan:
            if kategori == "self":
                harga = layanan.price_self

            elif kategori == "couple":
                harga = layanan.price_couple

            elif kategori == "group":
                harga = layanan.price_group

            elif kategori == "family":
                harga = layanan.price_family

        validated_data["harga"] = harga

        # Booking manual oleh admin
        if validated_data.get("customer") is None:
            validated_data["payment_status"] = "confirmed"
            validated_data["booking_status"] = "waiting"

        return Booking.objects.create(**validated_data)