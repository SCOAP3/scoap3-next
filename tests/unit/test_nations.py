# -*- coding: utf-8 -*-

from scoap3.utils.nations import _find_country_no_cache

affiliations = {
    "Instituto de Física, Pontificia Universidad Católica de Valparaíso, Avenida Brasil 2950, Casilla, Valparaíso, 4059, Chile": "Chile",
    "Instituto de Física, Pontificia Universidad Católica de Valparaíso, Avenida Brasil 2950, Casilla, Valparaiso, 4059, Chile": "Chile",
    "Instituto de Física, Facultad de Ciencias, Pontificia Universidad Católica de Valparaíso, Av. Brasil, Valparaiso, 2950, Chile": "Chile",
    "Instituto de Física, Pontificia Universidad Católica de Valparaíso, Av. Brasil 2950, Valparaíso, Chile": "Chile",
    "Instituto de Física, Pontificia Universidad Católica de Valparaíso, Av. Brasil, Valparaíso, 2950, Chile": "Chile",
    "Pontificia Universidad Católica de Valparaíso, Instituto de Física, Avenida Brasil 2950, Valparaíso, Chile": "Chile",
    "Facultad de Ciencias, Instituto de Física, Pontificia Universidad Católica de Valparaíso, Av. Brasil 2950, Valparaiso, Chile": "Chile",
    "Instituto de Física, Pontificia Universidad Católica de Valparaíso, Avda. Brasil 2950, Valparaiso, Chile": "Chile",
    "Instituto de Física, Pontificia Universidad Católica de Valparaíso, Avenida Brasil 2950, Valparaíso, Chile": "Chile",
    "Instituto de Física, Facultad de Ciencias, Pontificia Universidad Católica de Valparaíso, Av. Brasil 2950, Valparaiso, Chile": "Chile",
    "Instituto de Física, Pontificia Universidad de Católica de Valparaíso, Avenida Brasil 2950, Valparaíso, Chile": "Chile",
    "Instituto de Física, Pontificia Universidad Católica de Valparaíso, Avenida Brasil 2950, Casilla 4059, Valparaiso, Chile": "Chile",
    "Instituto de Física, Pontificia Universidad Católica de Valparaíso, Avenida Brasil 2950, Casilla 4059, Valparaíso, Chile": "Chile",
    "Instituto de Física, Facultad de Ciencias, Pontificia Universidad Católica de Valparaíso, Av. Brasil 2950, Valparaíso, Chile": "Chile",
    "Instituto de Física, Pontificia Universidad Católica de Valparaíso, Avenida Brasil 2950, Valparaiso, Chile": "Chile",
    "Pontificia Universidad Católica de Valparaíso, Instituto de Física, Av. Brasil 2950, Valparaíso, Chile": "Chile",
    "Pontificia Universidad Católica de Valparaíso, Instituto de Física, Av. Brasil, Valparaíso, 2950, Chile": "Chile",
    "Joint Institute for Nuclear Research, 141980 Dubna, Moscow region, Russia": "JINR",
    "Theoretical Physics Department, CERN, Esplande des Particules, 1211 Geneva 23, Switzerland" : "CERN",
    "Instituto de F?sica, Pontificia Universidad Cat?lica de Valpara?so, Avenida Chile 2950, Casilla, Valpara?so, 4059, Brasil": "Brazil",
    "Department of Mathematics and Physics, North China Electric Power University, Baoding, People's Republic of China": "China",}


def test_find_country_no_cache():
    for affiliation in affiliations:
        assert _find_country_no_cache(affiliation) == affiliations[affiliation]
