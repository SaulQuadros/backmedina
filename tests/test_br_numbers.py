import math

from backmedina.io.br_numbers import parse_br_number


def test_milhar_ponto():
    assert parse_br_number("4.059") == 4059.0
    assert parse_br_number("2.080") == 2080.0


def test_decimal_virgula():
    assert parse_br_number("-21,77314") == -21.77314
    assert parse_br_number("0,00") == 0.0


def test_milhar_e_decimal():
    assert parse_br_number("2.080,00") == 2080.0
    assert parse_br_number("1.234,56") == 1234.56


def test_ja_numerico():
    assert parse_br_number(44) == 44.0
    assert parse_br_number(9.0) == 9.0


def test_vazio_e_invalido():
    assert math.isnan(parse_br_number(""))
    assert math.isnan(parse_br_number(None))
    assert math.isnan(parse_br_number("abc"))


def test_ponto_decimal_simples():
    # "162" e "162.0" sem vírgula: não são milhar.
    assert parse_br_number("162") == 162.0
    assert parse_br_number("162.5") == 162.5
