from conans import ConanFile, CMake
from conans.client.generators.cmake import CMakeGenerator
from conans.util.files import normalize, save

import subprocess
import os
from os.path import join
import shutil
import tempfile
from io import StringIO


CMAKE_TEMPLATE_START = "cmake_minimum_required(VERSION 3.0)"

CMAKE_TEMPLATE_BODY = """
include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()

file(WRITE ${CMAKE_BINARY_DIR}/inspection.txt
"[[CXX][${CMAKE_CXX_COMPILER}]]
[[C][${CMAKE_C_COMPILER}]]
[[AR][${CMAKE_AR}]]
[[LD][${CMAKE_LINKER}]]
[[NM][${CMAKE_NM}]]
[[OBJDUMP][${CMAKE_OBJDUMP}]]
[[RANLIB][${CMAKE_RANLIB}]]
[[STRIP][${CMAKE_STRIP}]]
[[CXX_FLAGS][${CMAKE_CXX_FLAGS}]]
[[C_FLAGS][${CMAKE_C_FLAGS}]]
[[ASM_FLAGS][${CMAKE_ASM_FLAGS}]]
[[LD_EXE][${CMAKE_EXE_LINKER_FLAGS}]]
[[LD_MODULE][${CMAKE_MODULE_LINKER_FLAGS}]]
[[LD_SHARED][${CMAKE_SHARED_LINKER_FLAGS}]]
[[LD_STATIC][${CMAKE_STATIC_LINKER_FLAGS}]]
[[SYSTEM_NAME][${CMAKE_SYSTEM_NAME}]]
[[SYSTEM_VERSION][${CMAKE_SYSTEM_VERESION}]]
[[SYSTEM_PROCESSOR][${CMAKE_SYSTEM_PROCESSOR}]]
"
)
"""


class PlatformInspector(object):
    def _write_conaninfo(self):
        generator = CMakeGenerator(self._conanfile)
        generator.output_path = self._build_folder
        content = generator.content
        content  = normalize(content)
        self._conanfile.output.info("Conan info file created %s" % (generator.filename))
        save(join(self._build_folder, generator.filename), content, only_if_modified=True)

    def __init__(self, conanfile, verbose=False, languages='C CXX ASM'):
        self._conanfile = conanfile
        self._source_folder = tempfile.mkdtemp()
        self._build_folder = tempfile.mkdtemp()

        source_folder = self._source_folder
        build_folder = self._build_folder

        with open(os.path.join(source_folder, 'CMakeLists.txt'), 'w') as f:
            project_type = '\nproject(inspector LANGUAGES %s)\n' % languages
            full_text = CMAKE_TEMPLATE_START + project_type + CMAKE_TEMPLATE_BODY
            f.write(full_text )

        conanfile.output.info('Source folder: %s' % source_folder)
        conanfile.output.info('Bild folder: %s' % build_folder)

        if verbose:
            conanfile.output.info(self._conanfile.env)

        self._write_conaninfo()

        cmake = CMake(conanfile)
        cmake.configure(source_dir=source_folder, build_dir=build_folder)

        self.c = None
        self.cxx = None
        self.ar = None
        self.ld = None
        self.nm = None
        self.objdump = None
        self.ranlib = None
        self.strip = None
        self.cxx_flags = []
        self.c_flags = []
        self.asm_flags = []
        self.ld_exe_flags = []
        self.ld_module_flags = []
        self.ld_shared_flags = []
        self.ld_static_flags = []
        self.system_name = None
        self.system_processor = None
        self.system_version = None

        with open(join(build_folder, 'inspection.txt'), 'r') as f:
            out = f.readlines()

        if verbose:
            conanfile.output.info('-- Inspector output:')
            for line in out:
                conanfile.output.info(line)

        for line in out:
            line = line.strip()
            if not line.startswith('[[') or not line.endswith(']]'):
                continue
            line = line[2:][:-2]
            name, value = line.split(']')
            name = name.strip()
            value = value[1:].strip()

            if name == 'CXX':
                self.cxx = value
            elif name == 'C':
                self.c = value
            elif name == 'AR':
                self.ar = value
            elif name == 'LD':
                self.ld = value
            elif name == 'NM':
                self.nm = value
            elif name == 'OBJDUMP':
                self.objdump = value
            elif name == 'RANLIB':
                self.ranlib = value
            elif name == 'STRIP':
                self.strip = value
            elif name == 'CXX_FLAGS':
                self.cxx_flags = value.split(' ')
            elif name == 'C_FLAGS':
                self.c_flags = value.split(' ')
            elif name == 'ASM_FLAGS':
                self.asm_flags = value.split(' ')
            elif name == 'LD_EXE':
                self.ld_exe_flags = value.split(' ')
            elif name == 'LD_MODULE':
                self.ld_module_flags = value.split(' ')
            elif name == 'LD_SHARED':
                self.ld_shared_flags = value.split(' ')
            elif name == 'LD_STATIC':
                self.ld_static_flags = value.split(' ')
            elif name == 'SYSTEM_NAME':
                self.system_name = value
            elif name == 'SYSTEM_VERSION':
                self.system_version = value
            elif name == 'SYSTEM_PROCESSOR':
                self.system_processor = value

        shutil.rmtree(source_folder)
        shutil.rmtree(build_folder)


class Pkg(ConanFile):
    name = 'platform-inspector'
    version = '0.0.1'
    description = "A silly helper for extracting compiler and it's settings from CMake cache, assuming all our toolchains are built upon CMake"
    url = ''
