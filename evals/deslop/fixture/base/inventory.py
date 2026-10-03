"""Stock levels from a CSV of sku,qty."""
import csv

LOW_STOCK = 5


def load_stock(path):
    with open(path, newline="") as fh:
        return {row["sku"]: int(row["qty"]) for row in csv.DictReader(fh)}


def low_stock(stock):
    return sorted(s for s, q in stock.items() if q < LOW_STOCK)


def total_units(stock):
    # loop over the stock and add it up
    total = 0
    for qty in stock.values():
        total += qty
    return total
