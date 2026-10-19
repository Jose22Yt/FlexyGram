#pragma once
#include <VariantPolicy.generated.h>
#if !defined(FLEXYGRAM_BUILD_DIAGNOSTIC) || FLEXYGRAM_BUILD_DIAGNOSTIC != 1
#error "Unreviewed native variant: production implementation is unavailable"
#endif
namespace flexygram {
inline constexpr bool isolatedDiagnostic = FLEXYGRAM_BUILD_DIAGNOSTIC == 1;
inline constexpr bool authenticationAllowed = false;
inline constexpr bool telegramTransportAllowed = false;
inline constexpr bool pushAllowed = false;
inline constexpr bool translationAllowed = false;
inline constexpr bool pluginsAllowed = false;
inline constexpr bool sessionRestoreAllowed = false;
}
