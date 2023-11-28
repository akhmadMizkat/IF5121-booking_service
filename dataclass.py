from typing import List, Literal
import string
import random
from abc import ABC, abstractmethod
from datetime import date, timedelta
import requests
import os

class Account:

    def __init__(self) -> None:
        self._email = None 
        self._password = None
        self._database = None
    
    @property
    def database(self):
        return self._database
    
    @database.setter
    def database(self, selection_database):
        self._database = selection_database
    
    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, user_email):
        self._email = user_email

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, user_password):
        self._password = user_password
      
    def login(self):
        pass

    def reset_password(self):
        pass


class User(Account):

    def __init__(self, email)-> None:
        super().__init__()
        self.email = email

class Item(object):
    def __init__(self, name, price):
        self.name = name
        self.price = price
    def get_name(self):
        return self.name
    def get_price(self):
        return self.price
    def set_name(self, name):
        self.name = name
    def set_price(self, price):
        self.price = price

class Ticket(Item):
    def __init__(self, schedule, date, seat_row, seat_col):
        self.schedule = schedule
        self.date = date
        self.seat_row = seat_row
        self.seat_col = seat_col
        self.set_price(schedule.get_film().get_price())

    def get_schedule(self):
        return self.schedule
    def get_date(self):
        return self.date
    def set_schedule(self, schedule):
        self.schedule = schedule
    def set_date(self,date):
        self.date = date
    def cancel(self):
        self.schedule.untake_seat(self.date, self.seat_row, self.seat_col)
    def book(self):
        self.status = "booked"
    def buy(self):
        self.status = "bought"
    def invalidate(self):
        if self.status != "bought":
            raise Exception("Only bought ticket can be invalidated")
        self.set_status("invalidated")
    def get_seat(self):
        return self.matrix_index_to_seat_number(self.seat_row, self.seat_col)
    
    def matrix_index_to_seat_number(self, row_index, col_index):
        # Convert the column index to a letter representing the row
        row_letter = chr(ord('A') + row_index)
        
        seat_number = f"{row_letter}{col_index+1}"
        
        return seat_number

class FnB(Item):
    def __init__(self, name, price, poster, detail_info, available_stock, is_available=True):
        Item.__init__(self,name, price)
        self.poster = poster
        self.detail_info = detail_info
        self.is_available = is_available
        self.available_stock = available_stock
    def __str__(self):
        return f'Nama Makanan / Minuman : {self.name}\nDetail Info : {self.detail_info}\nKetersediaan : {self.available_stock}'
    def get_poster(self):
        return self.poster
    def get_detail_info(self):
        return self.detail_info
    def get_available_stock(self):
        return self.available_stock
    def set_poster(self, poster):
        self.poster = poster
    def set_detail_info(self, detail_info):
        self.detail_info = detail_info
    def set_stock(self, available_stock):
        self.available_stock = available_stock
    def set_available(self, is_available):
        self.is_available= is_available
    def cancel(self):
        self.set_stock(self.get_available_stock()+1)
    def book(self):
        if (self.get_available_stock()-1) < 0:
            raise Exception(f"Stock {self.get_name} sudah habis")
        self.set_stock(self.get_available_stock()-1)


class IBooking(ABC):

    @abstractmethod
    def checkout(self) -> None:
        pass

    @abstractmethod
    def cancel(self) -> None:
        pass

class Booking(IBooking):
    def __init__(self, user: User, fnbs: List[FnB], tickets: List[Ticket]) -> None:
        super().__init__()
        self.set_user(user)
        self.set_fnbs(fnbs)
        self.set_tickets(tickets)
        self.set_status("open") # open, waiting for payment, canceled, paid
        self.set_total_price(0)
        self.set_booking_number(self.generate_booking_number())
    
    def set_user(self, user: User):
        self.user = user
    
    def get_user(self) -> User:
        return self.user
    
    def set_status(self, status: Literal['open', 'waiting for payment', 'canceled', 'paid']):
        self.status = status
    
    def get_status(self) -> str:
        return self.status
    
    def set_tickets(self, tickets: List[Ticket]):
        self.tickets = tickets
    
    def get_tickets(self) -> List[Ticket]:
        return self.tickets

    def set_fnbs(self, fnbs: List[FnB]):
        self.fnbs = fnbs
    
    def get_fnbs(self) -> List[FnB]:
        return self.fnbs
    
    def set_total_price(self, total_price):
        self.total_price = total_price
    
    def get_total_price(self):
        return self.total_price
    
    def set_booking_number(self, booking_number):
        self.booking_number = booking_number
    
    def get_booking_number(self):
        return self.booking_number

    def generate_booking_number(self):
        prefix = "BK"
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        booking_number = prefix + random_part
        return booking_number
    
    def checkout(self) -> None:
        # kurangi stock FnB yang dibeli
        requests.post(os.getenv('DATA_SERVICE_URL')+'/fnb/book', json={"fnbs":[str(fnb.get_name()) for fnb in self.fnbs]})
        for f in self.fnbs:
            f.book()
            self.total_price += f.price
        
        requests.post(os.getenv('DATA_SERVICE_URL')+'/ticket/book/'+self.tickets[0].get_schedule().id+'/'+self.tickets[0].get_date(), json={"seats":[ticket.get_seat() for ticket in self.tickets]})
        for t in self.tickets:
            t.book()
            self.total_price += t.get_price()
        
        self.set_status("waiting for payment")
    
    def cancel(self):
        requests.post(os.getenv('DATA_SERVICE_URL')+'/fnb/cancel', json={"fnbs":[str(fnb.get_name()) for fnb in self.fnbs]})
        for f in self.fnbs:
            f.cancel()

        requests.post(os.getenv('DATA_SERVICE_URL')+'/ticket/cancel/'+self.tickets[0].get_schedule().id+'/'+self.tickets[0].get_date(), json={"seats":[ticket.get_seat() for ticket in self.tickets]})
        for t in self.tickets:
            t.cancel()
        
        self.status = "canceled"
    
    def __str__(self):
        fnb_list = ', '.join([str(fnb.get_name()) for fnb in self.fnbs])
        seat_list = ', '.join([ticket.get_seat() for ticket in self.tickets])

        return (
            f"Booking Number: {self.booking_number}\n"
            f"Film Name: {self.tickets[0].get_schedule().get_film().get_name()}\n"
            f"Studio: {self.tickets[0].get_schedule().get_studio().get_name()}\n"
            f"Seats: {seat_list}\n"
            f"FnBs: {fnb_list if fnb_list else 'No FnBs'}, \n"
            f"Status: {self.status}\n"
            f"Total Price: {self.total_price}\n\n"
        )

    def serialize(self):
        return dict(
            booking_number=self.booking_number,
            date=self.tickets[0].get_date(),
            film_name=self.tickets[0].get_schedule().get_film().get_name(),
            studio_name=self.tickets[0].get_schedule().get_studio().get_name(),
            status=self.status,
            total_price=self.total_price,
            fnbs=[str(fnb.get_name()) for fnb in self.fnbs],
            tickets=[ticket.get_seat() for ticket in self.tickets]
        )

class Film(Item):
    def __init__(self,name, price, synopsis, genre, duration, poster):
        Item.__init__(self, name, price)
        self.synopsis = synopsis
        self.genre = genre
        self.duration = duration
        self.poster = poster
    def __str__(self) -> str:
        return f"Film : {self.name}\nHarga: {self.price}\nGenre : {self.genre}\nDurasi: {self.duration} menit\nSinopsis: {self.synopsis}"
    def get_synopsis(self):
        return self.synopsis
    def get_genre(self):
        return self.genre
    def get_duration(self):
        return self.duration
    def get_poster(self):
        return self.poster
    def set_synopsis(self, synopsis):
        self.synopsis = synopsis
    def set_genre(self, genre):
        self.genre = genre
    def set_duration(self, duration):
        self.duration = duration
    def set_poster(self, poster):
        self.poster = poster

class Studio(object):
    def __init__(self, name, num_rows, num_cols):
        self.name = name
        self.num_rows = num_rows
        self.num_cols = num_cols
    def get_name(self):
        return self.name
    def get_num_rows(self):
        return self.num_rows
    def get_num_cols(self):
        return self.num_cols
    def set_name(self, name):
        self.name = name
    def set_num_rows(self, num_rows):
        self.name = num_rows
    def set_num_cols(self, num_cols):
        self.name = num_cols
    

class Schedule(object):
    def __init__(self, id: str, film: Film, studio: Studio, time: str, date_start: date, date_end: date):
        self.id = id
        self.film = film
        self.studio = studio
        self.time = time
        self.date_start = date_start
        self.date_end = date_end
        self.mat_seat = {}

    def __str__(self) -> str:
        return f'{self.film.__str__()}'
    def get_id(self):
        return self.id
    def get_film(self):
        return self.film
    def get_studio(self):
        return self.studio
    def get_time(self):
        return self.time
    def get_date_start(self):
        return self.date_start
    def get_date_end(self):
        return self.date_end
    def set_film(self, film):
        self.film = film
    def set_studio(self, studio):
        self.studio = studio
    def set_time(self, time):
        self.time = time
    def set_date_start(self, date_start):
        self.date_start = date_start
    def set_date_end(self, date_end):
        self.date_end = date_end
    def get_available_seat(self):
        return self.mat_seat
    def take_seat(self, date, row, col) -> Ticket:
        if not self.mat_seat[date][row][col]:
            raise Exception("Seat is currently unavailable")
        self.mat_seat[date][row][col] = False
        return Ticket(self, date, row, col)

    def untake_seat(self, date, row, col):
        pass
    
    def show_seats(self, date):
        try :
            seats = self.mat_seat[date]
            print("Seat Availability:")
            print("Row/Col", end='\t')
            for col in range(len(seats[0])):
                print(col+1, end='\t')
            print()
            for i, row in enumerate(seats):
                row_label = string.ascii_uppercase[i]  # Convert numeric row index to alphabet
                print(f"Row {row_label}", end='\t')
                for seat in row:
                    if seat:  # If the seat is available (True)
                        print("◯", end='\t')  # Circle symbol for available seat
                    else:
                        print("⨉", end='\t')  # X symbol for occupied seat
                print()
        except KeyError as e :
            raise KeyError(e)
    
    def serialize(self):
        return dict(
            id=self.id,
            film=self.film.serialize(),
            studio=self.studio.serialize(),
            time=self.time,
            date_start=self.date_start.strftime('%Y-%m-%d'),
            date_end=self.date_end.strftime('%Y-%m-%d'),
            mat_seat=self.mat_seat,
        )