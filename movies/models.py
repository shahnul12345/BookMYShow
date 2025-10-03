from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils import timezone
import json


User = get_user_model()

class Movie(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    duration_min = models.PositiveIntegerField(null=True, blank=True)
    poster = models.ImageField(upload_to="posters/", null=True, blank=True)
    release_date = models.DateField(null=True, blank=True)
    language = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.title

class Theater(models.Model):
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} — {self.city}"

class Screen(models.Model):
    theater = models.ForeignKey(Theater, on_delete=models.CASCADE, related_name="screens")
    name = models.CharField(max_length=100)
    rows = models.PositiveIntegerField(default=10, validators=[MinValueValidator(1)])
    cols = models.PositiveIntegerField(default=10, validators=[MinValueValidator(1)])

    def __str__(self):
        return f"{self.theater.name} / {self.name}"

class Show(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="shows")
    screen = models.ForeignKey(Screen, on_delete=models.CASCADE, related_name="shows")
    start_time = models.DateTimeField()
    price = models.DecimalField(max_digits=8, decimal_places=2, default=150.00)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_time']

    def __str__(self):
        return f"{self.movie.title} @ {self.screen} on {self.start_time}"

    def seat_map(self):
        """Return list of seat codes e.g. A1..J10 based on screen rows/cols"""
        rows = [chr(ord('A') + i) for i in range(self.screen.rows)]
        cols = range(1, self.screen.cols + 1)
        return [f"{r}{c}" for r in rows for c in cols]

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="bookings")
    show = models.ForeignKey(Show, on_delete=models.CASCADE, related_name="bookings")
    seats = models.JSONField()  # stores list of seat codes ["A1","A2"]
    total_price = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    booked_at = models.DateTimeField(auto_now_add=True)
    payment_done = models.BooleanField(default=False)
    payment_reference = models.CharField(max_length=200, blank=True)
    transaction_id = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Booking #{self.id} for {self.show} seats={self.seats}"

    def seats_display(self):
        return ", ".join(self.seats)

