#!/usr/bin/python3

# Ref: https://srome.github.io/Parsing-HTML-Tables-in-Python-with-BeautifulSoup-and-pandas/

from __future__ import absolute_import, division

import argparse
import datetime
import sys

from bs4 import BeautifulSoup, NavigableString
import pandas as pd
import requests
from tabulate import tabulate

URL = 'https://www.worldometers.info/coronavirus/'
TABLE_COLUMNS = ["Country", "Cases", "NCases", "Deaths",
                 "NDeaths", "Recovered", "Active", "Critical",
                 "CPM", "DPM", "Tests", "TPM"]


class HTMLTableParser:

    def parse_url(self, url):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'lxml')
        return [(table['id'], self.parse_html_table(table))
                for table in soup.find_all('table')]

    def parse_html_table(self, table):

        column_names = []

        # get <thead> and extract column names from it
        thead = table.find_all('thead')[0]
        th_tags = thead.find_all('th')

        for th in th_tags:
            col_name = []
            for item in th.contents:
                if isinstance(item, NavigableString):
                    col_name.append(item.strip(',+').strip())
                elif item.get_text().strip():
                    col_name.append(item.get_text().strip())
            column_names.append(' '.join(col_name))

        # get the first <tbody> and extract data
        tbody = table.find_all('tbody')[0]
        # list of lists from tr/td elements
        data = [
            [td.get_text().strip().replace(',', '').strip('+')
             for td in row.find_all('td')]
            for row in tbody.find_all('tr')]

        df = pd.DataFrame(data, columns=column_names)

        sorting_allowed = True
        # though we get column names from worldometers, we would like
        # our own compact names to help with display, sorting etc
        if len(df.columns) == len(TABLE_COLUMNS):
            df.columns = TABLE_COLUMNS
        else:
            print("WARNING: Number of columns is not as expected, sorting will not work.")
            sorting_allowed = False
        # replace empty strings with 0 in all columns
        # (does not impact the 'Country' column as it has data)
        for col in df.columns:
            df[col] = df[col].replace('', 0)

        if sorting_allowed:

            # convert a few columns to 'int'
            for col in ["Cases", "NCases", "Deaths",
                        "NDeaths", "Recovered", "Active",
                        "Critical", "Tests"]:
                try:
                    df[col] = df[col].astype(int)
                except ValueError as ve:
                    print(f"int(col) gave value error for {col}, {ve}")

            # convert a few columns to 'float'
            for col in ["CPM", "DPM", "TPM"]:
                try:
                    df[col] = df[col].astype(float)
                except ValueError as ve:
                    print(f"float(col) gave value error for {col}, {ve}")

        return df, sorting_allowed


def get_worldometer_stats():
    """
    Returns a pandas DataFrame with worldometers coronovirus stats.
    """

    hp = HTMLTableParser()
    data = hp.parse_url(URL)[0][1]
    return data


def display_stats(table):
    print(tabulate(table, headers=["#"] + list(table.columns),
                   tablefmt='psql'))


def export_stats_to_csv(table, timestamp):
    export_file_name = f'{timestamp}.csv'
    table.to_csv(export_file_name)
    print(f"Exported data to file: {export_file_name}")


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--export", "-e", help="export data to a CSV file", action="store_true")
    parser.add_argument("--sort_col", "-s",
                        action="store",
                        choices=TABLE_COLUMNS,
                        type=lambda arg: {x.lower(): x for x in TABLE_COLUMNS}[
                            arg.lower()],
                        default="Cases",
                        help="sort data by given column in descending order")
    parser.add_argument("--asc", "-a", action="store_true",
                        help="change sort order to ascending")
    args = parser.parse_args()

    # fetch data from worldometers
    table, sorting_allowed = get_worldometer_stats()
    # ['table.loc['Total']= table.sum()

    timestamp = datetime.datetime.now(
        datetime.timezone.utc).strftime("%Y-%m-%d %H:%M%Z")
    print("\n" + "Date/Time >: " + timestamp)
    print("Counters are reset at 23:59UTC" + "\n")

    sort_col = args.sort_col if sorting_allowed else 'None'
    # perform sorting if needed
    if sort_col != "None":
        table = table.sort_values(sort_col, ascending=args.asc)

    # display data table on the screen
    display_stats(table)

    if args.export:
        # export data to csv
        export_stats_to_csv(table, timestamp)


if __name__ == "__main__":
    main()
