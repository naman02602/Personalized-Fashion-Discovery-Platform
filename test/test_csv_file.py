import io
import pandas as pd
import pytest
from frontend.login_signup import validate_csv


def test_validate_csv_success():
    # Create a CSV in the correct format
    csv_data = "asin,Title,MainImage,Rating,NumberOfReviews,Price,AvailableSizes,AvailableColors,BulletPoints,SellerRank,ProductCat\n"
    csv_data += "123,Example Title,http://example.com/image.jpg,4.5,100,19.99,S/M/L,Red/Blue/Green,Point1/Point2,5,Clothing"

    # Use StringIO to simulate a file upload
    stringio = io.StringIO(csv_data)

    # Call the function and assert it returns the correct response
    assert validate_csv(stringio) == (True, "CSV validation successful.")


def test_validate_csv_missing_columns():
    # Create a CSV missing some required columns
    csv_data = "asin,Title,MainImage,Rating\n"
    csv_data += "123,Example Title,http://example.com/image.jpg,4.5"

    stringio = io.StringIO(csv_data)

    # The function should return False and a message about missing columns
    assert validate_csv(stringio) == (False, "Missing required columns in CSV.")
