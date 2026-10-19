#include "DiagnosticPolicy.h"
// Public, non-secret attestation for inspection of the actual linked JNI binary.
extern "C" __attribute__((visibility("default"), used))
const char *flexygram_variant_policy() {
    return "FLEXYGRAM_POLICY:" FLEXYGRAM_VARIANT_POLICY_SCOPE ":auth=0:transport=0:push=0:translation=0:plugins=0:restore=0";
}
