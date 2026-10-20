# Offline beta development only. Protected Diagnostic/Production policy is unchanged.
if(NOT FLEXYGRAM_FLAVOR STREQUAL "betaDevelopment")
    message(FATAL_ERROR "FLEXYGRAM_BETA_PROFILE_MISMATCH")
endif()
file(SHA256 "${CMAKE_CURRENT_LIST_DIR}/../../gradle/beta-development.json" _beta_digest)
if(NOT FLEXYGRAM_POLICY_SCOPE STREQUAL "${_beta_digest}:betaDevelopment")
    message(FATAL_ERROR "FLEXYGRAM_BETA_POLICY_SCOPE_MISMATCH")
endif()
# Legacy macro means JNI isolation; all six constants in DiagnosticPolicy.h stay false.
# This is not the future authenticated native implementation.
set(FLEXYGRAM_BUILD_DIAGNOSTIC 1)
configure_file("${CMAKE_CURRENT_LIST_DIR}/tgnet/VariantPolicy.generated.h.in"
    "${CMAKE_CURRENT_BINARY_DIR}/flexygram-policy/VariantPolicy.generated.h" @ONLY)
include_directories("${CMAKE_CURRENT_BINARY_DIR}/flexygram-policy")
