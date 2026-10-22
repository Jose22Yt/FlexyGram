import java.io.File;
import java.util.Arrays;
import javax.tools.*;
import com.sun.source.util.JavacTask;
public class ParseJava {
    public static void main(String[] args) throws Exception {
        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        DiagnosticCollector<JavaFileObject> diagnostics = new DiagnosticCollector<>();
        try (StandardJavaFileManager files = compiler.getStandardFileManager(diagnostics, null, null)) {
            JavacTask task = (JavacTask) compiler.getTask(null, files, diagnostics,
                    Arrays.asList("-proc:none"), null, files.getJavaFileObjectsFromStrings(Arrays.asList(args)));
            task.parse();
            for (Diagnostic<?> d : diagnostics.getDiagnostics()) {
                if (d.getKind() == Diagnostic.Kind.ERROR) throw new AssertionError(d.toString());
            }
        }
        System.out.println("Full generated Java syntax PASS; no symbol/type/Android compilation claim");
    }
}
