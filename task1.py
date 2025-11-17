import pickle
from collections import UserDict
from datetime import datetime, timedelta
import os


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field):
    def __init__(self, value):
        self.value = value

class Phone(Field):
    def __init__(self, value):
        if not isinstance(value, str):
            raise TypeError("Phone must be in a string format")
        if len(value) != 10 or not value.isdigit():
            raise ValueError("Phone must be 10 digit string format")

        self.value = value

class Birthday(Field):
    def __init__(self, value):
        try:
            date_obj = datetime.strptime(value, "%d.%m.%Y").date()
            super().__init__(date_obj)
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

class Record:
    def __init__(self, name):
        self.name = Name(name)      
        self.phones = []
        self.birthday = None

    def __str__(self):
        return f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}"

    def add_phone(self, phone_number):
        self.phones.append(Phone(phone_number))

    def remove_phone(self, phone_number):
        phone_to_remove = self.find_phone(phone_number)
        
        if phone_to_remove:
            self.phones.remove(phone_to_remove)
            return

    def edit_phone(self, old_phone, new_phone):
        phone_to_edit = self.find_phone(old_phone)

        if not phone_to_edit:
            raise ValueError(f"Phone {old_phone} not found.")
        
        new_phone_obj = Phone(new_phone)
        phone_to_edit.value = new_phone_obj.value

    def find_phone(self, phone_number):
        for phone in self.phones:
            if phone.value == phone_number:
                return phone
        return None  
    
    def add_birthday(self, birthday_date):
        self.birthday = Birthday(birthday_date)

    def __str__(self):
        birthday_str = self.birthday.value.strftime("%d.%m.%Y") if self.birthday else "N/A"
        return f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}, birthday: {birthday_str}"

class AddressBook(UserDict):

    def save_to_file(self, filename="addressbook.pkl"):
        try:
            with open(filename, "wb") as f:
                pickle.dump(self, f)
            print(f"Address book successfully saved to file: **{filename}**")
        except Exception as e:
            print(f"Error saving workbook: {e}")

    @classmethod
    def load_from_file(cls, filename="addressbook.pkl"):
        try:
            with open(filename, "rb") as f:
                book = pickle.load(f)
                print(f"Address book successfully loaded from file: **{filename}**")
                return book
        except FileNotFoundError:
            print(f"File **{filename}** not found. New address book created.")
            return cls() 
        except Exception as e:
            print(f"Error loading book ({e}). Creating a new one")
            return cls()
        
    def add_record(self, record: Record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self):
        today = datetime.today().date()
        upcoming_birthdays = []
        for record in self.data.values():
            try:
                if record.birthday is None:
                    continue
                birthday = record.birthday.value
                birthday_this_year = birthday.replace(year=today.year)
                
                if birthday_this_year < today:
                    birthday_this_year = birthday_this_year.replace(year=today.year + 1)
                    
                    days_until_birthday = (birthday_this_year - today).days
                    
                    if 0 <= days_until_birthday <= 7:
                        congratulation_date = birthday_this_year
                        
                        if congratulation_date.weekday() == 5:  # Saturday (5)
                            congratulation_date += timedelta(days=2)
                            
                        elif congratulation_date.weekday() == 6:  # Sunday (6)
                             congratulation_date += timedelta(days=1)
                            
                        upcoming_birthdays.append({
                                
                            "name": record.name.value,
                            "congratulation_date": congratulation_date.strftime("%d.%m.%Y")
                        })
        
            except ValueError as e:
                print(f"Date format error for {record.name.value}: {e}")
                continue
            except AttributeError as e:
                print(f"Attribute error for a record: {e}")
                continue
        return upcoming_birthdays


def parse_input(user_input):
    parts = user_input.strip().split()
    if not parts:
        return "", []
    cmd = parts[0].lower()
    args = parts[1:]
    return cmd, args

def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return f"Value error: {e}"
        except KeyError:
            return "Contact not found."
        except IndexError:
            return "Not enough arguments provided."
        except Exception as e:
            return f"Unexpected error: {e}"
    return inner


@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message


@input_error
def change_contact(args, book):
    if len(args) < 3:
        raise ValueError("Need: name, old_phone, new_phone")
    name, old_phone, new_phone = args
    record = book.find(name)
    if record is None:
        raise KeyError
    record.edit_phone(old_phone, new_phone)
    return "Phone updated."


@input_error
def show_phone(args, book):
    name = args[0]
    record = book.find(name)
    if record is None:
        return f"Contact '{name}' not found."
    return "; ".join(phone.value for phone in record.phones)


@input_error
def add_birthday(args, book):
    if len(args) < 2:
        raise ValueError("Give me name and birthday (DD.MM.YYYY).")
    name, birthday_str = args
    record = book.find(name)
    if record is None:
        raise KeyError("Contact not found.")
    record.add_birthday(birthday_str)
    return f"Birthday added for {name}."


@input_error
def show_all(book):
    if not book.data:
        return "No contacts."
    return "\n".join(str(record) for record in book.data.values())


@input_error
def show_birthday(args, book):
    if not args:
        raise IndexError
    name = args[0]
    record = book.find(name)
    if record is None or record.birthday is None:
        return f"No birthday set for {name}."
    return f"{name}'s birthday: {record.birthday.value.strftime('%d.%m.%Y')}"


@input_error
def birthdays(args, book):
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No birthdays in the upcoming week."
    result = []
    for item in upcoming:
        result.append(f"{item['name']} → {item['congratulation_date']}")
    return "\n".join(result)


def main():
    book = AddressBook.load_from_file()

    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            book.save_to_file() 
            print("Good bye!")
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_contact(args, book))

        elif command == "phone":
            print(show_phone(args, book))

        elif command == "all":
            print(show_all(book))

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(args, book))

        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()
        