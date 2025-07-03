"""
Check if user has checked in today
"""


def check_da_diem_danh_chua():
    """
    Check daycheck.txt to see if the user has checked in today
    :return: 1 if user has checked in today, 2 if user has not checked in today, 3 if daycheck.txt does not exist
    """

    import datetime
    now = datetime.datetime.now().date()
    try:
        with open('daycheck.txt', 'r') as file:
            last = datetime.datetime.strptime(file.read().strip(), "%Y-%m-%d").date()
        if now > last:
            print("2")
            return False
        else:
            print("1")
            return True
    except FileNotFoundError:
        print("3")
        return False


if __name__ == "__main__":
    check_da_diem_danh_chua()
