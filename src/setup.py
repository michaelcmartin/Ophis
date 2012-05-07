from distutils.core import setup
setup(name='Ophis',
      version='1.0.1',
      description='A cross-assembler for the 6502 series of processors',
      url='https://github.com/michaelcmartin/Ophis',
      author="Michael Martin",
      author_email="mcmartin@gmail.com",
      license="MIT",
      long_description="Ophis is a cross-assembler for the 65xx series of chips. It supports the stock 6502 opcodes, the 65c02 extensions, and syntax for the \"undocumented opcodes\" in the 6510 chip used on the Commodore 64. (Syntax for these opcodes matches those given in the VICE team's documentation.)",
      packages=['Ophis'],
      scripts=['scripts/ophis'])
