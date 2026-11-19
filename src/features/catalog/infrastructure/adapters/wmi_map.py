"""WMI Mercosur + tabla de año para VIN (ISO 3779 / FMVSS).

Primera sección: WMI -> (fabricante, mercado). Segunda sección: char 10 del
VIN -> año candidato (se usa el ciclo más reciente razonable).
"""

WMI_MAP = {
    # Volkswagen
    '8AW': ('Volkswagen', 'Argentina'),
    'WVW': ('Volkswagen', 'Europa/Argentina'),
    'WV2': ('Volkswagen', 'Europa/Alemania'),
    '3VV': ('Volkswagen', 'Brasil'),
    '9BW': ('Volkswagen', 'Brasil'),
    # Toyota
    '8AJ': ('Toyota', 'Argentina'),
    'JT':  ('Toyota', 'Global/Japón'),
    'MRO': ('Toyota', 'Australia'),
    'JTH': ('Toyota', 'Global'),
    # Ford
    '9BF': ('Ford', 'Argentina'),
    '3FA': ('Ford', 'México'),
    '1Z':  ('Ford', 'Europa'),
    '1FM': ('Ford', 'USA'),
    # Renault
    '8A1': ('Renault', 'Argentina'),
    'VF':  ('Renault', 'Francia'),
    'VF1': ('Renault', 'Francia/Europa'),
    # Peugeot
    '8FC': ('Peugeot', 'Argentina'),
    'VF3': ('Peugeot', 'Francia/Europa'),
    # Citroën
    '8FS': ('Citroën', 'Argentina'),
    'VF7': ('Citroën', 'Francia/Europa'),
    # Fiat
    '8AB': ('Fiat', 'Argentina'),
    'ZFA': ('Fiat', 'Italia'),
    '3C3': ('Fiat', 'Italia/Lo mena'),
    # General Motors (Chevrolet)
    '9BR': ('Chevrolet', 'Argentina'),
    '6G2': ('Chevrolet', 'GM Argentina/Brasil'),
    '3G':  ('Chevrolet', 'GM México/LatAm'),
    '1G1': ('Chevrolet', 'GM USA'),
    # Honda
    '19X': ('Honda', 'Japón/Global'),
    'SHH': ('Honda', 'Tailandia'),
    # Nissan
    '3N1': ('Nissan', 'Japón/Global'),
    '5N1': ('Nissan', 'México'),
    # Hyundai / Kia
    'KMH': ('Hyundai', 'Corea/Global'),
    'KNA': ('Kia', 'Corea/Global'),
}

# ISO 3779 modelo-año centenario continuo (1980–2029)
YEAR_MAP = {
    'A': 2010, 'B': 2011, 'C': 2012, 'D': 2013, 'E': 2014, 'F': 2015,
    'G': 2016, 'H': 2017, 'J': 2018, 'K': 2019, 'L': 2020,
    'M': 2021, 'N': 2022, 'P': 2023, 'R': 2024, 'S': 2025, 'T': 2026,
    'U': 2027, 'V': 2028, 'W': 2029,
    '1': 2001, '2': 2002, '3': 2003, '4': 2004, '5': 2005,
    '6': 2006, '7': 2007, '8': 2008, '9': 2009,
}


def wmi_info(wmi: str):
    return WMI_MAP.get(wmi.upper()[:3])


def year_from_char(ch: str):
    return YEAR_MAP.get((ch or '').upper())
