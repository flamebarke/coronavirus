#!/usr/bin/python3

# Ref: https://srome.github.io/Parsing-HTML-Tables-in-Python-with-BeautifulSoup-and-pandas/

from __future__ import absolute_import, division

import datetime
import sys

from bs4 import BeautifulSoup
import pandas as pd
import requests
from tabulate import tabulate

URL = 'https://www.worldometers.info/coronavirus/'


class HTMLTableParser:

    def parse_url(self, url):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'lxml')
        return [(table['id'], self.parse_html_table(table))
                for table in soup.find_all('table')]

    def parse_html_table(self, table):
        n_columns = 0
        n_rows = 0
        column_names = []

        for row in table.find_all('tr'):
            td_tags = row.find_all('td')
            if len(td_tags) > 0:
                n_rows += 1
                if n_columns == 0:
                    n_columns = len(td_tags)

        th_tags = row.find_all('th')
        if len(th_tags) > 0 and len(column_names) == 0:
            for th in th_tags:
                column_names.append(th.get_text())

        if len(column_names) > 0 and len(column_names) != n_columns:
            raise Exception("Column titles do not match the number of columns")

        columns = column_names if len(
            column_names) > 0 else range(0, n_columns)
        df = pd.DataFrame(columns=columns,
                          index=range(0, n_rows))
        row_marker = 0
        for row in table.find_all('tr'):
            column_marker = 0
            columns = row.find_all('td')
            for column in columns:
                df.iat[row_marker, column_marker] = column.get_text()
                column_marker += 1
            if len(columns) > 0:
                row_marker += 1

        for col in df:
            try:
                df[col] = df[col].astype(float)
            except ValueError:
                pass
        df.columns = ["Country", "Cases", "+", "Deaths",
                      "+", "Recovered", "Active", "Critical",
                      "CPM", "DPM"]
        return df


def get_worldometer_stats():
    """
    Returns a pandas DataFrame with worldometers coronovirus stats.
    """

    hp = HTMLTableParser()
    table = hp.parse_url(URL)[0][1]
    return table


def display_stats(export=False):

    time = datetime.datetime.now(
        datetime.timezone.utc).strftime("%Y-%m-%d %H:%M%Z")
    print("\n" + "Date/Time >: " + time)
    print("Counters are reset at 23:59UTC" + "\n")

    table = get_worldometer_stats()

    print(tabulate(table, headers=["#"] + list(table.columns),
                   tablefmt='psql'))

    if export:
        table.to_csv(time + '.csv')


if __name__ == "__main__":
    display_stats(len(sys.argv) == 2)
