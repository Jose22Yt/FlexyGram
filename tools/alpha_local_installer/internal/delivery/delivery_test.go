package delivery

import (
	"archive/tar"
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"io"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"filippo.io/age"
)

// Generated identities below are throwaway TEST fixtures, never the owner's key.
type entry struct {
	name string
	data []byte
	kind byte
	size int64
}

func fixture(t *testing.T, change func(*[]entry, map[string]any)) ([]byte, []byte, contract) {
	t.Helper()
	id, err := age.GenerateX25519Identity()
	if err != nil {
		t.Fatal(err)
	}
	apk := []byte("test APK bytes, not an Android release")
	h := sha256.Sum256(apk)
	c := contract{id.Recipient().String(), hex.EncodeToString(h[:]), "", "test-commit", strings.Repeat("a", 64), 2}
	r := map[string]any{"application_id": "io.github.jose22yt.flexygram.alpha", "version_code": 1265, "sha256": c.apk, "bytes": len(apk), "commit": c.commit, "status": "PASS_ARTIFACT_ONLY", "android_runtime": "NOT_TESTED", "certificate_sha256": strings.Repeat("a", 64), "elf_count": 2,
		"elfs": []map[string]string{{"name": "lib/one.so", "sha256": strings.Repeat("b", 64)}, {"name": "assets/chaquopy.zip!/two.so", "sha256": strings.Repeat("c", 64)}}}
	entries := []entry{{APKName, apk, tar.TypeReg, 0}}
	if change != nil {
		change(&entries, r)
	}
	reportBytes, _ := json.Marshal(r)
	entries = append(entries, entry{"verification.json", reportBytes, tar.TypeReg, 0})
	var plain bytes.Buffer
	tw := tar.NewWriter(&plain)
	for _, e := range entries {
		size := int64(len(e.data))
		if e.size != 0 {
			size = e.size
		}
		if err := tw.WriteHeader(&tar.Header{Name: e.name, Mode: 0600, Size: size, Typeflag: e.kind}); err != nil {
			t.Fatal(err)
		}
		if e.size == 0 {
			if _, err := tw.Write(e.data); err != nil {
				t.Fatal(err)
			}
		}
		if e.size != 0 {
			break
		} // Deliberately truncated oversized fixture.
	}
	tw.Close()
	var encrypted bytes.Buffer
	w, err := age.Encrypt(&encrypted, id.Recipient())
	if err != nil {
		t.Fatal(err)
	}
	if _, err = w.Write(plain.Bytes()); err != nil {
		t.Fatal(err)
	}
	if err = w.Close(); err != nil {
		t.Fatal(err)
	}
	b := encrypted.Bytes()
	ch := sha256.Sum256(b)
	c.cipher = hex.EncodeToString(ch[:])
	return b, []byte("# test fixture\n# public key: " + id.Recipient().String() + "\n" + id.String() + "\n"), c
}

func TestAuthenticatedDelivery(t *testing.T) {
	b, key, c := fixture(t, nil)
	dir := t.TempDir()
	if err := decrypt(bytes.NewReader(b), bytes.NewReader(key), dir, c); err != nil {
		t.Fatal(err)
	}
	apk, err := os.ReadFile(filepath.Join(dir, APKName))
	if err != nil || !bytes.HasPrefix(apk, []byte("test APK")) {
		t.Fatal("missing verified output")
	}
	files, _ := os.ReadDir(dir)
	if len(files) != 2 {
		t.Fatal("unexpected persisted file", files)
	}
	for _, f := range files {
		if strings.Contains(f.Name(), "key") || strings.Contains(f.Name(), "identity") {
			t.Fatal("identity persisted")
		}
	}
}

func TestRejectInvalidDelivery(t *testing.T) {
	tests := map[string]func(*[]entry, map[string]any){
		"wrong package":             func(es *[]entry, r map[string]any) { r["application_id"] = "other" },
		"previous Alpha 2 version":  func(es *[]entry, r map[string]any) { r["version_code"] = 1262 },
		"previous personalized":     func(es *[]entry, r map[string]any) { r["version_code"] = 1264 },
		"previous Signature Fix":    func(es *[]entry, r map[string]any) { r["version_code"] = 1263 },
		"wrong signing certificate": func(es *[]entry, r map[string]any) { r["certificate_sha256"] = strings.Repeat("b", 64) },
		"wrong version":             func(es *[]entry, r map[string]any) { r["version_code"] = 1261 },
		"wrong APK":                 func(es *[]entry, r map[string]any) { (*es)[0].data = []byte("altered") },
		"wrong report hash":         func(es *[]entry, r map[string]any) { r["sha256"] = strings.Repeat("d", 64) },
		"wrong source commit":       func(es *[]entry, r map[string]any) { r["commit"] = "other" },
		"wrong ELF count":           func(es *[]entry, r map[string]any) { r["elf_count"] = 96 },
		"wrong ELF inventory":       func(es *[]entry, r map[string]any) { r["elfs"] = []any{} },
		"duplicate ELF": func(es *[]entry, r map[string]any) {
			r["elfs"] = []map[string]string{{"name": "same", "sha256": strings.Repeat("a", 64)}, {"name": "same", "sha256": strings.Repeat("b", 64)}}
		},
		"invalid certificate": func(es *[]entry, r map[string]any) { r["certificate_sha256"] = "invalid" },
		"false runtime claim": func(es *[]entry, r map[string]any) { r["android_runtime"] = "PASSED" },
		"wrong bytes":         func(es *[]entry, r map[string]any) { r["bytes"] = 1 },
		"path traversal": func(es *[]entry, r map[string]any) {
			*es = append(*es, entry{"../escape", []byte("x"), tar.TypeReg, 0})
		},
		"extra file": func(es *[]entry, r map[string]any) {
			*es = append(*es, entry{"private-key.txt", []byte("x"), tar.TypeReg, 0})
		},
		"duplicate APK": func(es *[]entry, r map[string]any) { *es = append(*es, (*es)[0]) },
		"symlink":       func(es *[]entry, r map[string]any) { *es = append(*es, entry{"link", nil, tar.TypeSymlink, 0}) },
		"oversize APK":  func(es *[]entry, r map[string]any) { (*es)[0].size = MaxAPK + 1 },
		"oversize report": func(es *[]entry, r map[string]any) {
			*es = append(*es, entry{"verification.json", bytes.Repeat([]byte(" "), maxReport+1), tar.TypeReg, 0})
		},
	}
	for name, mutate := range tests {
		t.Run(name, func(t *testing.T) {
			b, key, c := fixture(t, mutate)
			dir := t.TempDir()
			if err := decrypt(bytes.NewReader(b), bytes.NewReader(key), dir, c); err == nil {
				t.Fatal("accepted corrupt delivery")
			}
			files, _ := os.ReadDir(dir)
			if len(files) != 0 {
				t.Fatal("failed delivery persisted", files)
			}
		})
	}
}

func TestIdentityAndAuthenticationFailures(t *testing.T) {
	b, key, c := fixture(t, nil)
	other, _ := age.GenerateX25519Identity()
	cases := map[string]struct {
		cipher, key []byte
		contract    contract
	}{
		"public recipient is not identity":     {b, []byte(c.recipient), c},
		"wrong identity":                       {b, []byte(other.String()), c},
		"identity too large":                   {b, bytes.Repeat([]byte("x"), 65537), c},
		"multiple identities":                  {b, append(append([]byte{}, key...), []byte(other.String())...), c},
		"truncated final authentication chunk": {b[:len(b)-1], key, c},
		"wrong ciphertext hash":                {b, key, contract{c.recipient, c.apk, strings.Repeat("0", 64), c.commit, c.certificate, c.elfCount}},
	}
	corrupt := append([]byte{}, b...)
	corrupt[len(corrupt)-1] ^= 1
	cases["corrupt final authentication chunk"] = struct {
		cipher, key []byte
		contract    contract
	}{corrupt, key, c}
	for name, x := range cases {
		t.Run(name, func(t *testing.T) {
			dir := t.TempDir()
			if err := decrypt(bytes.NewReader(x.cipher), bytes.NewReader(x.key), dir, x.contract); err == nil {
				t.Fatal("accepted invalid input")
			}
			files, _ := os.ReadDir(dir)
			if len(files) != 0 {
				t.Fatal("failed delivery persisted")
			}
		})
	}
}

func TestReadErrors(t *testing.T) {
	b, key, c := fixture(t, nil)
	if decrypt(bytes.NewReader(b), badReader{}, t.TempDir(), c) == nil {
		t.Fatal("accepted identity read failure")
	}
	if decrypt(badReader{}, bytes.NewReader(key), t.TempDir(), c) == nil {
		t.Fatal("accepted cipher read failure")
	}
}

type badReader struct{}

func (badReader) Read([]byte) (int, error) { return 0, io.ErrUnexpectedEOF }

func TestProductionContractCannotAcceptFixture(t *testing.T) {
	b, key, _ := fixture(t, nil)
	if Decrypt(bytes.NewReader(b), bytes.NewReader(key), t.TempDir()) == nil {
		t.Fatal("test fixture bypassed production pins")
	}
}
