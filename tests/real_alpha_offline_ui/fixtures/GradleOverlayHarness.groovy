// A Gradle/AGP DSL model only. Executes the actual overlay script with Groovy 4.
// It is not an AGP build or proof of Android source-set behavior.
class GradleException extends RuntimeException { GradleException(String message) { super(message) } }
class Sources {
    List excludes = []; List dirs = []
    void exclude(String path) { excludes.add(path) }
    void srcDir(File path) { dirs.add(path) }
}
class ComponentModel {
    List callbacks = []
    def selector() { [all: { -> 'all' }] }
    void beforeVariants(Object selector, Closure callback) { callbacks.add(callback) }
}
def root = new File(args[0])
def script = new File(root, 'gradle/real-alpha-offline-ui.gradle')
def evaluate = { Map props ->
    def main = [java: new Sources()]
    def alpha = [java: new Sources(), res: new Sources()]
    def components = new ComponentModel()
    def binding = new Binding([
        providers: [gradleProperty: { String key -> [orNull: props[key]] }],
        rootProject: [file: { String path -> new File(root, path) }],
        file: { String path -> new File(root, 'TMessagesProj/' + path) },
        android: [sourceSets: [main: main, realAlpha: alpha]],
        androidComponents: components
    ])
    binding.setVariable('fileTree', { File path ->
        Set files = [] as Set
        path.eachFileRecurse(groovy.io.FileType.FILES) { files.add(it) }
        [files: files]
    })
    new GroovyShell(this.class.classLoader, binding).evaluate(script)
    [main: main, alpha: alpha, components: components]
}
def disabled = evaluate([:])
assert disabled.main.java.excludes.empty && disabled.alpha.java.dirs.empty && disabled.components.callbacks.empty
for (props in [[flexygramOfflineDialogsUi: 'true'],
               [flexygramOfflineDialogsUi: 'true', flexygramRealAlpha: 'true', flexygramRealAlphaStartupDiagnostics: 'true']]) {
    try { evaluate(props); throw new AssertionError('invalid profile accepted') }
    catch (GradleException expected) { assert expected.message.contains('REQUIRES_CLOSED_REAL_ALPHA_DEBUG') }
}
def enabled = evaluate([flexygramOfflineDialogsUi: 'true', flexygramRealAlpha: 'true'])
assert enabled.main.java.excludes.size() == 3
assert enabled.alpha.java.dirs.size() == 2 && enabled.alpha.res.dirs.size() == 1
for (flavor in ['diagnostic', 'betaDevelopment', 'production', 'realAlpha']) {
    for (build in ['debug', 'release', 'startupDiagnostic']) {
        def builder = [productFlavors: [[first: 'environment', second: flavor]], buildType: build, enable: true]
        enabled.components.callbacks.each { it.call(builder) }
        assert builder.enable == (flavor == 'realAlpha' && build == 'debug')
    }
}
def alreadyDisabled = [productFlavors: [[first: 'environment', second: 'realAlpha']], buildType: 'debug', enable: false]
enabled.components.callbacks.each { it.call(alreadyDisabled) }
assert !alreadyDisabled.enable
println('GradleOverlayHarness PASS (DSL model, no AGP)')
