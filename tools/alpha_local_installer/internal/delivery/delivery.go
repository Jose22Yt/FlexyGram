// Package delivery uses upstream age unchanged. Only the two pinned deliverables
// may leave its private staging directory, after authenticated EOF and all checks.
package delivery

import (
	"archive/tar"
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"

	"filippo.io/age"
)

const APKName = "FlexyGram-Alpha-arm64.apk"
const APKHash = ""
const CipherHash = ""
const Recipient = "age1dc36uuvdg4ut52crhgux297zfjc5u0p0rucgnjss8svmgdl2eylseanqqe"
const Commit = ""
const CertificateSHA256 = "c8f04cad685ca5757d35b25ea4b0b4613c7399909948d821e6ada61f9fb12b2c"
const MaxAPK = 256 << 20
const maxReport = 256 << 10

var ErrIdentity = errors.New("identity rejected")
var ErrIntegrity = errors.New("delivery integrity rejected")

type contract struct {
	recipient, apk, cipher, commit, certificate string
	elfCount                                    int
}
type report struct {
	ApplicationID string `json:"application_id"`
	VersionCode   int    `json:"version_code"`
	SHA256        string `json:"sha256"`
	Certificate   string `json:"certificate_sha256"`
	Commit        string `json:"commit"`
	Status        string `json:"status"`
	Runtime       string `json:"android_runtime"`
	Bytes         int64  `json:"bytes"`
	ELFCount      int    `json:"elf_count"`
	ELFs          []struct {
		Name   string `json:"name"`
		SHA256 string `json:"sha256"`
	} `json:"elfs"`
}

// Decrypt never accepts an alternate production hash, recipient or source commit.
// The identity reader is consumed in memory only, and is never written to disk.
func Decrypt(cipher, identity io.Reader, output string) error {
	return decrypt(cipher, identity, output, contract{Recipient, APKHash, CipherHash, Commit, CertificateSHA256, 96})
}

func validHash(s string) bool {
	b, e := hex.DecodeString(s)
	return e == nil && len(b) == 32 && s == hex.EncodeToString(b)
}

func decrypt(cipher, identity io.Reader, output string, c contract) (err error) {
	key, e := io.ReadAll(io.LimitReader(identity, (64<<10)+1))
	if e != nil || len(key) > 64<<10 {
		return ErrIdentity
	}
	defer clear(key)
	ids, e := age.ParseIdentities(bytes.NewReader(key))
	if e != nil || len(ids) != 1 {
		return ErrIdentity
	}
	x, ok := ids[0].(*age.X25519Identity)
	if !ok || x.Recipient().String() != c.recipient {
		return ErrIdentity
	}
	// Staging is on the app's private filesystem. No untrusted tar path is used.
	staging, e := os.MkdirTemp(output, ".pending-")
	if e != nil {
		return errors.New("private staging unavailable")
	}
	defer os.RemoveAll(staging)
	for _, name := range []string{APKName, "verification.json"} {
		if e = os.Remove(filepath.Join(output, name)); e != nil && !os.IsNotExist(e) {
			return errors.New("old delivery unavailable")
		}
	}
	ch := sha256.New()
	reader, e := age.Decrypt(io.TeeReader(cipher, ch), ids...)
	if e != nil {
		return ErrIntegrity
	}
	tr := tar.NewReader(reader)
	seen := map[string]bool{}
	var apkDigest string
	var apkBytes int64
	var reportData []byte
	for {
		h, e := tr.Next()
		if e == io.EOF {
			break
		}
		if e != nil {
			return ErrIntegrity
		}
		if seen[h.Name] || (h.Name != APKName && h.Name != "verification.json") || h.Typeflag != tar.TypeReg || h.Size <= 0 {
			return ErrIntegrity
		}
		seen[h.Name] = true
		if h.Name == APKName {
			if h.Size > MaxAPK {
				return ErrIntegrity
			}
			f, e := os.OpenFile(filepath.Join(staging, APKName), os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
			if e != nil {
				return errors.New("private output unavailable")
			}
			ah := sha256.New()
			n, copyErr := io.Copy(io.MultiWriter(f, ah), tr)
			closeErr := f.Close()
			if copyErr != nil || closeErr != nil || n != h.Size {
				return ErrIntegrity
			}
			apkBytes, apkDigest = n, hex.EncodeToString(ah.Sum(nil))
		} else {
			if h.Size > maxReport {
				return ErrIntegrity
			}
			reportData, e = io.ReadAll(tr)
			if e != nil || int64(len(reportData)) != h.Size {
				return ErrIntegrity
			}
		}
	}
	// tar EOF alone is NOT authenticated age EOF. Consume the remaining age
	// stream, including its final AEAD chunk; reject hidden trailing content.
	tail, e := io.ReadAll(io.LimitReader(reader, (1<<20)+1))
	if e != nil || len(tail) > 1<<20 || !bytes.Equal(tail, make([]byte, len(tail))) {
		return ErrIntegrity
	}
	if len(seen) != 2 || apkDigest != c.apk || hex.EncodeToString(ch.Sum(nil)) != c.cipher {
		return ErrIntegrity
	}
	var r report
	if json.Unmarshal(reportData, &r) != nil || r.SHA256 != c.apk || r.Bytes != apkBytes || r.Commit != c.commit ||
		r.ApplicationID != "io.github.jose22yt.flexygram.alpha" || r.VersionCode != 1271 || r.Status != "PASS_ARTIFACT_ONLY" || r.Runtime != "NOT_TESTED" || r.ELFCount != c.elfCount ||
		len(r.ELFs) != c.elfCount || r.Certificate != c.certificate || !validHash(r.Certificate) {
		return ErrIntegrity
	}
	names := map[string]bool{}
	for _, elf := range r.ELFs {
		if elf.Name == "" || names[elf.Name] || !validHash(elf.SHA256) {
			return ErrIntegrity
		}
		names[elf.Name] = true
	}
	if e = os.WriteFile(filepath.Join(staging, "verification.json"), reportData, 0600); e != nil {
		return errors.New("private report unavailable")
	}
	// Publish report last: Java requires both files and rechecks hash/certificate.
	if e = os.Rename(filepath.Join(staging, APKName), filepath.Join(output, APKName)); e != nil {
		return errors.New("private APK unavailable")
	}
	if e = os.Rename(filepath.Join(staging, "verification.json"), filepath.Join(output, "verification.json")); e != nil {
		os.Remove(filepath.Join(output, APKName))
		return fmt.Errorf("private report unavailable")
	}
	return nil
}
