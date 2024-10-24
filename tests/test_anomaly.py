import pytest
import pandas as pd
import re

from rdflib import URIRef, Literal
from afdd.main import *
from timescale import TimeseriesData, PointReading


def test_load_graph_success():
    """
    checks that load_graph function loaded everything in with no null values, valid timeseries ids, and that device name and ts id match
    """

    facility_uri = "https://syyclops.com/example/example"
    device_list = [
        ("VG21D16414", "5e81563a-42ca-4137-9b36-f423a6f27a73"),
        ("VG21D22031", "9cdcab62-892c-46c8-b3d2-3d525512576a"),
    ]
    pattern = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"

    # checking dataframe is returned
    df = load_graph(facility_uri=facility_uri, device_list=device_list)
    assert type(df) == pd.DataFrame

    for index, row in df.iterrows():
        assert row["class"] != None
        assert row["point"] != None
        assert row["timeseriesid"] != None
        assert row["device name"] != None

    # checking all id's in timeseriesid column are valid
    for i in df["timeseriesid"]:
        assert re.match(pattern, i) != None

    # checking device name and timeseries id match up
    for device in device_list:
        device_name = device[0]
        device_udid = device[1]
        device_df = df.loc[df["device name"] == device_name]
        for index, row in device_df.iterrows():
            assert (row["timeseriesid"].startswith(Literal(device_udid))) and (
                row["device name"] == Literal(device_name)
            ) == True


def test_load_graph_invalid_inputs():
    with pytest.raises(TypeError) as error:
        df = load_graph(facility_uri=3948293, device_list=[("a", "b")])
    assert str(error.value) == "Facility URI must be a string. "

    with pytest.raises(TypeError) as error:
        df = load_graph(facility_uri="facility_uri", device_list=(2, 3, 4))
    assert (
        str(error.value)
        == "Device list must be a list of tuples in the format (device_name, device_udid). "
    )

    with pytest.raises(TypeError) as error:
        df = load_graph(facility_uri="facility_uri", device_list=[(2, 3)])
    assert str(error.value) == "Device name and id must be strings. "

    with pytest.raises(Exception) as error:
        df = load_graph(facility_uri="facility_uri", device_list=[("1", "2", "3")])
    assert (
        str(error.value)
        == "Device list must be a list of tuples in the format (device_name, device_udid). "
    )


def test_co2_rule():
    assert co2_too_high(1001) == True
    assert co2_too_high(5) == False

    with pytest.raises(TypeError) as error:
        co2_too_high("343")
    assert str(error.value) == "Measurement must be a float. "


def create_dataframe():
    dict = {
        "class": [
            URIRef("https://brickschema.org/schema/Brick#CO2_Sensor"),
            URIRef("https://brickschema.org/schema/Brick#Temperature_Sensor"),
            URIRef("https://brickschema.org/schema/Brick#CO2_Sensor"),
        ],
        "point": [
            URIRef(
                "https://syyclops.com/example/example/point/9cdcab62-892c-46c8-b3d2-3d525512576a-co2"
            ),
            URIRef(
                "https://syyclops.com/example/example/point/5e81563a-42ca-4137-9b36-f423a6f27a73-temperature"
            ),
            URIRef(
                "https://syyclops.com/example/example/point/5e81563a-42ca-4137-9b36-f423a6f27a73-co2"
            ),
        ],
        "timeseriesid": [
            Literal("9cdcab62-892c-46c8-b3d2-3d525512576a-co2"),
            Literal("5e81563a-42ca-4137-9b36-f423a6f27a73-temperature"),
            Literal("5e81563a-42ca-4137-9b36-f423a6f27a73-co2"),
        ],
        "device name": [
            Literal("VG21D22031"),
            Literal("VG21D16414"),
            Literal("VG21D16414"),
        ],
    }
    dict_df = pd.DataFrame(dict)
    return dict_df


def test_load_timeseries_success():
    # must be connected to postgres timeseries database in order to run load_timeseries()

    # making dataframe and putting all of the CO2 sensor ts ids into a list
    df = create_dataframe()
    id_list = []
    for index, row in df.iterrows():
        if row["class"] == URIRef("https://brickschema.org/schema/Brick#CO2_Sensor"):
            id_list.append(str(row["timeseriesid"]))

    # using load_timeseries to get ts data and compiling the ts ids from that data into another list
    start_time = "2024-06-13T13:00:04Z"
    end_time = "2024-06-13T14:00:04Z"
    brick_class_co2 = "https://brickschema.org/schema/Brick#CO2_Sensor"
    data_list = load_timeseries(df, start_time, end_time, brick_class_co2)
    tsid_data_list = []
    for tsdata in data_list:
        tsid_data_list.append(tsdata["timeseriesid"])

    # checking all of the ids from the first list are in the second list
    for id in id_list:
        assert (id in tsid_data_list) == True


def test_analyze_data():
    # initialize all required variables for analyze_data() function
    list = [
        TimeseriesData(
            data=[PointReading("5", 1003, "5e81563a-42ca-4137-9b36-f423a6f27a73-co2")],
            timeseriesid="5e81563a-42ca-4137-9b36-f423a6f27a73-co2",
        )
    ]
    df = create_dataframe()
    co2Rule = Rule(
        name="CO2 Too High",
        id=1,
        description="ppm above 1000",
        sensors_required=[URIRef("https://brickschema.org/schema/Brick#CO2_Sensor")],
    )

    def co2_too_high(ppm):
        if ppm > 1000:
            return True
        return False

    anomalies = analyze_data(list, df, co2Rule, co2_too_high, [])
    assert anomalies[0] == {
        "name": "CO2 Too High",
        "rule": 1,
        "timestamp": "5",
        "device": "VG21D16414",
        "value": 1003,
    }
