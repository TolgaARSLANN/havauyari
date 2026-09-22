import pytest

from havauyari.alerts.aqi import (
    ALERT_INDEX,
    UNHEALTHY_INDEX,
    aqi_category,
    is_alert,
    pm25_to_aqi,
    threshold_concentration,
)


@pytest.mark.parametrize(
    "conc, expected",
    [(0.0, 0), (9.0, 50), (9.1, 51), (35.4, 100), (35.5, 101), (55.4, 150), (55.5, 151),
     (125.4, 200), (225.4, 300), (325.4, 500), (1000, 500)],
)
def test_pm25_to_aqi_breakpoints(conc, expected):
    assert pm25_to_aqi(conc) == expected


def test_truncation_not_rounding():
    # EPA kuralı: 9.09 -> 9.0 (İyi), 9.1'e yuvarlanmaz
    assert aqi_category(9.09) == "İyi"


def test_category_and_alert():
    assert aqi_category(20) == "Orta"
    # Ana uyarı eşiği 35,5 (hassas gruplar için sağlıksız)
    assert threshold_concentration(ALERT_INDEX) == 35.5
    assert not is_alert(35.49)
    assert is_alert(35.5)
    # İkinci kademe 55,5
    assert not is_alert(50, UNHEALTHY_INDEX)
    assert is_alert(60, UNHEALTHY_INDEX)


def test_invalid_input():
    with pytest.raises(ValueError):
        pm25_to_aqi(-1)
