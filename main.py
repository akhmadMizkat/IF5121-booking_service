import os

from flask import Flask
from flask import jsonify
from flask import request, Response

import requests

from dotenv import load_dotenv

from dataclass import Booking, User, FnB, Ticket, Schedule, Film, Studio
from repository import Database
from helper import convert_seat_to_index, serialize

load_dotenv()

booking_db = Database()

app = Flask(__name__)

@app.route("/checkout", methods=["POST"])
def checkout():
    # Construct booking
    fnbs = []
    for f in request.json["fnbs"]:
        fj = requests.get(os.getenv("DATA_SERVICE_URL")+'/fnb/'+f).json()
        print(fj)
        fnb = FnB(fj["name"], fj["price"], fj["poster"], fj["detail_info"], fj["available_stock"], fj["is_available"])
        fnbs.append(fnb)
    
    tickets = []
    sj = requests.get(os.getenv("DATA_SERVICE_URL")+'/schedule/'+str(request.json['schedule_id'])).json()
    film = Film(name=sj["film"]["name"], price=sj["film"]["price"], duration=sj["film"]["duration"], genre=sj["film"]["genre"], synopsis=sj["film"]["duration"], poster=sj["film"]["poster"])
    studio = Studio(name=sj["studio"]["name"], num_cols=sj["studio"]["num_cols"], num_rows=sj["studio"]["num_rows"])
    schedule = Schedule(id=sj["id"], film=film, time=sj["time"], studio=studio, date_start=sj["date_start"], date_end=sj["date_end"])

    for s in convert_seat_to_index(request.json["seats"]):
        ticket = Ticket(schedule=schedule, date=request.json["date"], seat_row=s[0], seat_col=s[1])
        tickets.append(ticket)

    booking = Booking(User(email=request.json["email"]), fnbs=fnbs, tickets=tickets)
    
    # store booking to db
    booking_db.data_booking.append(booking)

    # checkout booking
    booking.checkout()

    return jsonify(serialize(booking))

@app.route("/cancel/<booking_number>", methods=["POST"])
def cancel(booking_number):
    booking = None
    for b in booking_db.data_booking:
        if b.get_booking_number() == booking_number:
            booking = b
            break
    if not booking:
        return jsonify({"msg":"Booking not found"}), 404
    
    booking.cancel()
    return Response(status=204)

@app.route("/pay/<booking_number>", methods=["POST"])
def pay(booking_number):
    booking = None
    for b in booking_db.data_booking:
        if b.get_booking_number() == booking_number:
            booking = b
            break
    if not booking:
        return jsonify({"msg":"Booking not found"}), 404
    
    booking.set_status("paid")
    return Response(status=204)

@app.route("/user-booking/<email>", methods=["POST"])
def get_user_booking(email):
    bookings = []
    for b in booking_db.data_booking:
        if b.get_user().get_email() == email:
            bookings.append(b)    

    return jsonify(serialize(bookings))

if __name__ == "__main__":
    app.run(port=5004, debug=True)

# [POST] fnb/book
# body json: list of FnB names. ex: ["CocaCola", "French Fries"]

# [POST] ticket/book
# body json: schedule id, date and list of seats number. ex:
# {"schedule_id": 1, "date": "2023-11-27", "seats": ["A1", "A2"]}

# [POST] fnb/cancel
# body json: list of FnB names. ex: ["CocaCola", "French Fries"]

# [POST] ticket/cancel
# body json: schedule id, date and list of seats number. ex:
# {"schedule_id": 1, "date": "2023-11-27", "seats": ["A1", "A2"]}