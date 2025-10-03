import uuid

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.timezone import now
from pyexpat.errors import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages

from .forms import UserRegisterForm
from .models import Movie, Show, Booking, User
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST

from decimal import Decimal
from django.utils import timezone
import json
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
import qrcode
from io import BytesIO
from base64 import b64encode


def movie_list(request):
    movies = Movie.objects.all()
    return render(request, "movies/movie_list.html", {"movies": movies})

def movie_detail(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    shows = movie.shows.filter(start_time__gte=timezone.now()).select_related('screen__theater')
    return render(request, "movies/movie_detail.html", {"movie": movie, "shows": shows})

def show_seats(request, show_id):
    show = get_object_or_404(Show, pk=show_id)
    # compute already booked seats
    booked = Booking.objects.filter(show=show).values_list("seats", flat=True)
    taken = set()
    for s in booked:
        # s is a list stored in JSONField
        if isinstance(s, list):
            taken.update(s)
        else:
            try:
                taken.update(json.loads(s))
            except:
                pass
    all_seats = show.seat_map()
    available = [seat for seat in all_seats if seat not in taken]
    return JsonResponse({"taken": list(taken), "available": available, "rows": show.screen.rows, "cols": show.screen.cols})




@login_required
def create_booking(request, show_id):
    show = get_object_or_404(Show, pk=show_id)
    seats = request.POST.getlist("seats[]") or request.POST.getlist("seats")
    if not seats:
        return HttpResponseBadRequest("No seats selected.")
    # re-check seat availability server-side
    booked = Booking.objects.filter(show=show).values_list("seats", flat=True)
    taken = set()
    for s in booked:
        if isinstance(s, list):
            taken.update(s)
        else:
            try:
                taken.update(json.loads(s))
            except:
                pass
    conflict = [s for s in seats if s in taken]
    if conflict:
        return JsonResponse({"error": "Seats already taken", "conflict": conflict}, status=409)

    total_price = Decimal(len(seats)) * show.price
    booking = Booking.objects.create(user=request.user, show=show, seats=seats, total_price=total_price)
    # TODO: integrate payment gateway & set booking.payment_done accordingly.
    return JsonResponse({"success": True, "booking_id": booking.id, "total_price": str(total_price)})


def show_seats_page(request, show_id):
    show = get_object_or_404(Show, pk=show_id)
    return render(request, "movies/show_seats.html", {"show": show})


@login_required(login_url='movies:login')
def create_booking(request, show_id):
    show = get_object_or_404(Show, pk=show_id)
    seats = request.GET.get("seats", "")
    seat_list = seats.split(",") if seats else []

    price_per_seat = 110
    total_price = len(seat_list) * price_per_seat

    if request.method == "POST":
        # ✅ Instead of saving now, redirect to payment page
        request.session["booking_data"] = {
            "show_id": show.id,
            "seats": seat_list,
            "total_price": total_price,
        }
        return redirect("movies:booking_payment")

    return render(request, "movies/booking_confirm.html", {
        "show": show,
        "seats": seat_list,
        "total_price": total_price,
    })

@login_required
def booking_payment(request):
    data = request.session.get("booking_data")
    if not data:
        return redirect("movies:movie_list")

    show = get_object_or_404(Show, pk=data["show_id"])

    if request.method == "POST":
        # ✅ Generate transaction ID
        txn_id = "TXN" + now().strftime("%Y%m%d%H%M%S") + uuid.uuid4().hex[:6].upper()

        booking = Booking.objects.create(
            user=request.user,
            show=show,
            seats=data["seats"],
            total_price=data["total_price"],
            transaction_id=txn_id,  # ✅ Save it
        )
        del request.session["booking_data"]

        return redirect("movies:booking_success", booking_id=booking.id)

    return render(request, "movies/booking_payment.html", {
        "show": show,
        "seats": data["seats"],
        "total_price": data["total_price"],
    })


@login_required
def booking_success(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)
    return render(request, "movies/booking_success.html", {"booking": booking})



@login_required
def download_ticket(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)

    # QR code: encode transaction ID (you can include more info if needed)
    qr_data = f"TransactionID:{booking.transaction_id}\nBookingID:{booking.id}"
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = b64encode(buffer.getvalue()).decode()  # encode as base64 for HTML

    # Render HTML template
    html_content = render_to_string("movies/ticket.html", {
        "booking": booking,
        "qr_base64": qr_base64
    })

    # Create PDF response
    response = HttpResponse(content_type="application/pdf")
    response['Content-Disposition'] = f'attachment; filename="ticket_{booking.id}.pdf"'

    pisa_status = pisa.CreatePDF(html_content, dest=response)
    if pisa_status.err:
        return HttpResponse("Error generating PDF")

    return response


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).select_related("show__movie")
    return render(request, "movies/my_bookings.html", {"bookings": bookings})


def register_view(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful.")
            return redirect("movies:movie_list")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserRegisterForm()

    return render(request, "movies/register.html", {"form": form})
# Login
def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "Login successful.")
            return redirect("movies:movie_list")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, "movies/login.html", {"form": form})

# Logout
@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "Logged out successfully.")
    return redirect("movies:movie_list")


