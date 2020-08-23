from conans import ConanFile


class InspectorTest(ConanFile):
    name='inspector-test'
    version='0.1'
    python_requires = 'platform-inspector/0.0.1@conan-burrito/stable'
    generator = 'cmake'

    def build(self):
        inspectorClass = self.python_requires['platform-inspector'].module.PlatformInspector
        inspector = inspectorClass(conanfile=self, verbose=True)
        print('Compiler: ' + inspector.cxx)
