# first exec in console to generate .tex file: python3 pphysical_constants.py
# https://tex.stackexchange.com/questions/496330/value-of-physical-constants-in-latex#496369
# https://docs.scipy.org/doc/scipy/reference/constants.html
from scipy.constants import physical_constants as pc
import re
from math import ceil

filename = r'physical_constants.tex'
setup = r"""
\RequirePackage{etoolbox}
\RequirePackage{xparse}
\RequirePackage{siunitx}

\makeatletter

\def\physicalconstants@missingconstantmarker#1{%
    \ifx\@onlypreamble\@notprerr% only insert the marker when not in preamble
        {\textbf{??#1??}}%
    \fi
}
\def\physicalconstants@declare#1#2#3#4#5{% {name}{value}{unit}{uncertainty}
    \csdef{physicalconstants@#1@value}{#2}%
    \csdef{physicalconstants@#1@unit}{#3}%
    \csdef{physicalconstants@#1@uncertainty}{#4}%
    \csdef{physicalconstants@#1@uncertainvalue}{#5}%
}
\def\physicalconstants@blind@get#1#2{% {entry}{name}
    \csuse{physicalconstants@#2@#1}%
}
\def\physicalconstants@try#1{% {name}{subject}, gobbles subject if name is undefined
    \ifcsdef{physicalconstants@#1@value}{%
        \@firstofone
    }{%
        \GenericWarning{}{LaTeX Warning: I do not know the physical constant `#1'.}%
        \physicalconstants@missingconstantmarker{#1}%
        \@gobble
    }%
}
\def\physicalconstants@declarealias#1#2{% {new}{old}
    \physicalconstants@try{#2}{%
        \csdef{physicalconstants@#1@value}{\physicalconstants@blind@get{value}{#2}}%
        \csdef{physicalconstants@#1@unit}{\physicalconstants@blind@get{unit}{#2}}%
        \csdef{physicalconstants@#1@uncertainty}{\physicalconstants@blind@get{uncertainty}{#2}}%
        \csdef{physicalconstants@#1@uncertainvalue}{\physicalconstants@blind@get{uncertainvalue}{#2}}%
    }%
}
\def\physicalconstants@get#1#2{% {entry}{name}
    \physicalconstants@try{#2}{%
        \physicalconstants@blind@get{#1}{#2}%
    }%
}
\NewDocumentCommand\pcalias{}{% {new}{old}}
    \physicalconstants@declarealias
}
\NewDocumentCommand\pcget{}{% {entry}{name}
    \physicalconstants@get
}
\NewDocumentCommand\pcvalue{O{} m}{% [\num options]{name}
    \physicalconstants@try{#2}{%
        \num[#1]{\physicalconstants@blind@get{value}{#2}}%
    }%
}
\NewDocumentCommand\pcunit{O{} m}{% [\si options]{name}
    \physicalconstants@try{#2}{%
        \si[#1]{\physicalconstants@blind@get{unit}{#2}}%
    }%
}
\NewDocumentCommand\pcuncertainty{O{} m}{% [\num options]{name}
    \physicalconstants@try{#2}{%
        \num[#1]{\physicalconstants@blind@get{uncertainty}{#2}}%
    }%
}
\NewDocumentCommand\pcuncertainvalue{O{} m}{% [\num options]{name}
    \physicalconstants@try{#2}{%
        \num[#1]{\physicalconstants@blind@get{uncertainvalue}{#2}}%
    }%
}
\NewDocumentCommand\pc{O{} m}{% [\SI options]{name}
    \physicalconstants@try{#2}{%
        \SI[#1]{\physicalconstants@blind@get{value}{#2}}{\physicalconstants@blind@get{unit}{#2}}%
    }%
}
\NewDocumentCommand\pcu{O{} m}{% [\num options]{name}
    \physicalconstants@try{#2}{%
        \SI[#1]{\physicalconstants@blind@get{uncertainvalue}{#2}}{\physicalconstants@blind@get{unit}{#2}}%
    }%
}

"""
cleanup = r"""
\makeatother
"""

unit_map = {
    'A': r'\ampere',
    'C': r'\coulomb',
    'F': r'\farad',
    'GeV': r'\giga\electronvolt',
    'Hz': r'\hertz',
    'J': r'\joule',
    'K': r'\kelvin',
    'MHz': r'\mega\hertz',
    'MeV': r'\mega\electronvolt',
    'N': r'\newton',
    'Pa': r'\pascal',
    'S': r'\siemens',
    'T': r'\tesla',
    'V': r'\volt',
    'W': r'\watt',
    'Wb': r'\weber',
    'c': r'\clight',
    'eV': r'\electronvolt',
    'fm': r'\femto\meter',
    'kg': r'\kilogram',
    'm': r'\metre',
    'mol': r'\mole',
    'ohm': r'\ohm',
    's': r'\second',
    'sr': r'\steradian',
    'u': r'\atomicmassunit',
}
unit_regex = re.compile(r'\b([a-zA-Z]+)(?:\^(-?)(\d+))?\b')
number_regex = re.compile(r'([+-]?)(\d+)(\.?)(\d*)(e?)([+-]?\d*)')


def format_unit(unit_input):
    unit = ''
    for (base, sign, exp) in unit_regex.findall(unit_input):
        if sign:
            unit += r'\per'
        if exp == '1':
            pass
        elif exp == '2':
            unit += r'\square'
        elif exp == '3':
            unit += r'\cube'
        elif exp:
            unit += r'\raiseto{{{}}}'.format(exp)
        unit += unit_map[base]
    return unit
        
def format_uncertain_value(value_input, uncertainty_input):
    val_parts = number_regex.fullmatch(str(value_input)).groups()
    unc_parts = number_regex.fullmatch(str(uncertainty_input)).groups()
    unc_digits = unc_parts[1] + unc_parts[3]
    if int(unc_digits):
        val_exp = int(val_parts[5]) if val_parts[5] else 0
        unc_exp = int(unc_parts[5]) if unc_parts[5] else 0
        exp_discrepancy = ( (unc_exp - len(unc_parts[3]))
                           - (val_exp - len(val_parts[3])) )
        if exp_discrepancy < 0:
            # The uncertainty is too granular, we have to round.
            unc_digits = str(ceil(float('{}e{}'.format(unc_digits, exp_discrepancy))))
        else:
            # The uncertainty is missing some zeros at the end.
            unc_digits += '0' * exp_discrepancy
    else:
        unc_digits = '0'
    return '{0}{1}{2}{3}({6}){4}{5}'.format(*val_parts, unc_digits)

def main():
    with open(filename, 'w') as of:
        of.write(setup)
        for (name, entries) in pc.items():
            (value, unit, uncertainty) = entries
            of.write(r'\physicalconstants@declare{{{}}}{{{}}}{{{}}}{{{}}}{{{}}}'.format(
                            name,
                            value,
                            format_unit(unit),
                            uncertainty, 
                            format_uncertain_value(value, uncertainty))
                        + '\n')
        of.write(cleanup)
        
if __name__ == '__main__':
    main()
    print(r'⧹emph{Hello}, world!')


