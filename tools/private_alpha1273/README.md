# Alpha 1273 — private native APK handoff

Application source is frozen at `751c926d91acd536d96b427af5f34f2fe6bedbc4`.
This delivery branch adds infrastructure only; PR92 remains draft and unchanged.

The workflow checks out that exact source for host checks and compilation,
including its original JNI/Chaquopy recipes, package, version and signing inputs.
Delivery tooling is checked out separately. A harmless probe must first pass an
authenticated download/hash roundtrip and anonymous denial at both the asset API
and browser download URL. Failure prevents compilation/transfer of the APK.

The final verifier checks V2, ARM64/16KiB, package/version, 96 ELF and the authorized
certificate. The APK and verifier report are then uploaded to the **unpublished
draft** and downloaded again authenticated, comparing the actual hash and size.
Only after that step does the original runner cleanup run. No APK Actions artifact,
public release, AGE file, installer or private key is created or published.

The draft remains accessible only to repository users with write permission.
Open the resulting draft/download link while signed into the owning GitHub account.
Keep the delivery as a draft; this automation never publishes it. The report and
uploaded file remain there after runner cleanup, including if a later network
verification fails. Anonymous exposure causes removal of the affected asset.

A rebuild may have a different APK hash due to generated build metadata or archive
timestamps; the delivered bytes are independently reverified and their own hash
is reported. Physical installation/update and Poco performance remain untested.
