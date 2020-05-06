#!/usr/bin/python3

# Ref: https://srome.github.io/Parsing-HTML-Tables-in-Python-with-BeautifulSoup-and-pandas/

from __future__ import absolute_import, division

import argparse
import datetime

from bs4 import BeautifulSoup
import pandas as pd
import requests
from tabulate import tabulate

URL = 'https://www.worldometers.info/coronavirus/'

TABLE_COLUMNS = {
    'CountryOther': 'Country',
    'TotalCases': 'Cases',
    'NewCases': 'NCases',
    'TotalDeaths': 'Deaths',
    'NewDeaths': 'NDeaths',
    'TotalRecovered': 'Recovered',
    'ActiveCases': 'Active',
    'SeriousCritical': 'Critical',
    'TotCases/1Mpop': 'CPM',
    'Deaths/1Mpop': 'DPM',
    'TotalTests': 'Tests',
    'Tests/1Mpop': 'TPM',
    'Continent': 'Continent'
}


class HTMLTableParser:

    def parse_url(self, url):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'lxml')
        return [(table['id'], self.parse_html_table(table))
                for table in soup.find_all('table')]

    def get_friendly_column_names(self, col_names):
        unknown = []
        f_col_names = []
        for col in col_names:
            if col in TABLE_COLUMNS:
                name = TABLE_COLUMNS[col]
            else:
                name = col
                unknown.append(col)
            f_col_names.append(name)
        return f_col_names, unknown

    def parse_html_table(self, table):

        column_names = []

        # get <thead> and extract column names from it
        thead = table.find_all('thead')[0]
        th_tags = thead.find_all('th')
        column_names = [
            th.get_text().replace(' ', '').replace('\n', '')
            .replace('\xa0', '').replace(',', '') for th in th_tags]

        # though we get column names from worldometers, we would like
        # our own compact names to help with display, sorting etc
        friendly_column_names, unknown_cols = self.get_friendly_column_names(
            column_names)

        # get the first <tbody> to extract data
        tbody = table.find_all('tbody')[0]

        # list of lists from tr/td elements
        data = [
            [td.get_text().strip().replace(',', '').strip('+')
             for td in row.find_all('td')]
            for row in tbody.find_all('tr')]

        # use friendly column names when creating DataFrame
        df = pd.DataFrame(data, columns=friendly_column_names)

        if unknown_cols:
            print(
                f"WARNiNG: Unexpected column names from worldometers data \
                    ({unknown_cols}). Please raise an issue on github.")

        # convert a few columns to 'int'
        for col in ["Cases", "NCases", "Deaths",
                    "NDeaths", "Recovered", "Active",
                    "Critical", "Tests"]:
            df[col] = df[col].replace('', 0)
            df[col] = df[col].replace("N/A", 0)

            try:
                df[col] = df[col].astype(int)
            except ValueError as ve:
                print(f"int(col) gave value error for {col}, {ve}")

        # convert a few columns to 'float'
        for col in ["CPM", "DPM", "TPM"]:
            df[col] = df[col].replace('', 0)
            try:
                df[col] = df[col].astype(float)
            except ValueError as ve:
                print(f"float(col) gave value error for {col}, {ve}")

        try:
            df['Country'] = df['Country'].replace('', 'Non-Country')
        except KeyError:
            pass  # do nothing

        try:
            df['Continent'] = df['Continent'].replace('', 'Non-Continent')
        except KeyError:
            pass  # do nothing

        return df


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
    parser.add_argument("--export", "-e",
                        help="export data to a CSV file",
                        action="store_true")
    parser.add_argument("--sort_col", "-s",
                        default="Cases",
                        help="Sort data by given column in descending order. \
                        Defaults to 'Cases'. Pass 'None' to skip sorting.")
    parser.add_argument("--asc", "-a", action="store_true",
                        help="change sort order to ascending")
    args = parser.parse_args()

    # fetch data from worldometers
    table = get_worldometer_stats()

    timestamp = datetime.datetime.now(
        datetime.timezone.utc).strftime("%Y-%m-%d %H:%M%Z")
    print("\n" + "Date/Time >: " + timestamp)
    print("Counters are reset at 23:59UTC" + "\n")

    # perform sorting if needed
    if args.sort_col != "None":
        if args.sort_col in table.columns:
            table = table.sort_values(args.sort_col, ascending=args.asc)
        else:
            print(
                f"ERROR: provided column name '{args.sort_col}' is invalid. \
                    Use a valid column name for sorting.")

    # display data table on the screen
    display_stats(table)

    if args.export:
        # export data to csv
        export_stats_to_csv(table, timestamp)


if __name__ == "__main__":
    main()
