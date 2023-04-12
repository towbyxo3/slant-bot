import datetime


def get_todays_date():
    # day of monday of that week
    now = datetime.datetime.now()
    iso_year, iso_week, iso_day = now.isocalendar()
    monday = now - datetime.timedelta(days=iso_day - 1)
    year, month = monday.year, monday.month
    week = monday.strftime("%W")
    return str(year), str(month), str(week)


def get_todays_date_actually():
    now = datetime.datetime.now()
    year = now.year
    month = now.strftime('%m')
    week = now.strftime("%W")
    return str(year), str(month), str(week)


def get_week_dates(year, week):
    # Get the first day of the week
    first_day = datetime.datetime.strptime(f"{year}-W{week}-1", "%Y-W%U-%w")
    # Get the last day of the week
    last_day = first_day + datetime.timedelta(days=6)
    # Return the dates as strings in the desired format
    return (first_day.strftime("%d. %b %Y"), last_day.strftime("%d. %b %Y"))


def get_month_name(month):
    month_names = ["January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"]
    return month_names[int(month) - 1]


def DbYYYformat(date_str):
    # 2020-08-13 -> "13. Aug 2020"
    date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    month_name = date.strftime("%b")
    day = date.day
    return f"{day}. {month_name} {date.year}"


def get_last_7_days(date):
    # Convert the date string to a date object
    end_date = datetime.datetime.strptime(date, "%Y-%m-%d").date()

    # Initialize an empty list to store the dates
    dates = []

    # Loop through the last 7 days
    for i in range(7):
        # Subtract i days from the end date to get the current date
        current_date = end_date - datetime.timedelta(days=i)

        # Format the date as a string in the desired format
        formatted_date = current_date.strftime("%Y-%m-%d")

        # Add the date to the list
        dates.append(formatted_date)

    # Return the list of dates
    return dates


def get_dates_for_week(year, week):
    # Initialize an empty list to store the dates
    dates = []

    # Calculate the first day of the week
    first_day_of_week = datetime.date(
        year, 1, 1) + datetime.timedelta(weeks=week - 1)
    # Adjust the first day of the week to be a Monday if it's not
    if first_day_of_week.weekday() != 0:
        first_day_of_week += datetime.timedelta(
            days=7 - first_day_of_week.weekday())

    # Loop through the week
    for i in range(7):
        # Add i days to the first day of the week to get the current day
        current_day = first_day_of_week + datetime.timedelta(days=i)

        # Format the date as a string in the desired format
        formatted_date = current_day.strftime("%Y-%m-%d")

        # Add the date to the list
        dates.append(formatted_date)

    # Return the list of dates
    return dates


def get_previous_week(year, week):
    # Convert the year and week numbers to a date object
    date = datetime.datetime.strptime(f'{year}-W{week}-1', '%Y-W%U-%w')

    # Subtract one week from the date
    previous_week = date - datetime.timedelta(weeks=1)

    # Extract the year and week from the previous week date object
    previous_year = previous_week.strftime("%Y")
    previous_week = previous_week.strftime("%U")

    # Return the year and week as a tuple
    return (previous_year, previous_week)
