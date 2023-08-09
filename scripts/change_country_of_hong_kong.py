import os
from zipfile import ZipFile
import re
from invenio_search import current_search_client as es
from io import StringIO
import xml.etree.ElementTree as ET
from invenio_pidstore.models import PersistentIdentifier
from invenio_records_files.api import Record
from invenio_db import db
import unidecode

dois_aff = {'10.1103/PhysRevD.105.L111502': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1103/PhysRevD.104.L111502': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1103/PhysRevD.105.076013': 'Guangdong Provincial Key Laboratory of Nuclear Science, Institute of Quantum Matter, South China Normal University, Guangzhou 510006, China and Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1103/PhysRevD.105.054026': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1103/PhysRevLett.126.012301': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1103/PhysRevD.106.096012': 'Guangdong Provincial Key Laboratory of Nuclear Science, Institute of Quantum Matter, South China Normal University, Guangzhou 510006, China and Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1016/j.physletb.2021.136724': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou, China',
 '10.1140/epjc/s10052-021-09613-8': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou, 510006, China',
 '10.1140/epjc/s10052-021-09715-3': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou, 510006, China',
 '10.1103/PhysRevD.103.L031901': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1103/PhysRevD.104.094505': 'Guangdong Provincial Key Laboratory of Nuclear Science, Institute of Quantum Matter, South China Normal University, Guangzhou 510006, Guangdong, China and Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, Guangdong, China',
 '10.1016/j.physletb.2022.137286': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou, China',
 '10.1103/PhysRevD.106.034019': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1016/j.physletb.2022.136916': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou, China',
 '10.1007/JHEP05(2021)185': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou, Guangdong, 510006, China',
 '10.1103/PhysRevD.105.114049': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1103/PhysRevC.105.054902': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1140/epjc/s10052-021-09642-3': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou, 510006, People’s Republic of China',
 '10.1007/JHEP08(2021)034': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou, 510006, China',
 '10.1016/j.physletb.2021.136392': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou, China',
 '10.1103/PhysRevLett.129.242001': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1103/PhysRevLett.129.132001': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1016/j.nuclphysb.2021.115370': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou, China',
 '10.1007/JHEP12(2022)053': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou, 510006, China',
 '10.1103/PhysRevD.104.054023': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1007/JHEP01(2021)093': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou, 510006, China',
 '10.1007/JHEP05(2021)287': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou, 510006, China',
 '10.1103/PhysRevD.106.074006': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1103/PhysRevD.105.096002': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1103/PhysRevD.107.034009': 'Guangdong Provincial Key Laboratory of Nuclear Science, Institute of Quantum Matter, South China Normal University and Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, People’s Republic of China',
 '10.1007/JHEP05(2021)081': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou, 510006, China',
 '10.1140/epjc/s10052-022-10423-9': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Higher Education Mega Center, South China Normal University, West Waihuan Road No. 378, Guangzhou, China',
 '10.1016/j.nuclphysb.2021.115528': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou, China',
 '10.1103/PhysRevD.105.074022': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1103/PhysRevD.105.094027': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1140/epjc/s10052-023-11725-2': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou, 510006, China',
 '10.1103/PhysRevD.106.096008': 'Guangdong Provincial Key Laboratory of Nuclear Science, Institute of Quantum Matter, South China Normal University, Guangzhou 510006, China and Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1103/PhysRevD.107.034012': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, South China Normal University, Guangzhou 510006, China',
 '10.1103/PhysRevD.107.034033': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1007/JHEP07(2023)002': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou, Guangdong, 510006, China',
 '10.1140/epjc/s10052-021-09180-y': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou, 510006, China',
 '10.1007/JHEP09(2021)117': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou, 510006, China',
 '10.1103/PhysRevD.105.096025': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1103/PhysRevD.105.056021': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1103/PhysRevD.107.116021': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1103/PhysRevD.106.116012': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1016/j.physletb.2022.136893': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou, China',
 '10.1140/epjc/s10052-022-10340-x': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou, 510006, China',
 '10.1103/PhysRevD.107.054034': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1103/PhysRevD.103.076023': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1103/PhysRevD.106.056022': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1103/PhysRevD.103.054043': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1103/PhysRevD.107.054007': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1103/PhysRevD.106.014512': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1007/JHEP03(2021)213': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou, 510006, China',
 '10.1103/PhysRevD.104.074502': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1103/PhysRevC.105.044904': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1140/epjc/s10052-022-10882-0': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou, 510006, China',
 '10.1007/JHEP02(2023)163': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou, 510006, China',
 '10.1103/PhysRevD.104.094503': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1007/JHEP01(2022)071': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing centre, South China Normal University, Guangzhou, 510006, China',
 '10.1103/PhysRevC.106.044904': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1103/PhysRevLett.127.082301': 'Guangdong Provincial Key Laboratory of Nuclear Science, Institute of Quantum Matter & Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1016/j.nuclphysb.2022.115971': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou, China',
 '10.1140/epjc/s10052-023-11807-1': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou, 510006, China',
 '10.1016/j.physletb.2022.137290': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou, China',
 '10.1103/PhysRevD.106.094009': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1103/PhysRevD.104.114039': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1103/PhysRevD.105.014024': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1007/JHEP08(2021)157': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou, 510006, China',
 '10.1103/PhysRevD.108.014035': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1103/PhysRevD.106.034509': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1007/JHEP06(2023)022': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1007/JHEP06(2023)146': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1103/PhysRevC.107.034911': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1103/PhysRevC.106.064901': 'Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Southern Nuclear Science Computing Center, South China Normal University, Guangzhou 510006, China',
 '10.1007/JHEP06(2023)044': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1007/JHEP06(2023)143': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1007/JHEP07(2023)069': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1007/JHEP07(2023)119': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1007/JHEP07(2023)075': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1007/JHEP07(2023)067': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1140/epjc/s10052-023-11608-6': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1140/epjc/s10052-023-11634-4': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1007/JHEP07(2023)066': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1140/epjc/s10052-023-11674-w': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1007/JHEP07(2023)138': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1007/JHEP07(2023)204': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1007/JHEP07(2023)228': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1103/PhysRevLett.131.031901': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China (associated with Center for High Energy Physics, Tsinghua University, Beijing, China)',
 '10.1140/epjc/s10052-023-11759-6': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1140/epjc/s10052-023-11832-0': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1103/PhysRevD.108.012018': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China (associated with Center for High Energy Physics, Tsinghua University, Beijing, China)',
 '10.1140/epjc/s10052-023-11560-5': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1103/PhysRevD.108.032002': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China (associated with Center for High Energy Physics, Tsinghua University, Beijing, China)',
 '10.1103/PhysRevD.108.L031102': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China (associated with Center for High Energy Physics, Tsinghua University, Beijing, China)',
 '10.1007/JHEP07(2022)117': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1103/PhysRevC.105.L032201': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China, associated to3',
 '10.1007/JHEP06(2023)073': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1007/JHEP04(2023)081': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1007/JHEP06(2023)132': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1007/JHEP07(2022)026': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1007/JHEP07(2022)099': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1007/JHEP03(2022)153': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1007/JHEP03(2022)109': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1007/JHEP05(2022)067': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1007/JHEP05(2022)038': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1007/JHEP11(2021)181': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1007/JHEP12(2021)117': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1007/JHEP12(2021)107': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1007/JHEP12(2021)141': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1007/JHEP10(2021)060': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1007/JHEP11(2021)043': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1103/PhysRevLett.127.111801': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China (associated with Center for High Energy Physics, Tsinghua University, Beijing, China)',
 '10.1103/PhysRevLett.128.142004': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China (associated with Center for High Energy Physics, Tsinghua University, Beijing, China)',
 '10.1007/JHEP01(2022)036': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1007/JHEP01(2022)166': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1007/JHEP01(2022)069': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1007/JHEP01(2022)065': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1103/PhysRevD.105.012010': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China (associated with Center for High Energy Physics, Tsinghua University, Beijing, China)',
 '10.1103/PhysRevLett.128.062001': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China (associated with Center for High Energy Physics, Tsinghua University, Beijing, China)',
 '10.1103/PhysRevD.104.L091102': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China (associated with Center for High Energy Physics, Tsinghua University, Beijing, China)',
 '10.1103/PhysRevLett.128.041801': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China (associated with Center for High Energy Physics, Tsinghua University, Beijing, China)',
 '10.1007/JHEP01(2022)131': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1007/JHEP04(2022)046': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1140/epjc/s10052-023-11673-x': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1103/PhysRevD.108.012013': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China (associated with Center for High Energy Physics, Tsinghua University, Beijing, China)',
 '10.1103/PhysRevLett.128.221801': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China (associated with Center for High Energy Physics, Tsinghua University, Beijing, China)',
 '10.1103/PhysRevLett.129.091801': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China (associated with Center for High Energy Physics, Tsinghua University, Beijing, China)',
 '10.1103/PhysRevLett.128.162001': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China (associated with Center for High Energy Physics, Tsinghua University, Beijing, China)',
 '10.1103/PhysRevLett.128.191802': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China (associated with Center for High Energy Physics, Tsinghua University, Beijing, China)',
 '10.1103/PhysRevD.105.072005': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China (associated with Center for High Energy Physics, Tsinghua University, Beijing, China)',
 '10.1103/PhysRevLett.128.191803': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China (associated with Center for High Energy Physics, Tsinghua University, Beijing, China)',
 '10.1140/epjc/s10052-022-10186-3': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China',
 '10.1103/PhysRevD.105.092013': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China (associated with Center for High Energy Physics, Tsinghua University, Beijing, China)',
 '10.1103/PhysRevLett.128.082001': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China (associated with Center for High Energy Physics, Tsinghua University, Beijing, China)',
 '10.1103/PhysRevD.104.112008': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China (associated with Center for High Energy Physics, Tsinghua University, Beijing, China)',
 '10.1103/PhysRevD.105.L051104': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China (associated with Center for High Energy Physics, Tsinghua University, Beijing, China)',
 '10.1140/epjc/s10052-023-11641-5': 'Guangdong Provincial Key Laboratory of Nuclear Science, Guangdong-Hong Kong Joint Laboratory of Quantum Matter, Institute of Quantum Matter, South China Normal University, Guangzhou, China'}

def find_articles_recid():
    dois_and_recids = {}
    for doi in dois_aff.keys():
        query = {
            "query": {
                "bool": {
                    "must": [{"match": {"dois.value": doi}}],
                }
            }
        }
        search_result = es.search(index="scoap3-records-record", body=query)
        try:
            recid = recid = search_result["hits"]["hits"][0]["_source"]["control_number"]
            dois_and_recids[recid] = dois_aff[doi]
        except:
            pass
    return dois_and_recids

def update_records(dois_and_recids):
    recids = dois_and_recids.keys()
    for recid in recids:
        pid = PersistentIdentifier.get("recid", recid)
        existing_record = Record.get_record(pid.object_uuid)
        for index_auth, author in enumerate(existing_record['authors']):
            try:
                for index_aff, affiliation in enumerate(existing_record['authors'][index_auth]['affiliations']):
                    if  unidecode.unidecode(dois_and_recids[recid].decode('utf-8')) in unidecode.unidecode(affiliation['value']):
                        print("Country is " + existing_record['authors'][index_auth]['affiliations'][index_aff]['country'])
                        existing_record['authors'][index_auth]['affiliations'][index_aff]['country'] = "China"
                        print("Country should be " + existing_record['authors'][index_auth]['affiliations'][index_aff]['country'])
                    else:
                        pass
            except:
                print("No affiliations")
        print('Updating record...', recid)
        existing_record.update(dict(existing_record))
        existing_record.commit()
        db.session.commit()

data = find_articles_recid()
update_records(data)


