# Unapplied integration fragment: include AFTER the original shared target exists, after review.
if(NOT FLEXYGRAM_FLAVOR STREQUAL "realAlpha" OR NOT TARGET ${NATIVE_LIB})
    message(FATAL_ERROR "SESSION_BRIDGE_REQUIRES_REAL_ALPHA_TARGET")
endif()
target_sources(${NATIVE_LIB} PRIVATE "${CMAKE_CURRENT_LIST_DIR}/../src/main/cpp/SessionReadOnlyBridge.cpp")
target_include_directories(${NATIVE_LIB} PRIVATE "${CMAKE_CURRENT_LIST_DIR}/../../../TMessagesProj/jni/tgnet")
