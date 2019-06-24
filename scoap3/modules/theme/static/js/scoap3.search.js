
// This file is part of SCOAP3.
// Copyright (C) 2015, 2016 CERN.
//
// SCOAP3 is free software; you can redistribute it
// and/or modify it under the terms of the GNU General Public License as
// published by the Free Software Foundation; either version 2 of the
// License, or (at your option) any later version.
//
// SCOAP3 is distributed in the hope that it will be
// useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
// General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with SCOAP3; if not, write to the
// Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
// MA 02111-1307, USA.
//
// In applying this license, CERN does not
// waive the privileges and immunities granted to it by virtue of its status
// as an Intergovernmental Organization or submit itself to any jurisdiction.
$(document).ready(function() {
    // add safe filter to invenioSearch module
    angular.module('invenioSearch')
    .filter('safe', ['$sce', function($sce) {
        return function(input) {
            return $sce.trustAsHtml(input);
        }
    }])
    .filter('titlecase_country', function() {
        return function(value) {
            if (!value) return value;
            if (typeof value !== 'string') {
                throw invalidPipeArgumentError(value);
            }

            // Some values should be uppercase.
            if (['cern', 'uk', 'usa', 'jinr'].includes(value.toLowerCase()))
                return value.toUpperCase()

            // Change first letter of words to uppercase, except: and, of
            return value.replace(/(?:(?!of|and\b)\b\w+)\S*/g, (txt => txt[0].toUpperCase() + txt.substr(1).toLowerCase()));
        }
    })
    .filter('short_title_journal', function() {
        return function(value) {
            if (!value) return value;
            if (typeof value !== 'string') {
                throw invalidPipeArgumentError(value);
            }

            var journal_mapping = {
                "Journal of Cosmology and Astroparticle Physics": "J. of Cos. and Astropartcile P.",
                "Advances in High Energy Physics": "Adv.High Energy Phys.",
                "Progress of Theoretical and Experimental Physics": 'Prog. of Theor. and Exp. Phys.',
                "Journal of High Energy Physics": "J. High Energy Phys."
            };

            return journal_mapping[value] || value
        }
    });
});
