import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np
import itertools
import datetime
import matplotlib.colors as mcolors
import sys
from helpers.numberformatting import abbreviate_number, abbreviate_number_no_dec
from helpers.dateformatting import get_month_name

sys.path.append("helpers")


def cmap_blue():
    """
    Returns cmap colours for daytime and daytime/weekday heatmap
    """
    return mcolors.LinearSegmentedColormap.from_list("custom", ["#303434", "#1f0073"])


def cmap_red():
    """
    Returns cmap colours for calendar and months/year heatmap
    """
    return mcolors.LinearSegmentedColormap.from_list("custom", ["#303434", "#ff0000"])


def create_heatmap_hour_of_day(database, id, year, server=False):
    """
    Creates and stores a heatmap stripe with 24 hrs with messages count on
    every day cell. Cells are coloured based on the value

    database: database from which we extract the data
    id: member id
    year: year
    server: wheither we create the heatmap for a server
    """

    # assigns the query variable to the server or user specific query
    if not server:
        query = """
                    SELECT DATETIME(date) as datetime
                    FROM B40
                    WHERE STRFTIME('%Y', date) = '{}' AND authorID = '{}'
                    """.format(year, id)
    else:
        query = """
                SELECT DATETIME(date) as datetime
                FROM B40
                WHERE STRFTIME('%Y', date) = '{}'
                """.format(year)

    # Get the data from the sqlite3 database and put them in a DataFrame
    data = pd.read_sql_query(query, database)
    # extract datetime object from datetime column of the database
    data['datetime'] = pd.to_datetime(data['datetime'])
    data['hour'] = data['datetime'].dt.hour

    # Create a DataFrame with all 24 hours
    hours = range(0, 24)
    all_combinations = pd.DataFrame(list(itertools.product(hours)), columns=['hour'])

    # create counts column which is the sum of the grouped hour sets
    grouped_data = data.groupby(['hour']).size().reset_index(name='counts')
    all_combinations = all_combinations.merge(grouped_data, how='left', on=['hour'])
    all_combinations = all_combinations.fillna(np.nan)  # no issues with transparent fields

    # get most active hour
    #highest_count_hour = all_combinations.loc[all_combinations['counts'].idxmax()]['hour']
    highest_count_hour = all_combinations[['counts']].idxmax()

    heatmap_data = all_combinations.drop(columns='hour')  # index == hour column so we can get rid of it
    # switch position of count  and hour so we have hours on x axis and count on y axis
    heatmap_data = heatmap_data.transpose()

    # create heatmap
    # the numbers get too big
    sns.heatmap(
        heatmap_data,
        annot=True, fmt=".0f",
        linewidths=.5,
        linecolor='white',
        cmap=cmap_blue(),
        annot_kws={"fontsize": 9},
        cbar=False
    )

    # get axis instance
    ax = plt.gca()
    # we modify the numbers with 2 different works that make the text
    # readable with bigger numbers
    for text in ax.texts:
        if int(text.get_text()) > 10000:
            text.set_text(abbreviate_number_no_dec(int(text.get_text())))
        else:
            text.set_text(abbreviate_number(int(text.get_text())))

    # line on the heatmap indicating before moon and after moon
    plt.axvline(x=12, ymin=0, ymax=1, color='black', linewidth=1.5)

    # get x ticks
    hours = [(datetime.time(i).strftime('%I')).lstrip('0')if i != 12 else "PM" for i in range(24)]
    hours[0] = "AM"

    plt.yticks([])
    plt.xticks(ticks=range(24), labels=hours, rotation=0, color='white', fontweight='bold')
    plt.gca().tick_params(axis='both', which='both', colors='white')

    plt.xlabel('')
    plt.ylabel('')
    fig = plt.gcf()
    # fig.set_size_inches(8, 0.5)
    fig.set_size_inches(10, 0.7)
    path = f'rewind_images/{"server" if server else "user"}/heatmap_daytime.png'
    fig.savefig(path, dpi=300, transparent=True, bbox_inches='tight')
    plt.clf()
    plt.close()

    return int(highest_count_hour)


def create_heatmap_hour_of_weekday(database, id, year, server=False):
    """
    Creates and stores a weekday(y) and hour(x) heatmap messages count on
    the top 3 hours. Cells are coloured based on the value

    database: database from which we extract the data
    id: member id
    year: year
    server: wheither we create the heatmap for a server
    """
    if not server:
        query = """
                    SELECT DATETIME(date) as datetime
                    FROM B40
                    WHERE STRFTIME('%Y', date) = '{}' AND authorID = '{}'
                """.format(year, id)
    else:
        query = """
                    SELECT DATETIME(date) as datetime
                    FROM B40
                    WHERE STRFTIME('%Y', date) = '{}'
                """.format(year)

    # Get the data
    data = pd.read_sql_query(query, database)
    data['datetime'] = pd.to_datetime(data['datetime'])
    data['hour'] = data['datetime'].dt.hour
    data['weekday'] = data['datetime'].dt.weekday
    # data['weekday'] = np.where(data['weekday'] == 0, 7, data['weekday'])

    # Create a DataFrame with all possible combinations of weekdays and hours
    weekdays = range(7)
    hours = range(0, 24)
    all_combinations = pd.DataFrame(list(itertools.product(weekdays, hours)), columns=['weekday', 'hour'])

    grouped_data = data.groupby(['weekday', 'hour']).size().reset_index(name='counts')

    all_combinations = all_combinations.merge(grouped_data, how='left', on=['weekday', 'hour'])
    all_combinations['counts'] = all_combinations['counts'].fillna(np.nan)

    heatmap_data = all_combinations.pivot("weekday", "hour", "counts")

    sns.heatmap(
        heatmap_data,
        annot=True,
        fmt=".0f",
        linewidths=.5,
        linecolor='grey',
        cmap=cmap_blue(),
        annot_kws={"fontsize": 9},
        cbar=False
    )

    # list of top 10 hours -> these will be the only cells with annotation
    top_3_counts = list(heatmap_data.stack().sort_values(ascending=False).head(3))
    top_1_counts = top_3_counts[0]

    ax = plt.gca()
    # show the annotation for only the top 10 values
    for text in ax.texts:
        value = int(text.get_text())
        if value in top_3_counts:
            text.set_text(abbreviate_number(int(text.get_text())))
            if value == top_1_counts:
                # store the x, y coordinates of the top 1 hour which at the same
                # time represent the top1 hour and weekday as integer
                top1_hour, top1_weekday = text.get_position()
                top1_hour = int(float(top1_hour) - 0.5)
                top1_weekday = int(float(top1_weekday) - 0.5)
                # ax.text(x, y-0.2, '#1', color='white', ha='center')
        else:
            text.set_alpha(0)

    weekday_labels = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
    # x ticks
    hours = [(datetime.time(i).strftime('%I')).lstrip('0') if i != 12 else "PM" for i in range(24)]
    hours[0] = "AM"
    plt.axvline(x=12, ymin=0, ymax=1, color='black', linewidth=1.5)

    plt.yticks(
        ticks=np.arange(heatmap_data.shape[0]) + 0.5,
        fontsize=10,
        labels=weekday_labels,
        rotation=0,
        color='white',
        fontweight='bold'
    )
    plt.xticks(
        ticks=range(24),
        labels=hours,
        rotation=0,
        color='white',
        fontweight='bold'
    )

    plt.gca().tick_params(axis='both', which='both', colors='white')

    plt.xlabel('')
    plt.ylabel('')

    fig = plt.gcf()
    fig.set_size_inches(10, 3)
    path = f'rewind_images/{"server" if server else "user"}/heatmap_weekday_hour.png'
    fig.savefig(path, dpi=300, transparent=True, bbox_inches='tight')
    plt.clf()
    plt.close()

    return top1_hour, top1_weekday, top_1_counts


def create_heatmap_calendar(database, id, year, server=False):
    """
    Creates and stores heatmap calendar (x: month, y: day of the month) heatmap
    with messages count for every day. Cells are coloured based on the value

    database: database from which we extract the data
    id: member id
    year: year
    server: wheither we create the heatmap for a server
    """
    if not server:
        query = """
                    SELECT DATETIME(date) as datetime
                    FROM B40
                    WHERE authorid = '{}'AND STRFTIME('%Y', date) = '{}'
                """.format(id, year)
    else:
        query = """
                    SELECT DATETIME(date) as datetime
                    FROM B40
                    WHERE STRFTIME('%Y', date) = '{}'
                """.format(year)

    # create all combinations of months and days, which will be filled later on
    df = pd.DataFrame(columns=range(1, 13), index=range(1, 32))
    df.fillna(np.nan, inplace=True)
    data = pd.read_sql_query(query, database)
    data['datetime'] = pd.to_datetime(data['datetime'])
    data['month'] = data['datetime'].dt.month
    data['day'] = data['datetime'].dt.day

    # Group the data by month and day
    grouped_data = data.groupby(['day', 'month']).size().reset_index(name='counts')

    # Fill the dataframe with 0

    # Add the grouped data to the existing dataframe
    df.update(grouped_data.pivot(index='day', columns='month', values='counts'))

    sns.heatmap(
        df,
        annot=True,
        fmt=".0f",
        linewidths=.5,
        linecolor='lightgrey',
        cmap=cmap_red(),
        annot_kws={"fontsize": 9, "fontweight": 'bold'},
        cbar=False,
        xticklabels=[get_month_name(i + 1)[:3] for i in range(12)]
    )

    ax = plt.gca()
    if server:
        for text in ax.texts:
            text.set_text(abbreviate_number(int(text.get_text())))
    else:
        for text in ax.texts:
            text.set_text((text.get_text()))

    plt.yticks(rotation=0, color='white', fontweight='bold', fontsize=14)
    plt.xticks(rotation=0, color='white', fontweight='bold', fontsize=14)
    plt.gca().tick_params(axis='both', which='both', colors='white')
    plt.xlabel('')
    plt.ylabel('')
    # plt.title(str(year), color='white', fontsize=20)

    fig = plt.gcf()
    fig.set_size_inches(10, 7)
    path = f'rewind_images/{"server" if server else "user"}/heatmap_calendar_year.png'
    fig.savefig(path, dpi=300, transparent=True, bbox_inches='tight')
    plt.clf()
    plt.close()


def create_heatmap_years_months(database, id, year, server=False):
    """
    Creates and stores a year(y) and month(x) heatmap with messages count on
    for every month. Cells are coloured based on the value. The given year
    is marked with outlines to make the comparison easier

    database: database from which we extract the data
    id: member id
    year: year
    server: wheither we create the heatmap for a server
    """
    if not server:
        query = """
                    SELECT DATETIME(date) as datetime
                    FROM B40
                    WHERE authorid = '{}'
                """.format(id)
    else:
        query = """
                    SELECT DATETIME(date) as datetime
                    FROM B40
                """
    # Get the data
    data = pd.read_sql_query(query, database)
    data['datetime'] = pd.to_datetime(data['datetime'])
    data['month'] = data['datetime'].dt.month
    data['year'] = data['datetime'].dt.year

    # Grouping the data by month and year
    grouped_data = data.groupby(['year', 'month']).size().reset_index(name='counts')

    # Create a DataFrame with all possible combinations of year and months
    years = [2023 - i for i in range(4)]
    months = range(1, 13)
    all_combinations = pd.DataFrame(list(itertools.product(years, months)), columns=['year', 'month'])

    # Merge the grouped data with the all_combinations dataframe
    all_combinations = all_combinations.merge(grouped_data, how='left', on=['year', 'month'])
    all_combinations['counts'] = all_combinations['counts'].fillna(np.nan)

    # calculates the y position of the horizontal lines which indicate the
    # considered year
    y_marks = [abs(2023 - int(year) - i) for i in range(len(years) - 1, len(years) + 1)]
    # draw the axhlines on the inner side of the row
    y_marks[0] = y_marks[0] + 0.03
    y_marks[1] = y_marks[1] - 0.03
    # draw white lines above and below the considered year row
    for y in y_marks:
        plt.axhline(y=y, xmin=0, color='white', linewidth=2.5)

    heatmap_data = all_combinations.pivot("year", "month", "counts")

    sns.heatmap(
        heatmap_data,
        annot=True,
        fmt=".0f",
        linewidths=.5,
        cmap=cmap_red(),
        annot_kws={"fontsize": 11, "fontweight": 'bold'},
        xticklabels=[get_month_name(i + 1)[:3] for i in range(12)],
        linecolor='grey',
        cbar=False
    )

    ax = plt.gca()
    for text in ax.texts:
        try:
            text.set_text(abbreviate_number(int(text.get_text())))
        except:
            pass

    plt.yticks(rotation=0, color='white', fontweight='bold', fontsize=14)
    plt.xticks(rotation=0, color='white', fontweight='bold', fontsize=14)
    plt.gca().tick_params(axis='both', which='both', colors='white')
    plt.xlabel('')
    plt.ylabel('')

    fig = plt.gcf()
    fig.set_size_inches(10, 3)
    path = f'rewind_images/{"server" if server else "user"}/heatmap_years_months.png'
    fig.savefig(path, dpi=300, transparent=True, bbox_inches='tight')
    plt.clf()



""""

The following code is significantly faster because it takes the data from an
already grouped dataset but for now, the code stays unchanged

query = ""
        SELECT DATETIME(date) as datetime, SUM(Msgs) as counts
        FROM serverchat
        GROUP BY STRFTIME("%Y-%m", date)
        ""


data = pd.read_sql_query(query, database)


data['datetime'] = pd.to_datetime(data['datetime'])
data['year'] = data['datetime'].dt.year
data['month'] = data['datetime'].dt.month


data.drop(columns = ['datetime'])




# Create a DataFrame with all possible combinations of year and months
years = [2023 - i for i in range(4)]
months = range(1, 13)
all_combinations = pd.DataFrame(list(itertools.product(years, months)), columns=['year', 'month'])

# Merge the grouped data with the all_combinations dataframe
all_combinations = all_combinations.merge(data, how='left', on=['year', 'month'])
all_combinations['counts'] = all_combinations['counts'].fillna(np.nan)

heatmap_data = all_combinations.pivot("year", "month", "counts")

"""
