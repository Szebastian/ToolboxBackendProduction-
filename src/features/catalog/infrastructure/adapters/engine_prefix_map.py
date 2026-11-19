"""Mapa de prefijos de número de motor → especificación.

Clave: prefijo tal como figura en la placa/documentación del motor (ej. BKP,
K4M, 1KD). Valores: (cilindrada_cc, familia, aspiración, timing, etiqueta).

Familia ∈ {nafta, diesel, turbo, aspirado} — se usa para filtrar visibilidad de
subcategorías. `timing` ∈ {correa, cadena}.
"""

ENGINE_PREFIX_MAP = {
    # Volkswagen (Argentina/Europa/Brasil)
    'CFZ':  (2000, 'diesel', 'turbo', 'correa', '2.0 TDI · Correa · Turbo'),
    'CFFB': (2000, 'diesel', 'turbo', 'correa', '2.0 TDI · Correa · Turbo'),
    'CFZB': (2000, 'diesel', 'turbo', 'correa', '2.0 TDI · Correa · Turbo · 140CV'),
    'BKP':  (2000, 'diesel', 'turbo', 'correa', '2.0 TDI · Correa · Turbo · 140CV'),
    'CBDB': (2000, 'diesel', 'turbo', 'correa', '2.0 TDI · Correa · Turbo'),
    'BGD':  (2000, 'nafta',  'turbo', 'cadena', '2.0 T · Cadena · Turbo'),
    'AWX':  (2000, 'diesel', 'turbo', 'correa', '2.0 TDI · Correa'),
    'BUD':  (2000, 'nafta',  'aspirado', 'cadena', '2.0 · Cadena · Nafta'),
    # Renault
    'K4M':  (1600, 'nafta',  'aspirado', 'correa', '1.6 16V · Correa · Nafta'),
    'D4F':  (1600, 'nafta',  'aspirado', 'correa', '1.6 16V · Correa · Nafta'),
    'H4M':  (1600, 'nafta',  'aspirado', 'cadena', '1.6 16V · Cadena · Nafta'),
    'M9R':  (2000, 'diesel', 'turbo', 'correa', '2.0 dCi · Correa · Turbo'),
    'F3R':  (2000, 'nafta',  'aspirado', 'correa', '2.0 16V · Correa · Nafta'),
    # Toyota
    '1KD':  (3000, 'diesel', 'turbo', 'correa', '3.0 D-4D · Correa · Turbo'),
    '2KD':  (2500, 'diesel', 'turbo', 'correa', '2.5 D-4D · Correa · Turbo'),
    '1GD':  (2800, 'diesel', 'turbo', 'correa', '2.8 D-4D · Correa · Turbo'),
    '2GD':  (2400, 'diesel', 'turbo', 'correa', '2.4 D-4D · Correa · Turbo'),
    '1NZ-FE': (1500, 'nafta', 'aspirado', 'cadena', '1.5 16V · Cadena · Nafta'),
    '2TR-FE': (2700, 'nafta', 'aspirado', 'correa', '2.7 16V · Correa · Nafta'),
    # PSA (Peugeot / Citroën)
    'XU7':  (1800, 'nafta',  'aspirado', 'correa', '1.8 16V · Correa · Nafta'),
    'EW10': (2000, 'nafta',  'aspirado', 'correa', '2.0 16V · Correa · Nafta'),
    'DV6':  (1400, 'diesel', 'turbo', 'correa', '1.4 HDi · Correa · Turbo'),
    'TU5':  (1600, 'nafta',  'aspirado', 'correa', '1.6 16V · Correa · Nafta'),
    # Fiat
    '188A': (1300, 'nafta',  'aspirado', 'correa', '1.25 8V · Correa · Nafta'),
    'F14':  (1300, 'diesel', 'turbo', 'correa', '1.3 Mjet · Correa · Turbo'),
    '188B5': (1600, 'nafta', 'aspirado', 'correa', '1.6 · Correa · Nafta'),
    # Ford
    'Duratec': (2300, 'nafta', 'aspirado', 'correa', '2.3 Duratec · Correa · Nafta'),
    'EcoBoost': (1600, 'nafta', 'turbo', 'correa', '1.6 EcoBoost · Correa · Turbo'),
}
