import matplotlib.pyplot as plt
import pandas as pd
import itertools
import matplotlib.colors as mcolors
import sys
from matplotlib.ticker import FuncFormatter
from helpers.numberformatting import abbreviate_number, abbreviate_number_no_dec
sys.path.append("helpers")


def custom_formatter(x, pos):
    """
    Returns the Y values in a readable, abbreviated form. 80000 -> 80k
    """

    # Format x as a string with one decimal place
    formatted = f"{x:.1f}"
    # Split the string into integer and decimal parts
    int_part, dec_part = formatted.split(".")
    # Remove the decimal point and trailing zeros if the decimal part is zero
    if dec_part == "0":
        formatted = int_part
    if x >= 1e6:
        # Divide x by 1 million and format as a string with one decimal place
        formatted = f"{x/1e6:.1f}"
        # Remove the decimal point and trailing zeros if x is an integer
        if x == int(x):
            formatted = formatted.rstrip("0").rstrip(".")
        return f"{formatted}M"
    elif x >= 1e3:
        # Divide x by 1 thousand and format as a string with one decimal place
        formatted = f"{x/1e3:.1f}"
        # Remove the decimal point and trailing zeros if x is an integer
        if x == int(x):
            formatted = formatted.rstrip("0").rstrip(".")
        return f"{formatted}k"
    else:
        return formatted


def create_chart_weekday(database, id, year, server=False):
    """
    Creates a bar chart displaying the message for all 7 weekdays

    database: database from which we fetch the data
    id: member id
    year: year
    server: wheither the chart is for the server
    """

    if not server:
        decimal = True
        query = """
                SELECT DATETIME(date) as datetime
                FROM B40
                WHERE STRFTIME('%Y', date) = '{}' AND authorID = '{}'
            """.format(year, id)
    else:
        decimal = False
        query = """
                SELECT DATETIME(date) as datetime
                FROM B40
                WHERE STRFTIME('%Y', date) = '{}'
            """.format(year)


    # Get the data from the sqlite3 database and put them in a DataFrame
    data = pd.read_sql_query(query, database)
    # extract datetime object from datetime column of the database
    data['datetime'] = pd.to_datetime(data['datetime'])
    data['weekday'] = data['datetime'].dt.weekday

    # Create a DataFrame with all 24 hours
    hours = range(0, 7)
    all_combinations = pd.DataFrame(list(itertools.product(hours)), columns=['weekday'])

    # create counts column which is the sum of the grouped hour sets
    grouped_data = data.groupby(['weekday']).size().reset_index(name='counts')
    all_combinations = all_combinations.merge(grouped_data, how='left', on=['weekday'])
    all_combinations = all_combinations.fillna(0)  # no issues with transparent fields

    # get most active hour
    highest_count_weekday = all_combinations.loc[all_combinations['counts'].idxmax()]['weekday']

    # heatmap_data = all_combinations.drop(columns='weekday')  # index == hour column so we can get rid of it
    # switch position of count  and hour so we have hours on x axis and count on y axis
    # heatmap_data = heatmap_data.transpose()

    # create a DataFrame from the data
    df = all_combinations[::-1]
    highest_value = df['counts'].max()

    custom_cmap = mcolors.LinearSegmentedColormap.from_list("custom", ["#303434", "#1f0073"])

    # Normalize the data to be used with the colormap
    norm = mcolors.Normalize(vmin=df['counts'].min(), vmax=df['counts'].max())

    # Use the custom colormap to color the data points
    colors = custom_cmap(norm(df['counts']))
    # create the bar chart
    ax = df.plot.barh(
        y='counts',
        x='weekday',
        rot=0,
        linewidth=1,
        color=colors,
        edgecolor='white'
    )

    # draw the values (msg count) on top of the respective bars
    gap_to_chart = highest_value * 0.01
    for i, value in enumerate(df['counts']):
        if value > (highest_value / 10):
            ax.text(
                value +
                gap_to_chart, i, abbreviate_number(value) if decimal else abbreviate_number_no_dec(value),
                ha='left',
                va='center',
                color='white',
                fontsize=16
            )

    # remove the x-axis tick labels and x-axis label
    weekdays_name = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']
    plt.yticks(ticks=range(7), labels=weekdays_name[::-1], fontweight='bold', fontsize=15)
    plt.xticks(fontweight='bold', fontsize=15)
    plt.ylabel('')

    plt.tight_layout()
    plt.gca().tick_params(axis='both', which='both', colors='white', )
    plt.grid(True, axis='x', alpha=0.1)
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['bottom'].set_visible(True)
    plt.gca().spines['left'].set_visible(True)
    plt.gca().spines['bottom'].set_edgecolor('white')
    plt.gca().spines['left'].set_edgecolor('white')
    plt.legend('', frameon=False)
    xaxis = plt.gca().xaxis
    xaxis.set_major_formatter(FuncFormatter(custom_formatter))
    fig = plt.gcf()
    fig.set_size_inches(9, 5)
    path = f'rewind_images/{"server" if server else "user"}/chart_weekday.png'
    fig.savefig(
        path,
        dpi=300,
        transparent=True,
        bbox_inches='tight'
    )
    plt.clf()
    plt.close()

    return highest_count_weekday


def create_chart_month(database, id, year, server=False):
    """
    Creates a bar chart displaying the message for all 12 months in a year

    database: database from which we fetch the data
    id: member id
    year: year
    server: wheither the chart is of the server
    """

    if not server:
        decimal = True
        query = """
                    SELECT STRFTIME('%m', Date) as month, SUM(Msgs) as msgs
                    FROM userchat
                    WHERE id = '{}'AND STRFTIME('%Y', date) = '{}'
                    GROUP BY STRFTIME('%Y-%m', Date)
                """.format(id, year)
    else:
        decimal = False
        query = """
                    SELECT STRFTIME('%m', Date) as month, SUM(Msgs) as msgs
                    FROM userchat
                    WHERE STRFTIME('%Y', date) = '{}'
                    GROUP BY STRFTIME('%Y-%m', Date)
                """.format(year)

    # Get the data from the sqlite3 database and put them in a DataFrame
    data = pd.read_sql_query(query, database)

    data['month'] = data['month'].astype('int')

    month = range(1, 13)
    df = pd.DataFrame(list(itertools.product(month)), columns=['month'])

    df = df.merge(data, how='left', on=['month'])
    df = df.fillna(0)  # no issues with transparent fields

    highest_msgs_month = df.loc[df['msgs'].idxmax()]['month']
    highest_value = df['msgs'].max()
    # average_msgs = df['msgs'].sum() / 12

    custom_cmap = mcolors.LinearSegmentedColormap.from_list("custom", ["#303434", "#ff0000"])

    # Normalize the data to be used with the colormap
    norm = mcolors.Normalize(vmin=df['msgs'].min(), vmax=df['msgs'].max())

    # Use the custom colormap to color the data points
    colors = custom_cmap(norm(df['msgs']))
    # create the bar chart
    ax = df.plot.bar(
        x='month',
        y='msgs',
        rot=0,
        linewidth=1,
        color=colors,
        edgecolor='white'
    )

    # plt.axhline(average_msgs, color='r', linestyle='--', alpha=0.3)

    gap_to_chart = highest_value * 0.01
    for i, value in enumerate(df['msgs']):
        ax.text(
            i, value + gap_to_chart, abbreviate_number(value) if decimal else abbreviate_number_no_dec(value),
            ha='center',
            va='bottom',
            color='white',
            fontsize=16
        )

    # remove the x-axis tick labels and x-axis label
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    plt.xticks(ticks=range(12), labels=month_names, fontweight='bold', fontsize=15)
    plt.yticks(fontweight='bold', fontsize=15)
    plt.xlim(-0.7)
    plt.xlabel('')
    plt.tight_layout()
    plt.gca().tick_params(axis='both', which='both', colors='white', )
    plt.grid(True, axis='y', alpha=0.1)
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['bottom'].set_visible(True)
    plt.gca().spines['left'].set_visible(True)
    plt.gca().spines['bottom'].set_edgecolor('white')
    plt.gca().spines['left'].set_edgecolor('white')
    plt.legend('', frameon=False)
    xaxis = plt.gca().yaxis
    xaxis.set_major_formatter(FuncFormatter(custom_formatter))
    fig = plt.gcf()
    fig.set_size_inches(9, 5)
    path = f'rewind_images/{"server" if server else "user"}/chart_month.png'
    fig.savefig(path, dpi=300,
                transparent=True, bbox_inches='tight')
    plt.clf()
    plt.close('all')

    return int(highest_msgs_month)
