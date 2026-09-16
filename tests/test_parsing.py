from sicar_pa.parsing import g, normalizar_cpf_cnpj, safe_dict


def test_safe_dict_returns_dict_unchanged():
    assert safe_dict({"a": 1}) == {"a": 1}


def test_safe_dict_returns_empty_for_non_dict():
    assert safe_dict(None) == {}
    assert safe_dict([1, 2, 3]) == {}
    assert safe_dict("string") == {}


def test_g_returns_value_when_present():
    assert g({"a": 1}, "a") == 1


def test_g_returns_default_when_missing_or_none():
    assert g({"a": None}, "a", default="fallback") == "fallback"
    assert g({}, "missing", default="fallback") == "fallback"


def test_g_returns_default_for_non_dict_input():
    assert g(None, "a", default="fallback") == "fallback"


def test_normalizar_cpf_pads_to_11_digits():
    assert normalizar_cpf_cnpj("123.456.789-01") == "12345678901"
    assert normalizar_cpf_cnpj("1") == "00000000001"


def test_normalizar_cnpj_pads_to_14_digits():
    assert normalizar_cpf_cnpj("12.345.678/0001-95") == "12345678000195"


def test_normalizar_cpf_cnpj_returns_none_for_empty_or_invalid():
    assert normalizar_cpf_cnpj("") is None
    assert normalizar_cpf_cnpj(None) is None
    assert normalizar_cpf_cnpj("abc-def") is None
