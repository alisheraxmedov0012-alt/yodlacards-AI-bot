from datetime import datetime


def calculate_level_xp(level):

    return level * 100


def today():

    return datetime.now().strftime("%Y-%m-%d")
