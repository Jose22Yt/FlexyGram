/* Owner-local/public-certificate verifier. Does not generate keys or process APK/AAB. */
import java.io.Console;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.KeyStore;
import java.security.MessageDigest;
import java.security.PrivateKey;
import java.security.SecureRandom;
import java.security.Signature;
import java.security.cert.CertificateFactory;
import java.security.cert.X509Certificate;
import java.security.interfaces.RSAPublicKey;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.Locale;
import javax.naming.ldap.LdapName;

class VerifySigning {
    private static final String OFFICIAL_SHA256 = "e71c4d1e14dd940892009c61164df522c133029df6d1258561f6a1a4d1f3c015";
    private static final String ALIAS = "flexygram-release";
    private static final String ALPHA_SHA256 =
        "c8f04cad685ca5757d35b25ea4b0b4613c7399909948d821e6ada61f9fb12b2c";

    private static String expectedFingerprint(String value) {
        String normalized = value.replace(":", "").toLowerCase(Locale.ROOT);
        if (!normalized.matches("[a-f0-9]{64}")) {
            throw new IllegalArgumentException("Expected SHA-256 must contain 64 hexadecimal digits.");
        }
        return normalized;
    }

    private static String validateCertificate(X509Certificate cert, String expected) throws Exception {
        cert.checkValidity();
        if (!(cert.getPublicKey() instanceof RSAPublicKey rsa) || rsa.getModulus().bitLength() != 3072) {
            throw new IllegalArgumentException("Certificate must use RSA 3072 bits.");
        }
        if (!cert.getSigAlgName().equalsIgnoreCase("SHA256withRSA")) {
            throw new IllegalArgumentException("Certificate must use SHA256withRSA.");
        }
        boolean correctName = false;
        int commonNameCount = 0;
        for (var rdn : new LdapName(cert.getSubjectX500Principal().getName()).getRdns()) {
            if (rdn.getType().equalsIgnoreCase("CN")) {
                commonNameCount++;
                correctName = rdn.getValue().equals("FlexyGram Release Key");
            }
        }
        if (!correctName || commonNameCount != 1 || !cert.getSubjectX500Principal().equals(cert.getIssuerX500Principal())) {
            throw new IllegalArgumentException("Expected the dedicated self-signed FlexyGram Release Key certificate.");
        }
        cert.verify(cert.getPublicKey());
        String sha = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(cert.getEncoded()));
        if (sha.equals(ALPHA_SHA256)) {
            throw new IllegalArgumentException("The Alpha certificate cannot be used for Beta.");
        }
        if (!sha.equals(OFFICIAL_SHA256)) {
            throw new IllegalArgumentException("Certificate is not the registered official FlexyGram Beta identity.");
        }
        if (expected != null && !sha.equals(expected)) {
            throw new IllegalArgumentException("Certificate SHA-256 differs from the pinned fingerprint.");
        }
        return sha;
    }

    private static X509Certificate inspectKeystore(Path file, boolean fromOwnerWizard) throws Exception {
        char[] password;
        if (fromOwnerWizard) {
            String supplied = System.getenv("FLEXYGRAM_LOCAL_STORE_PASSWORD");
            password = supplied == null ? null : supplied.toCharArray();
        } else {
            Console console = System.console();
            if (console == null) {
                throw new IllegalArgumentException("Use an interactive terminal; password piping and command-line passwords are not supported.");
            }
            password = console.readPassword("PKCS12 password (not displayed): ");
        }
        if (password == null || password.length == 0) {
            throw new IllegalArgumentException("A password is required.");
        }
        try {
            // Probe the actual file type; reject JKS even when JDK compatibility is enabled.
            KeyStore store = KeyStore.getInstance(file.toFile(), password);
            if (!store.getType().equalsIgnoreCase("PKCS12") || store.size() != 1 || !store.isKeyEntry(ALIAS)) {
                throw new IllegalArgumentException("Expected one PKCS12 private entry named flexygram-release.");
            }
            if (!(store.getKey(ALIAS, password) instanceof PrivateKey key)) {
                throw new IllegalArgumentException("Alias does not contain an accessible private key.");
            }
            if (!(store.getCertificate(ALIAS) instanceof X509Certificate cert)) {
                throw new IllegalArgumentException("Alias does not have an X.509 certificate.");
            }
            // Prove that the recovered private key matches the public certificate.
            // This signs only a random in-memory challenge, never an APK or AAB.
            byte[] nonce = new byte[32];
            new SecureRandom().nextBytes(nonce);
            Signature proof = Signature.getInstance("SHA256withRSA");
            proof.initSign(key);
            proof.update(nonce);
            byte[] signed = proof.sign();
            proof.initVerify(cert.getPublicKey());
            proof.update(nonce);
            if (!proof.verify(signed)) {
                throw new IllegalArgumentException("Private-key possession check failed.");
            }
            Arrays.fill(nonce, (byte) 0);
            Arrays.fill(signed, (byte) 0);
            return cert;
        } finally {
            Arrays.fill(password, '\0');
        }
    }

    public static void main(String[] args) {
        try {
            if (args.length < 2 || args.length > 3 || !(args[0].equals("keystore") || args[0].equals("keystore-env") || args[0].equals("certificate"))) {
                throw new IllegalArgumentException("Usage: java VerifySigning.java keystore|certificate PATH [EXPECTED_SHA256]");
            }
            String expected = args.length == 3 ? expectedFingerprint(args[2]) : null;
            Path file = Path.of(args[1]).toRealPath();
            if (!Files.isRegularFile(file)) {
                throw new IllegalArgumentException("Input must be an existing regular file.");
            }
            X509Certificate cert;
            if (args[0].startsWith("keystore")) {
                cert = inspectKeystore(file, args[0].equals("keystore-env"));
            } else {
                try (InputStream stream = Files.newInputStream(file)) {
                    cert = (X509Certificate) CertificateFactory.getInstance("X.509").generateCertificate(stream);
                    if (stream.read() != -1) {
                        throw new IllegalArgumentException("Expected a single public certificate, without trailing material.");
                    }
                }
            }
            String sha = validateCertificate(cert, expected);
            // Only public fields, never passwords, key encodings, paths or challenge signatures.
            System.out.println("{\"status\":\"PASS\",\"sha256\":\"" + sha
                + "\",\"public_key\":\"RSA-3072\",\"signature\":\"SHA256withRSA\",\"not_before\":\""
                + cert.getNotBefore().toInstant() + "\",\"not_after\":\"" + cert.getNotAfter().toInstant()
                + "\",\"private_key\":\"" + (args[0].startsWith("keystore") ? "POSSESSION_VERIFIED" : "NOT_CHECKED")
                + "\",\"custody\":\"OWNER_CONFIRMATION_REQUIRED\",\"android_apk\":\"NOT_TESTED\"}");
        } catch (Exception error) {
            // Do not echo provider exceptions: they may contain sensitive local details.
            System.err.println("FAIL: signing identity could not be verified. Check inputs, password, alias, certificate policy and pinned fingerprint locally.");
            System.exit(1);
        }
    }
}
