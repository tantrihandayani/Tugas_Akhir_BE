from django.contrib.auth import authenticate
from rest_framework.response import Response
from rest_framework.decorators import (api_view, permission_classes)
from rest_framework.permissions import IsAuthenticated
from .models import User, Booking, MenuLayanan
from .serializers import (LayananSerializer, BookingSerializer, RegisterSerializer, ChangePasswordSerializer,)
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import date
from django.db.models import Sum, Count
from .models import MenuLayanan  
from collections import defaultdict, Counter
import calendar
from datetime import datetime 
from .serializers import ChangePasswordSerializer
import os

from django.http import FileResponse, Http404
from django.conf import settings

def media_file(request, path):
    file_path = os.path.join(settings.MEDIA_ROOT, path)

    print("MEDIA_ROOT :", settings.MEDIA_ROOT)
    print("FILE PATH  :", file_path)
    print("EXISTS     :", os.path.exists(file_path))

    if not os.path.exists(file_path):
        raise Http404("File tidak ditemukan")

    return FileResponse(open(file_path, "rb"))



@api_view(['POST'])
def login_view(request):

    username = request.data.get('username')
    password = request.data.get('password')
    if not username or not password:
        return Response({
            "message": "Username dan password wajib diisi"
        }, status=400)
    user = authenticate(
        username=username,
        password=password
    )
    if user is not None:
        refresh = RefreshToken.for_user(user)
        return Response({
            "message": "Login berhasil",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "nomor_hp": user.nomor_hp,
            "role": user.role,
        })
    return Response({
        'message': 'Username atau password salah'
    }, status=400)

@api_view(['POST'])
def register_view(request):

    serializer = RegisterSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()

        return Response({
            "message": "Register berhasil"
        }, status=201)

    return Response(serializer.errors, status=400)

@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def profile_view(request):

    user = request.user

    if request.method == 'GET':
        return Response({
            "username": user.username,
            "email": user.email,
            "nomor_hp": user.nomor_hp,
        })

    if request.method == 'PATCH':

        user.username = request.data.get(
            "username",
            user.username
        )

        user.email = request.data.get(
            "email",
            user.email
        )

        user.nomor_hp = request.data.get(
            "nomor_hp",
            user.nomor_hp
        )

        user.save()

        return Response({
            "message": "Profile berhasil diupdate"
        })
        
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def change_password(request):

    serializer = ChangePasswordSerializer(data=request.data)

    if serializer.is_valid():

        user = request.user

        if not user.check_password(
            serializer.validated_data["old_password"]
        ):
            return Response(
                {"message": "Password lama salah."},
                status=400
            )

        user.set_password(
            serializer.validated_data["new_password"]
        )

        user.save()

        return Response({
            "message": "Password berhasil diubah."
        })

    return Response(
        serializer.errors,
        status=400
    )
        
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_history(request):

    bookings = Booking.objects.filter(
        customer=request.user
    ).order_by("-created_at")
    result = []
    for item in bookings:
        result.append({
            "id": item.id,
            "customer_id": (
                item.customer.id
                if item.customer
                else None
            ),
            "package_name": item.package_name,
            "kategori": item.kategori,
            "date": item.date.strftime("%d %B %Y"),
            "time": item.time.strftime("%H:%M"),
            "payment_method": item.payment_method,
            "payment_status": item.payment_status,
            "booking_status": item.booking_status,
            "harga": float(item.harga),
            "deskripsi": item.deskripsi,
            "nomor_hp": item.nomor_hp,
            "nama": item.nama,
            "drive_link": item.drive_link,
            "bukti_pembayaran": (
                request.build_absolute_uri(item.bukti_pembayaran.url)
                if item.bukti_pembayaran
                else None
            ),
            "created_at": item.created_at,
        })

    return Response(result)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def customer_list(request):
    print("USERNAME :", request.user.username)
    print("ROLE :", request.user.role)
    if request.user.role != "admin":
        return Response(
            {"message": "Unauthorized"},
            status=403
        )
    customers = User.objects.filter(
        role="customer"
    )
    result = []
    for customer in customers:
        bookings = Booking.objects.filter(
            customer=customer
        )
        total_booking = bookings.count()
        total_transaksi = (
            bookings.filter(
                payment_status="confirmed"
            ).aggregate(
                total=Sum("harga")
            )["total"] or 0
        )
        last_booking = bookings.order_by("-created_at").first()
        result.append({
            "id": customer.id,
            "username": customer.username,
            "email": customer.email,
            "nomor_hp": customer.nomor_hp,
            "total_booking": total_booking,
            "total_transaksi": total_transaksi,
            "last_booking": (
                str(last_booking.date)
                if last_booking
                else "-"
            ),
            "status": (
                last_booking.booking_status
                if last_booking
                else "-"
            )
        })

    return Response(result)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_statistic(request):

    bookings = Booking.objects.filter(
        customer=request.user
    )
    total_booking = bookings.count()
    total_pengeluaran = (
        bookings.aggregate(
            total=Sum("harga")
        )["total"] or 0
    )

    booking_selesai = bookings.filter(
        booking_status="finished"
    ).count()

    booking_waiting = bookings.filter(
        booking_status="waiting"
    ).count()

    booking_progress = bookings.filter(
        booking_status="progress"
    ).count()

    favorite = (
        bookings.values("package_name")
        .annotate(
            total=Count("package_name")
        )
        .order_by("-total")
        .first()
    )

    return Response({
        "total_booking": total_booking,
        "total_pengeluaran": float(total_pengeluaran),
        "booking_selesai": booking_selesai,
        "booking_waiting": booking_waiting,
        "booking_progress": booking_progress,
        "favorite_service":
            favorite["package_name"]
            if favorite
            else "-",
        "favorite_count":
            favorite["total"]
            if favorite
            else 0,
    })

@api_view(['GET', 'POST', 'PATCH'])
def get_booking(request, id=None):

    # AMBIL DATA
    if request.method == 'GET':
        bookings = Booking.objects.filter(
            payment_status="confirmed"
        ).order_by("date", "time")
        result = []
        for item in bookings:
            result.append({
                "id": item.id,
                "customer_id": item.customer.id if item.customer else None,
                "nama": item.nama,
                "nomor_hp": item.nomor_hp,
                "package_name": item.package_name,
                "kategori": item.kategori,
                "payment_method": item.payment_method,
                "date": str(item.date),
                "time": item.time.strftime("%H:%M") if item.time else None,
                "payment_status": item.payment_status,
                "booking_status": item.booking_status,
                "harga": float(item.harga),
                "drive_link": item.drive_link,
            })

        return Response(result)

    # TAMBAH DATA
    if request.method == 'POST':

        serializer = BookingSerializer(
            data=request.data
        )

        if serializer.is_valid():
            tanggal = request.data.get("date")
            jam = request.data.get("time")

            sudah_ada = Booking.objects.exclude(
                payment_status='rejected'
            ).filter(
                date=tanggal,
                time=jam
            ).exists()

            if sudah_ada:
                return Response(
                    {
                        "message":
                        "Jam tersebut sudah dibooking."
                    },
                    status=400
                )
                
            package_name = request.data.get(
                "package_name"
            )

            kategori = request.data.get(
                "kategori"
            )

            layanan = MenuLayanan.objects.filter(
                title=package_name
            ).first()

            harga = get_harga_layanan(
                layanan,
                kategori
            )
            customer = None

            customer = request.user if request.user.is_authenticated else None

            extra_data = {
                "harga": harga,
                "customer": customer,
            }

            # Booking manual oleh admin
            if customer is None:
                extra_data["payment_status"] = "confirmed"
                extra_data["booking_status"] = "waiting"

            serializer.save(**extra_data)

            print("USER:", request.user)
            print("AUTH:", request.user.is_authenticated)


            return Response({
                "message": "Booking berhasil ditambahkan"
            }, status=201)

        print(serializer.errors)  

        return Response(
            serializer.errors,
            status=400
    )
    
    if request.method == 'PATCH':

        try:
            booking = Booking.objects.get(id=id)

        except Booking.DoesNotExist:
            return Response(
                {"message": "Booking tidak ditemukan"},
                status=404
            )

        payment_status = request.data.get("payment_status")
        booking_status = request.data.get("booking_status")
        drive_link = request.data.get("drive_link")

        if payment_status is not None:
            booking.payment_status = payment_status

        if booking_status is not None:
            booking.booking_status = booking_status

        if drive_link is not None:
            booking.drive_link = drive_link

        booking.save()

        return Response({
            "message": "Status berhasil diupdate",
            "data": BookingSerializer(booking).data
        })

def get_harga_layanan(layanan, kategori):

    if not layanan:
        return 0
    kategori = (kategori or "").lower()
    if kategori == "self":
        return float(layanan.price_self)
    elif kategori == "couple":
        return float(layanan.price_couple)
    elif kategori == "group":
        return float(layanan.price_group)
    elif kategori == "family":
        return float(layanan.price_family)
    return 0
    
from collections import defaultdict
from datetime import datetime

@api_view(["GET"])
def laporan_pendapatan(request):

    bookings = Booking.objects.filter(
        booking_status="finished"
    )
    filter_type = request.GET.get("type")
    date = request.GET.get("date")
    month = request.GET.get("month")
    year = request.GET.get("year")

    if filter_type == "day" and date:
        bookings = bookings.filter(date=date)

    elif filter_type == "month" and month:
        try:
            y, m = month.split("-")
            bookings = bookings.filter(
                date__year=int(y),
                date__month=int(m),
            )
        except ValueError:
            pass

    elif filter_type == "year" and year:
        bookings = bookings.filter(
            date__year=int(year)
        )

    bookings = bookings.order_by("date")

    laporan = []
    pendapatan_bulanan = defaultdict(float)
    kategori_counter = Counter()
    kategori_pendapatan = defaultdict(float)

    total_pendapatan = 0

    for item in bookings:
        harga = float(item.harga)
        laporan.append({
            "id": item.id,
            "customer_id": item.customer.id if item.customer else None,
            "nama": item.nama,
            "paket": item.package_name,
            "tanggal": str(item.date),
            "metodeBayar": item.payment_method,
            "harga": harga,
        })
        total_pendapatan += harga
        bulan = item.date.strftime("%Y-%m")
        pendapatan_bulanan[bulan] += harga
        kategori_counter[item.package_name] += 1
        kategori_pendapatan[item.package_name] += harga

    # ===========================
    # CHART
    # ===========================

    chart = []
    nilai = []

    nama_bulan = [
        "Januari",
        "Februari",
        "Maret",
        "April",
        "Mei",
        "Juni",
        "Juli",
        "Agustus",
        "September",
        "Oktober",
        "November",
        "Desember",
    ]

    # ===========================
    # FILTER BULAN
    # ===========================

    if filter_type == "month" and month:

        tahun, bulan = map(int, month.split("-"))

        jumlah_hari = calendar.monthrange(tahun, bulan)[1]

        pendapatan_harian = defaultdict(float)

        for item in bookings:
            pendapatan_harian[item.date.day] += float(item.harga)

        for hari in range(1, jumlah_hari + 1):

            pendapatan = round(pendapatan_harian.get(hari, 0))

            chart.append({
                "bulan": str(hari),
                "pendapatan": pendapatan,
                "movingAverage": 0,
            })

            nilai.append(pendapatan)

    # ===========================
    # FILTER TAHUN / DEFAULT
    # ===========================

    else:

        if filter_type == "year" and year:
            tahun = int(year)
        else:
            tahun = datetime.now().year

        pendapatan_per_bulan = defaultdict(float)

        for item in bookings:
            pendapatan_per_bulan[item.date.month] += float(item.harga)

        for bulan in range(1, 13):

            pendapatan = round(
                pendapatan_per_bulan.get(bulan, 0)
            )

            chart.append({
                "bulan": nama_bulan[bulan - 1],
                "pendapatan": pendapatan,
                "movingAverage": 0,
            })

            nilai.append(pendapatan)

    # ===========================
    # MOVING AVERAGE (3 PERIODE)
    # ===========================

    for i in range(len(chart)):

        if i < 2:
            chart[i]["movingAverage"] = None
            continue

        data = [
            chart[i - 2]["pendapatan"],
            chart[i - 1]["pendapatan"],
            chart[i]["pendapatan"],
        ]

        if 0 in data:
            chart[i]["movingAverage"] = None
        else:
            chart[i]["movingAverage"] = round(
                sum(data) / 3
            )

    # ===========================
    # PREDIKSI BULAN BERIKUTNYA
    # ===========================

    bulan_aktif = [
        x for x in nilai
        if x > 0
    ]

    prediksi = None

    if len(bulan_aktif) >= 3:

        prediksi = round(
            sum(
                bulan_aktif[-3:]
            ) / 3
        )

    # ===========================
    # TREND
    # ===========================

    trend = None
    persentase = None

    if prediksi is not None:

        terakhir = bulan_aktif[-1]

        persentase = round(
            ((prediksi - terakhir) / terakhir) * 100,
            2,
        )

        if prediksi > terakhir:
            trend = "naik"

        elif prediksi < terakhir:
            trend = "turun"

        else:
            trend = "stabil"

    # ===========================
    # BULAN TERTINGGI
    # ===========================

    bulan_tertinggi = "-"
    pendapatan_tertinggi = 0

    if chart:

        terbesar = max(chart, key=lambda x: x["pendapatan"])

        bulan_tertinggi = terbesar["bulan"]
        pendapatan_tertinggi = terbesar["pendapatan"]

    # ===========================
    # KATEGORI FAVORIT
    # ===========================

    kategori_favorit = "-"
    jumlah_booking = 0
    kontribusi_kategori = 0

    if kategori_counter:

        kategori_favorit, jumlah_booking = kategori_counter.most_common(1)[0]

        kontribusi_kategori = kategori_pendapatan[kategori_favorit]

    # ===========================
    # RATA-RATA
    # ===========================

    rata_rata = round(
        total_pendapatan / len(bulan_aktif),
        2,
    ) if bulan_aktif else 0

    # ===========================
    # BULAN PREDIKSI
    # ===========================

    bulan_prediksi = "-"

    bulan_data = [
        datetime.strptime(key, "%Y-%m")
        for key in pendapatan_bulanan.keys()
    ]

    if bulan_data:

        terakhir = max(bulan_data)

        bulan_selanjutnya = terakhir.month + 1
        tahun_prediksi = terakhir.year

        if bulan_selanjutnya > 12:
            bulan_selanjutnya = 1
            tahun_prediksi += 1

        bulan_prediksi = (
            f"{nama_bulan[bulan_selanjutnya - 1]} {tahun_prediksi}"
        )
    
    # ===========================
    # INSIGHT
    # ===========================

    insight = (
        "Data historis belum mencukupi untuk melakukan prediksi "
        "menggunakan metode Moving Average 3 Periode. "
        "Sistem membutuhkan minimal tiga bulan data pendapatan."
    )

    if len(bulan_aktif) >= 3:

        if persentase > 10:

            insight = (
                f"Pendapatan diprediksi meningkat sebesar {persentase:.1f}% "
                f"dibanding periode terakhir. Tren ini menunjukkan perkembangan yang positif. "
                f"Kategori layanan '{kategori_favorit}' menjadi kontributor pendapatan terbesar."
            )

        elif persentase > 0:

            insight = (
                f"Pendapatan diprediksi meningkat sebesar {persentase:.1f}%. "
                f"Bisnis menunjukkan tren positif dengan kategori '{kategori_favorit}' "
                f"sebagai layanan yang paling diminati."
            )

        elif persentase < -10:

            insight = (
                f"Pendapatan diprediksi menurun sebesar {abs(persentase):.1f}%. "
                f"Disarankan melakukan evaluasi strategi promosi atau pengembangan layanan "
                f"agar tren dapat kembali meningkat."
            )

        elif persentase < 0:

            insight = (
                f"Pendapatan diprediksi menurun sebesar {abs(persentase):.1f}%, "
                f"namun penurunannya masih relatif kecil. "
                f"Monitoring pendapatan pada periode berikutnya tetap diperlukan."
            )

        else:

            insight = (
                "Pendapatan diprediksi stabil dibanding periode sebelumnya. "
                "Kondisi bisnis relatif konsisten dan dapat dipertahankan."
            )
                
    return Response({
        "laporan": laporan,
        "chart": chart,
        "statistik":{
            "totalPendapatan": total_pendapatan,
            "rataRata": rata_rata,
            "bulanTertinggi": bulan_tertinggi,
            "pendapatanTertinggi": pendapatan_tertinggi,
            "kategoriFavorit": kategori_favorit,
            "jumlahBookingKategori": jumlah_booking,
            "kontribusiKategori": kontribusi_kategori,
        },

        "prediksi": {
            "nominal": prediksi,
            "bulanPrediksi": bulan_prediksi,
            "trend": trend,
            "persentase": persentase,
            "metode": "Single Moving Average (3)",
            "insight": insight,
        }
    })
   
@api_view(['GET'])
def dashboard_summary(request):

    total_booking = Booking.objects.count()

    waiting_booking = Booking.objects.filter(
        payment_status="confirmed",
        booking_status="waiting"
    )

    waiting = waiting_booking.count()

    print("========== WAITING ==========")

    for b in waiting_booking:
        print(
            b.id,
            b.nama,
            b.payment_status,
            b.booking_status,
            b.date,
        )

    print("TOTAL:", waiting)

    progress = Booking.objects.filter(
        booking_status='progress'
    ).count()

    finished = Booking.objects.filter(
        booking_status='finished'
    ).count()
    
    transaksi_pending = Booking.objects.filter(
        payment_status='pending'
    ).count()

    booking_waiting = Booking.objects.filter(
        payment_status="confirmed",
        booking_status='waiting'
    ).count()

    today = date.today()

    booking_hari_ini = Booking.objects.filter(
        date=today
    ).count()

    antrian = Booking.objects.filter(
        date=today,
        payment_status='confirmed',
        booking_status='waiting'
    ).count()

    pelanggan_hari_ini = Booking.objects.filter(
        date=today
    ).count()

    pendapatan_hari_ini = 0

    booking_selesai = Booking.objects.filter(
        date=today,
        booking_status='finished'
    )

    for booking in booking_selesai:
        layanan = MenuLayanan.objects.filter(
            title=booking.package_name
        ).first()

        if layanan:
            pendapatan_hari_ini += booking.harga

    return Response({
        "booking_hari_ini": booking_hari_ini,
        "antrian": antrian,
        "pelanggan_hari_ini": pelanggan_hari_ini,
        "pendapatan_hari_ini": pendapatan_hari_ini,

        "total_booking": total_booking,
        "waiting": waiting,
        "progress": progress,
        "finished": finished,

        "booking_waiting": booking_waiting,
        "transaksi_pending": transaksi_pending,
    })

@api_view(['GET'])
def transaksi_list(request):

    bookings = Booking.objects.all().order_by("-created_at")

    result = []

    for item in bookings:

        layanan = MenuLayanan.objects.filter(
            title=item.package_name
        ).first()

        result.append({
            "id": item.id,
            "customer_id": 
                item.customer.id
                if item.customer
                else None,
            "nama": item.nama,
            "nomor_hp": item.nomor_hp,
            "package_name": item.package_name,
            "kategori": item.kategori,  
            "payment_method": item.payment_method,
            "date": str(item.date),
            "time": str(item.time),

            "bukti_pembayaran": str(item.bukti_pembayaran)
            if item.bukti_pembayaran
            else "",

            "payment_status": item.payment_status,
            "booking_status": item.booking_status,

            "harga": float(item.harga),
        })

    return Response(result)


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def menuLayanan(request, id=None):
    if request.method == 'GET':
        data = MenuLayanan.objects.all()
        serializer = LayananSerializer(data, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        serializer = LayananSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    if request.method == 'PUT':
        try:
            layanan = MenuLayanan.objects.get(id=id)
        except MenuLayanan.DoesNotExist:
            return Response({"message": "Data tidak ditemukan"}, status=404)

        serializer = LayananSerializer(layanan, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    if request.method == 'DELETE':
        try:
            layanan = MenuLayanan.objects.get(id=id)
            layanan.delete()
            return Response({"message": "Data berhasil dihapus"})
        except MenuLayanan.DoesNotExist:
            return Response({"message": "Data tidak ditemukan"}, status=404)