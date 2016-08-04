#!/bin/bash
scoap3 collections create scoap3
scoap3 collections create "Acta Physica Polonica B" -p scoap3 -q 'collections.secondary:Acta'
scoap3 collections create "Nuclear Physics B" -p scoap3 -q 'publication_info.journal_title:"Nuclear Physics B"'
scoap3 collections create "Physics Letters B" -p scoap3 -q 'publication_info.journal_title:"Physics Letters B"'
scoap3 collections create "Advances in High Energy Physics" -p scoap3 -q 'collections.secondary:Hindawi'
scoap3 collections create "Chinese Physics C" -p scoap3 -q 'publication_info.journal_title:"Chinese Phys. C"'
scoap3 collections create "Journal of Cosmology and Astroparticle Physics" -p scoap3 -q 'publication_info.journal_title:JCAP'
scoap3 collections create "New Journal of Physics" -p scoap3 -q 'publication_info.journal_title:"New J. Phys."'
scoap3 collections create "Progress of Theoretical and Experimental Physics" -p scoap3 -q 'collections.secondary:Oxford'
scoap3 collections create "Journal of High Energy Physics" -p scoap3 -q 'collections.secondary:SISSA'
scoap3 collections create "European Physical Journal C" -p scoap3 -q 'collections.secondary:Springer'
