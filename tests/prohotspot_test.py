import pytest
from pytest import approx
import open_cp.prohotspot as testmod

import numpy as np
from datetime import datetime, timedelta
from unittest import mock
import open_cp

Cell = open_cp.RectangularRegion

def test_weight_diags_same_distance():
    weight = testmod.ClassicDiagonalsSame()
    assert( weight.distance(1, 1, 2, 2) == 1 )
    assert( weight.distance(1, 1, 1, 2) == 1 )
    assert( weight.distance(1, 1, 1, 1) == 0 )
    assert( weight.distance(2, 1, 1, 2) == 1 )
    assert( weight.distance(2, 1, 4, 3) == 2 )
    

def test_weight_diags_same_weight():
    weight = testmod.ClassicDiagonalsSame()
    cell = Cell(10, 20, 50, 60)
    
    # Too far in past
    assert( weight(cell, np.timedelta64(8, "W"), 0, 0) == 0 )
    
    # Too distant
    assert( weight(cell, np.timedelta64(1, "W"), 1000, 0) == 0 )
    
    # Same cell and time
    assert( weight(cell, np.timedelta64(0), 15, 55) == 1 )
    assert( weight(cell, np.timedelta64(0), 10, 50) == 1 )
    assert( weight(cell, np.timedelta64(0), 20 - 0.1, 60 - 0.1) == 1 )
    
    # Time tests
    assert( weight(cell, np.timedelta64(1, "W"), 15, 55) == approx(0.5) )
    assert( weight(cell, np.timedelta64(9, "D"), 15, 55) == approx(0.5) )
    assert( weight(cell, np.timedelta64(13, "D"), 15, 55) == approx(0.5) )
    assert( weight(cell, np.timedelta64(14, "D"), 15, 55) == approx(1 / 3) )
    assert( weight(cell, np.timedelta64(20, "D"), 15, 55) == approx(1 / 3) )
    assert( weight(cell, np.timedelta64(21, "D"), 15, 55) == approx(1 / 4) )
    assert( weight(cell, np.timedelta64(7 * 7 - 1, "D"), 15, 55) == approx(1 / 7) )
    assert( weight(cell, np.timedelta64(7 * 7, "D"), 15, 55) == 0 )
    
    # Space tests
    assert( weight(cell, np.timedelta64(0), 20, 55) == approx(1 / 2) )
    assert( weight(cell, np.timedelta64(0), 30, 55) == approx(1 / 3) )
    assert( weight(cell, np.timedelta64(0), 40, 55) == approx(1 / 4) )
    assert( weight(cell, np.timedelta64(0), 399, 55) == approx(1 / 39) )
    assert( weight(cell, np.timedelta64(0), 400, 55) == 0 )
    
    # Combined
    assert( weight(cell, np.timedelta64(1, "W"), 20, 65) == approx(1 / 4) )
    assert( weight(cell, np.timedelta64(3, "W"), 30, 65) == approx(1 / (4 * 3)) )
    
    
def test_weight_diags_different_distance():
    weight = testmod.ClassicDiagonalsDifferent()
    assert( weight.distance(1, 1, 2, 2) == 2 )
    assert( weight.distance(1, 1, 1, 2) == 1 )
    assert( weight.distance(1, 1, 2, 1) == 1 )
    assert( weight.distance(1, 1, 4, 5) == 7 )
    
    
def test_predict_wrong_times():
    pred = testmod.ProspectiveHotSpot(Cell(0, 0, 0, 0))
    with pytest.raises(ValueError):
        pred.predict(datetime(2017, 3, 10, 12, 30), datetime(2017, 3, 10, 0))

def test_predict_single_event():
    region = open_cp.RectangularRegion(0, 150, 0, 150)
    cutoff = datetime(2017, 3, 10, 12, 30)
    predict = cutoff
    times = [cutoff]
    coords = np.array([75, 75]).reshape((2,1))
    
    pred = testmod.ProspectiveHotSpot(region)
    pred.data = open_cp.TimedPoints(times, coords)
    prediction = pred.predict(cutoff, predict)
    
    wanted = [ [0.5, 0.5, 0.5], [0.5, 1, 0.5], [0.5, 0.5, 0.5] ]
    for i in range(3):
        for j in range(3):
            assert( prediction.grid_risk(i, j) == wanted[j][i] )
            
    assert( prediction.grid_risk(3, 0) == 0 )
    assert( prediction.grid_risk(0, 3) == 0 )
    
def test_predict_filter_by_time():
    region = open_cp.RectangularRegion(0, 100, 0, 100)
    cutoff = datetime(2017, 3, 10, 12, 30)
    predict = datetime(2017, 3, 17, 12, 30)
    times = [cutoff, cutoff + timedelta(hours = 5)]
    coords = [ [25, 75], [25, 75] ]
    data = open_cp.TimedPoints(times, coords)
    
    pred = testmod.ProspectiveHotSpot(region)
    pred.data = data
    prediction = pred.predict(cutoff, predict)
    
    assert( prediction.grid_risk(0, 0) == approx(1 / 2) )
    assert( prediction.grid_risk(0, 1) == approx(1 / 4) )
    assert( prediction.grid_risk(1, 0) == approx(1 / 4) )
    assert( prediction.grid_risk(1, 1) == approx(1 / 4) )

def test_predict_multiple_events():
    region = open_cp.RectangularRegion(0, 100, 0, 100)
    cutoff = datetime(2017, 3, 15, 12, 30)
    predict = datetime(2017, 3, 17, 12, 30)
    times = [cutoff - timedelta(days = 5), cutoff]
    coords = [ [25, 75], [25, 75] ]
    data = open_cp.TimedPoints(times, coords)
    
    pred = testmod.ProspectiveHotSpot(region)
    pred.data = data
    prediction = pred.predict(cutoff, predict)
    
    assert( prediction.grid_risk(0, 0) == approx(1 / 2 + 1 / 2) )
    assert( prediction.grid_risk(0, 1) == approx(1 / 4 + 1 / 2) )
    assert( prediction.grid_risk(1, 0) == approx(1 / 4 + 1 / 2) )
    assert( prediction.grid_risk(1, 1) == approx(1 / 4 + 1) )


# Aim is to now test the predictition algorithm.  If we believe the weight code
# is correct (which we do!) then we can supply our own simplified weight and
# test that the predict code does the right thing with it.

class TestWeightConstant(testmod.Weight):
    def __call__(self, cell, timestamp, x, y):
        return 1

def a_valid_predictor():
    region = open_cp.RectangularRegion(0,100,0,144)
    predictor = testmod.ProspectiveHotSpot(region)
    predictor.weight = TestWeightConstant()
    predictor.grid = 10
    timestamps = [datetime(2017,3,1)]
    xcoords = [50]
    ycoords = [50]
    predictor.data = open_cp.TimedPoints.from_coords(timestamps, xcoords, ycoords)
    return predictor

def test_ProspectiveHotSpot_cannot_pass_wrong_data_type():
    p = a_valid_predictor()
    with pytest.raises(TypeError):
        p.data = [1,2,3]

def test_ProspectiveHotSpot_times_ordered():
    p = a_valid_predictor()
    with pytest.raises(ValueError):
        p.predict(datetime(2017,1,1), datetime(2016,1,1))

def test_ProspectiveHotSpot_correct_return():
    p = a_valid_predictor()
    prediction = p.predict(datetime(2017,3,2), datetime(2017,3,2))
    # Grid size
    assert( prediction.xsize == 10 )
    assert( prediction.ysize == 10 )
    # Weight is uniformly 1.
    for i in range(10):
        for j in range(14):
            assert( prediction.grid_risk(i, j) == 1 )
    assert( prediction.grid_risk(-1,0) == 0 )
    assert( prediction.grid_risk(10,0) == 0 )
    assert( prediction.grid_risk(0,14) == 0 )

def test_ProspectiveHotSpot_filters_by_time():
    p = a_valid_predictor()
    prediction = p.predict(datetime(2017,2,1), datetime(2017,3,10))
    assert( prediction.grid_risk(0,0) == 0 )

def test_ProspectiveHotSpot_weight_gets_time_delta():
    p = a_valid_predictor()
    p.weight = mock.Mock(return_value = 1)
    p.predict(datetime(2017,3,1), datetime(2017,3,4,12,30))

    expected = timedelta(days=3, hours=12, minutes=30)
    for call_args in p.weight.call_args_list:
        assert( call_args[0][1] == np.timedelta64(expected) )
    assert( p.weight.call_count == 140 )

def test_ProspectiveHotSpot_gets_correct_cell_outline_and_coords():
    region = open_cp.RectangularRegion(5,100,7,144)
    predictor = testmod.ProspectiveHotSpot(region)
    predictor.grid = 15
    timestamps = [datetime(2017,3,1)]
    xcoords = [50]
    ycoords = [70]
    predictor.data = open_cp.TimedPoints.from_coords(timestamps, xcoords, ycoords)
    
    predictor.weight = mock.Mock(return_value = 1)
    predictor.predict(datetime(2017,3,1), datetime(2017,3,4,12,30))

    for call_args in predictor.weight.call_args_list:
        assert( call_args[0][2] == 50 )
        assert( call_args[0][3] == 70 )
        cell = call_args[0][0]
        assert( (cell.xmin - 5) % 15 == 0 )
        assert( (cell.ymin - 7) % 15 == 0 )
        assert( cell.xmax - cell.xmin == 15 )
        assert( cell.ymax - cell.ymin == 15 )

def test_ProspectiveHotSpot_record_total_weight():
    predictor = a_valid_predictor()
    timestamps = [datetime(2017,3,1), datetime(2017,3,1)]
    xcoords = [52, 72]
    ycoords = [52, 25]
    predictor.data = open_cp.TimedPoints.from_coords(timestamps, xcoords, ycoords)

    class TestWeight(testmod.Weight):
        def __call__(self, cell, timestamp, x, y):
            if cell.xmin < x and x < cell.xmax and cell.ymin < y and y < cell.ymax:
                return 1 if x == 52 else 2
            return 0.5
    predictor.weight = TestWeight()
        
    prediction = predictor.predict(datetime(2017,3,1), datetime(2017,3,1))
    assert( prediction.grid_risk(5, 5) == 1.5 )
    assert( prediction.grid_risk(7, 2) == 2.5 )
    assert( prediction.grid_risk(0, 0) == 1.0 )