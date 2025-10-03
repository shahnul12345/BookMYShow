from django.contrib import admin
from .models import Movie, Theater, Screen, Show, Booking

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ("title", "release_date", "language")

@admin.register(Theater)
class TheaterAdmin(admin.ModelAdmin):
    list_display = ("name", "city")

@admin.register(Screen)
class ScreenAdmin(admin.ModelAdmin):
    list_display = ("name", "theater", "rows", "cols")
    list_filter = ("theater",)

@admin.register(Show)
class ShowAdmin(admin.ModelAdmin):
    list_display = ("movie", "screen", "start_time", "price")
    list_filter = ("screen__theater", "movie")

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "show", "seats_display", "total_price", "booked_at", "payment_done")
    readonly_fields = ("booked_at",)
