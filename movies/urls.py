from django.urls import path
from . import views

app_name = "movies"
urlpatterns = [
    path('', views.movie_list, name="movie_list"),
    path('movie/<int:pk>/', views.movie_detail, name="movie_detail"),
    path('show/<int:show_id>/seats/', views.show_seats, name="show_seats"),
    path('book/<int:show_id>/', views.create_booking, name="create_booking"),
    path('show/<int:show_id>/select/', views.show_seats_page, name="show_seats_page"),
    path('book/<int:show_id>/', views.create_booking, name="create_booking"),
    path('payment/', views.booking_payment, name="booking_payment"),
    path('booking/<int:booking_id>/success/', views.booking_success, name="booking_success"),
    path('booking/<int:booking_id>/download/', views.download_ticket, name="download_ticket"),
    path("my-bookings/", views.my_bookings, name="my_bookings"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),


]
