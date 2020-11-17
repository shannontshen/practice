from numpy.distutils.fcompiler import FCompiler

compilers = ['FJFCompiler']

class FJFCompiler(FCompiler):
    compiler_type = 'fj'
    description = 'Fujitsu Fortran Compiler'

    possible_executables = ['frt']
    version_pattern = r'frt \(FRT\) (?P<version>[a-z\d.]+)'
    # $ frt --version
    # frt (FRT) x.x.x yyyymmdd

    executables = {
        'version_cmd'  : ["<F77>", "--version"],
        'compiler_f77' : ["frt", "-Fixed"],
        'compiler_fix' : ["frt", "-Fixed"],
        'compiler_f90' : ["frt"],
        'linker_so'    : ["frt", "-shared"],
        'archiver'     : ["ar", "-cr"],
        'ranlib'       : ["ranlib"]
        }
    pic_flags = ['-KPIC']
    module_dir_switch = '-M'
    module_include_switch = '-I'

    def get_flags_opt(self):
        return ['-O3']
    def get_flags_debug(self):
        return ['-g']
    def runtime_library_dir_option(self, dir):
        return f'-Wl,-rpath={dir}'

if __name__ == '__main__':
    from distutils import log
    from numpy.distutils import customized_fcompiler
    log.set_verbosity(2)
    print(customized_fcompiler('fj').get_version())
