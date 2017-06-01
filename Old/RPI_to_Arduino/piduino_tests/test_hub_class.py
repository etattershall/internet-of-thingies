import pytest
import sys
sys.path.append('../piduino')
from piduino.piduino import Hub

def test_initialise_hub():
    myhub = Hub()
    assert type(myhub.own_address) == str 
