from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path

# from booking.views import media_file
from django.http import HttpResponse

def tes(request):
    return HttpResponse("MEDIA OK")

def media_file(request, path):
    return HttpResponse(f"Path = {path}")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('booking.urls')),
    
    path("media-test/", tes),
    
    re_path(r"^media/(?P<path>.*)$", media_file),

]
# urlpatterns += static(
#     settings.MEDIA_URL,
#     document_root=settings.MEDIA_ROOT
# )