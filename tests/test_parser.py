from motor_reader.parser import parse_nameplate

def test_parse_common_motor_fields():
    text = "TYPE YE2-100L-6 3 PHASE VOLTS 220/380 V CURRENT 1.93/1.12 A 0.37 kW 945 r/min IP55 INSULATION F MOUNTING B3"
    result = parse_nameplate(text)
    assert result["Model"] == "YE2-100L-6"
    assert result["Phase"] == "3"
    assert "220/380" in result["Voltage"]
    assert result["IP Rating"] == "IP55"
    assert result["Insulation"] == "F"

def test_parse_rpm():
    result = parse_nameplate("MOTOR SPEED 1470 rpm")
    assert result["Speed"].startswith("1470")
